import os
import re
import uuid
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Swagger y ReDoc deshabilitados: no exponer la superficie de la API en producción
app = FastAPI(docs_url=None, redoc_url=None)

# ── CORS restrictivo ──────────────────────────────────────────────────────────
# allow_origins recibe una lista con el origen exacto leído del .env.
# allow_credentials=False evita que cookies o cabeceras de autorización del
# navegador se envíen junto a las peticiones cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ── Manejadores de error globales ─────────────────────────────────────────────
# Capturan excepciones antes de que FastAPI las serialice con el stack trace
# completo. Devuelven solo un mensaje genérico al cliente; el detalle queda
# en el log del servidor (donde el usuario final no puede verlo).

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Datos de solicitud inválidos."},
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
    )


# ── Modelo de entrada ─────────────────────────────────────────────────────────
class PresignedUrlRequest(BaseModel):
    fileName: str
    fileType: str
    fileSize: int

    @field_validator("fileName")
    @classmethod
    def file_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("fileName no puede estar vacío.")
        return v

    @field_validator("fileSize")
    @classmethod
    def file_size_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("fileSize debe ser mayor que cero.")
        return v


# ── Utilidades de seguridad ───────────────────────────────────────────────────

# Regex explícito en ASCII: solo letras a-z/A-Z, dígitos, punto, guión, guión
# bajo. Se evita \w para no permitir caracteres Unicode que podrían causar
# problemas en nombres de claves S3 o en sistemas de archivos.
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9.\-_]")


def get_extension(filename: str) -> str:
    """
    Devuelve la extensión real del archivo.

    .tar.gz es una extensión compuesta. os.path.splitext lo partiría en
    ('.tar', '.gz') y devolvería solo '.gz', fallando la validación.
    Por eso se comprueba primero con endswith antes de recurrir a splitext.
    """
    lower = filename.lower()
    if lower.endswith(".tar.gz"):
        return ".tar.gz"
    _, ext = os.path.splitext(lower)
    return ext


def sanitize_filename(name: str) -> str:
    """
    Neutraliza nombres de archivo maliciosos antes de usarlos como clave S3.

    Controles aplicados:
    1. Normaliza separadores y extrae solo el componente final (anti path-traversal).
    2. Elimina bytes nulos (evita truncamiento de cadenas en C-extensions).
    3. Sustituye caracteres fuera del conjunto seguro por '_'.
    4. Elimina puntos iniciales (evita archivos ocultos en sistemas Unix).
    """
    name = name.replace("\\", "/").rsplit("/", 1)[-1]   # solo el nombre base
    name = name.replace("\x00", "")                     # bytes nulos
    name = _SAFE_NAME_RE.sub("_", name)                 # solo ASCII seguro
    name = name.lstrip(".")                             # sin punto inicial
    return name if name else "archivo"


def build_s3_client():
    """
    Construye el cliente S3 con las credenciales temporales del .env.

    Se instancia en cada petición para que rotaciones de credenciales AWS
    Academy (que cambian con cada sesión de laboratorio) surtan efecto sin
    reiniciar el servidor.
    """
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/healthz")
def healthz():
    """Comprobación de vida. Usada por balanceadores y CI/CD."""
    return {"status": "ok"}


@app.post("/api/upload/presigned-url")
def generate_presigned_url(payload: PresignedUrlRequest):
    # ── 1. Límite de tamaño ──────────────────────────────────────────────────
    # Validación temprana antes de cualquier llamada a AWS para no desperdiciar
    # cuota de API ni generar URLs para archivos que serán rechazados.
    if payload.fileSize > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el límite de 50 MB.",
        )

    # ── 2. Validación de extensión ───────────────────────────────────────────
    ext = get_extension(payload.fileName)
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos .zip y .tar.gz.",
        )

    # ── 3. Sanitización y composición de la clave S3 ─────────────────────────
    safe_name = sanitize_filename(payload.fileName)
    # UUID v4 garantiza unicidad y evita colisiones entre subidas del mismo
    # nombre; el prefijo "uploads/" segmenta el bucket por función.
    key = f"{settings.UPLOAD_PREFIX}{uuid.uuid4()}_{safe_name}"

    # ── 4. Generación de presigned URL ───────────────────────────────────────
    s3 = build_s3_client()
    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": key,
                "ContentType": payload.fileType,
                "ContentLength": payload.fileSize,  # cliente DEBE subir exactamente este tamaño
            },
            ExpiresIn=settings.PRESIGNED_URL_EXPIRY,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 presigned URL error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="No se pudo generar la URL firmada.",
        )

    public_url = (
        f"https://{settings.S3_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    )

    return {
        "presignedUrl": presigned_url,
        "key": key,
        "publicUrl": public_url,
    }
