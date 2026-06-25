# =============================================================================
#  main.py  —  API FastAPI del backend ArchivaCloud P-07
# -----------------------------------------------------------------------------
#  Expone dos endpoints:
#    GET  /healthz                     -> comprobación de vida del servicio
#    POST /api/upload/presigned-url    -> genera una URL firmada para subir a S3
#
#  Patrón "presigned URL": el navegador NO sube el archivo a través de nuestro
#  backend. El backend solo FIRMA un permiso temporal y el navegador sube el
#  archivo DIRECTO a S3. Así el servidor no gasta ancho de banda ni memoria en
#  archivos grandes, y nunca toca el contenido del archivo.
# =============================================================================

import os         # utilidades de rutas (os.path.splitext) para detectar extensiones
import re         # expresiones regulares para sanear el nombre de archivo
import uuid       # genera identificadores únicos para las claves S3
import logging    # registra errores en el servidor SIN mostrarlos al cliente

import boto3                                              # SDK oficial de AWS
from botocore.exceptions import BotoCoreError, ClientError  # errores que lanza boto3/S3
from fastapi import FastAPI, HTTPException, Request       # núcleo de la API
from fastapi.middleware.cors import CORSMiddleware        # middleware para CORS (SEC-02)
from fastapi.responses import JSONResponse                # respuestas JSON manuales
from fastapi.exceptions import RequestValidationError     # error de validación de Pydantic
from pydantic import BaseModel, field_validator           # modelo y validadores de entrada

from app.config import settings   # nuestra configuración central (config.py)


# -----------------------------------------------------------------------------
#  Logger
# -----------------------------------------------------------------------------
#  Configura el sistema de logs. Los errores se escriben en la CONSOLA DEL
#  SERVIDOR (donde solo nosotros los vemos), nunca se envían al usuario final
#  (control SEC-07: errores sin información sensible).
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
#  Instancia de la aplicación
# -----------------------------------------------------------------------------
#  La documentación automática (/docs Swagger y /redoc) se habilita SOLO en
#  modo desarrollo (DEBUG=true en el .env local), para poder probar los
#  endpoints de forma visual. En producción (DEBUG ausente o false) queda
#  apagada: es superficie de ataque que dejaría explorar la API sin
#  autenticarse. (control SEC)
app = FastAPI(
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# -----------------------------------------------------------------------------
#  CORS restrictivo  (control SEC-02)
# -----------------------------------------------------------------------------
#  CORS = Cross-Origin Resource Sharing. Decide QUÉ webs (orígenes) pueden
#  llamar a nuestra API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    #  Lista con UN solo origen, leído del .env. Nunca "*".
    allow_origins=[settings.FRONTEND_ORIGIN],
    #  False = el navegador no enviará cookies ni cabeceras de autorización en
    #  las peticiones cross-origin. Mitiga ataques de tipo CSRF.
    allow_credentials=False,
    #  Solo permitimos los métodos que realmente usa el frontend (mínimo
    #  privilegio): GET (listar), POST (presigned-url), DELETE (eliminar).
    allow_methods=["GET", "POST", "DELETE"],
    #  Solo permitimos la cabecera necesaria para enviar JSON.
    allow_headers=["Content-Type"],
)


# -----------------------------------------------------------------------------
#  Manejadores de error globales  (control SEC-07)
# -----------------------------------------------------------------------------
#  Sin estos, FastAPI podría devolver al cliente el "stack trace" (traza
#  técnica) completo, revelando rutas internas, versiones de librerías y
#  lógica del servidor. Aquí interceptamos los errores y devolvemos un mensaje
#  genérico, mientras el detalle real queda en el log del servidor.

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    #  Se dispara cuando la entrada no cumple el modelo Pydantic (faltan
    #  campos, tipos incorrectos, validadores fallidos...). Devolvemos 422
    #  con un mensaje neutro, sin revelar qué campo exacto falló internamente.
    return JSONResponse(
        status_code=422,
        content={"detail": "Datos de solicitud inválidos."},
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    #  Red de seguridad para CUALQUIER error no previsto.
    #  exc_info=True guarda la traza completa EN EL LOG del servidor...
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    #  ...pero al cliente solo le llega un 500 genérico.
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
    )


# -----------------------------------------------------------------------------
#  Modelo de entrada  (control SEC-03: validación con Pydantic)
# -----------------------------------------------------------------------------
#  Define la forma EXACTA del JSON que aceptamos en POST /presigned-url.
#  Si el cliente manda algo que no encaja (falta un campo, tipo equivocado),
#  Pydantic lo rechaza ANTES de que el código del endpoint se ejecute.
class PresignedUrlRequest(BaseModel):
    fileName: str   # nombre del archivo, p.ej. "respaldo.tar.gz"
    fileType: str   # tipo MIME, p.ej. "application/zip"
    fileSize: int   # tamaño en bytes que declara el cliente

    #  field_validator = regla extra que corre sobre un campo concreto.
    @field_validator("fileName")
    @classmethod
    def file_name_not_empty(cls, v: str) -> str:
        #  v.strip() quita espacios; si queda vacío, el nombre era inválido.
        if not v or not v.strip():
            raise ValueError("fileName no puede estar vacío.")
        return v

    @field_validator("fileSize")
    @classmethod
    def file_size_positive(cls, v: int) -> int:
        #  Un tamaño de 0 o negativo no tiene sentido: lo rechazamos.
        if v <= 0:
            raise ValueError("fileSize debe ser mayor que cero.")
        return v


# -----------------------------------------------------------------------------
#  Utilidades de seguridad
# -----------------------------------------------------------------------------

#  Expresión regular que define qué caracteres NO son seguros en un nombre.
#  El "^" dentro de [...] significa "cualquier cosa que NO sea":
#  letras a-z/A-Z, dígitos 0-9, punto, guion y guion bajo.
#  Usamos ASCII explícito (y no \w) para no permitir letras Unicode (tildes,
#  kanji, emojis...) que podrían dar problemas en las claves de S3.
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9.\-_]")


def get_extension(filename: str) -> str:
    """
    Devuelve la extensión REAL del archivo.

    Problema: os.path.splitext("backup.tar.gz") devuelve ('backup.tar', '.gz'),
    o sea, solo ve la última parte (.gz). Si validáramos con eso, un .tar.gz
    legítimo NUNCA pasaría la lista blanca.

    Solución: comprobamos primero, a mano, si el nombre termina en ".tar.gz"
    (extensión doble). Solo si no, recurrimos a splitext para el caso simple
    como ".zip".  (Apoya el control SEC-03.)
    """
    lower = filename.lower()                 # normalizamos a minúsculas (.ZIP == .zip)
    if lower.endswith(".tar.gz"):            # caso especial de extensión doble
        return ".tar.gz"
    _, ext = os.path.splitext(lower)         # caso normal: separa nombre y extensión
    return ext                               # p.ej. ".zip"


def sanitize_filename(name: str) -> str:
    """
    Limpia el nombre de archivo antes de usarlo como clave en S3.
    Cada paso neutraliza un ataque distinto (control SEC-03).
    """
    #  1) Anti path-traversal: convertimos "\" en "/" y nos quedamos SOLO con
    #     lo que hay tras la última "/". Así "../../etc/passwd" -> "passwd".
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    #  2) Anti null-byte injection: quitamos el byte nulo \x00 que en algunos
    #     lenguajes corta la cadena y permite saltarse validaciones.
    name = name.replace("\x00", "")
    #  3) Sustituimos todo carácter inseguro (según la regex) por "_".
    name = _SAFE_NAME_RE.sub("_", name)
    #  4) Quitamos puntos al inicio para evitar archivos ocultos tipo ".bashrc".
    name = name.lstrip(".")
    #  5) Si tras limpiar quedó vacío, ponemos un nombre por defecto.
    return name if name else "archivo"


def build_s3_client():
    """
    Crea el cliente de boto3 para hablar con S3, usando las credenciales
    temporales del .env.

    Lo construimos EN CADA petición (no una sola vez al arrancar) porque las
    credenciales de AWS Academy cambian con cada sesión de laboratorio; así
    tomamos siempre las más recientes sin reiniciar el servidor.
    """
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,   # obligatorio en voclabs
    )


# -----------------------------------------------------------------------------
#  Endpoint: GET /healthz  —  comprobación de vida
# -----------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    """Devuelve 200 y {"status": "ok"} si el servicio está vivo.
    Lo usan balanceadores de carga y pipelines de CI/CD para saber si la app
    responde, sin tocar ninguna lógica de negocio."""
    return {"status": "ok"}


# -----------------------------------------------------------------------------
#  Endpoint: POST /api/upload/presigned-url
# -----------------------------------------------------------------------------
#  Recibe (fileName, fileType, fileSize), valida según los parámetros P-07 y,
#  si todo está bien, devuelve la URL firmada para subir el archivo a S3.
@app.post("/api/upload/presigned-url")
def generate_presigned_url(payload: PresignedUrlRequest):
    #  Nota: Pydantic YA validó que payload tiene los 3 campos, que fileName no
    #  está vacío y que fileSize > 0 antes de llegar aquí.

    # ── 1) Límite de tamaño (control SEC-04) ─────────────────────────────────
    #  Validamos PRIMERO lo barato (un simple if) antes de gastar una llamada
    #  a AWS. Si supera 50 MB, cortamos con un error 400 (petición incorrecta).
    if payload.fileSize > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el límite de 50 MB.",
        )

    # ── 2) Validación de extensión / lista blanca (control SEC-03) ───────────
    ext = get_extension(payload.fileName)            # detecta .zip o .tar.gz bien
    if ext not in settings.ALLOWED_EXTENSIONS:       # ¿está en la lista permitida?
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos .zip y .tar.gz.",
        )

    # ── 3) Sanitización del nombre y construcción de la clave S3 ─────────────
    safe_name = sanitize_filename(payload.fileName)  # nombre limpio y seguro
    #  La clave (key) es la ruta del objeto dentro del bucket. La formamos con:
    #    - el prefijo obligatorio "uploads/"
    #    - un UUID v4 aleatorio (garantiza unicidad: dos archivos con el mismo
    #      nombre no se pisan entre sí)
    #    - el nombre ya saneado
    key = f"{settings.UPLOAD_PREFIX}{uuid.uuid4()}_{safe_name}"

    # ── 4) Generación de la presigned URL ────────────────────────────────────
    s3 = build_s3_client()
    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",        # la URL servirá para SUBIR (PUT)
            Params={
                "Bucket": settings.S3_BUCKET_NAME,   # bucket destino
                "Key": key,                          # ruta/clave del objeto
                "ContentType": payload.fileType,     # tipo declarado del archivo
                #  ContentLength firma el tamaño exacto: S3 rechazará la subida
                #  si el navegador intenta subir un número de bytes distinto.
                #  Cierra el truco de "digo 5 MB pero subo 500".
                "ContentLength": payload.fileSize,
            },
            ExpiresIn=settings.PRESIGNED_URL_EXPIRY,  # caduca en 5 minutos
        )
    except (BotoCoreError, ClientError) as exc:
        #  Si AWS falla (credenciales caducadas, red, permisos...), lo
        #  registramos en el log interno y devolvemos un 502 neutro al cliente,
        #  sin filtrar el detalle técnico de AWS (control SEC-07).
        logger.error("S3 presigned URL error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="No se pudo generar la URL firmada.",
        )

    # ── 5) URL pública del objeto (dónde quedará una vez subido) ─────────────
    #  Se arma con el patrón estándar de S3: bucket + región + clave.
    public_url = (
        f"https://{settings.S3_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    )

    # ── 6) Respuesta al frontend ─────────────────────────────────────────────
    #  presignedUrl -> a dónde hace el PUT el navegador
    #  key          -> identificador del objeto (se usará luego para listar/borrar)
    #  publicUrl    -> dónde quedará accesible el archivo
    return {
        "presignedUrl": presigned_url,
        "key": key,
        "publicUrl": public_url,
    }


# -----------------------------------------------------------------------------
#  Endpoint: GET /api/files  —  listar los archivos subidos
# -----------------------------------------------------------------------------
#  Devuelve los objetos guardados bajo el prefijo uploads/ del bucket. Mira
#  SOLO esa carpeta lógica, nunca el resto del bucket: es defensa en profundidad
#  que acompaña a la política IAM de mínimo privilegio (control SEC-05).
@app.get("/api/files")
def list_files():
    s3 = build_s3_client()
    try:
        #  Prefix restringe el listado a uploads/. Sin Prefix se listaría todo
        #  el bucket, lo que violaría el mínimo privilegio.
        response = s3.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME,
            Prefix=settings.UPLOAD_PREFIX,
        )
    except (BotoCoreError, ClientError) as exc:
        #  Cualquier fallo de AWS se registra en el log y al cliente solo le
        #  llega un 502 neutro, sin detalles técnicos (control SEC-07).
        logger.error("S3 list error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="No se pudieron listar los archivos.",
        )

    #  Si no hay objetos bajo uploads/, la respuesta de S3 NO trae la clave
    #  "Contents"; por eso usamos .get("Contents", []) para no provocar un error.
    files = []
    for obj in response.get("Contents", []):
        files.append(
            {
                "key": obj["Key"],                                # ruta completa en S3
                "size": obj["Size"],                              # tamaño en bytes
                "lastModified": obj["LastModified"].isoformat(),  # fecha ISO 8601
            }
        )

    return {"count": len(files), "files": files}


# -----------------------------------------------------------------------------
#  Endpoint: DELETE /api/files/{key}  —  eliminar un archivo
# -----------------------------------------------------------------------------
#  Borra un objeto del bucket. El convertidor {key:path} captura la ruta
#  completa INCLUIDAS las barras "/", porque la clave es del tipo
#  "uploads/<uuid>_nombre.zip" (un path param normal cortaría en la primera /).
@app.delete("/api/files/{key:path}")
def delete_file(key: str):
    # ── Seguridad: solo se puede borrar DENTRO de uploads/ (SEC-05) ──────────
    #  Aunque la política IAM ya restringe el acceso a uploads/, lo validamos
    #  también aquí (defensa en profundidad). Rechazamos con 400:
    #    - claves que no empiezan por "uploads/" (intento de salir del prefijo)
    #    - claves con ".." (intento de path traversal)
    if not key.startswith(settings.UPLOAD_PREFIX) or ".." in key:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar archivos dentro de uploads/.",
        )

    s3 = build_s3_client()
    try:
        #  delete_object es idempotente: S3 responde con éxito aunque el objeto
        #  no exista. Para este proyecto es un comportamiento aceptable.
        s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 delete error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="No se pudo eliminar el archivo.",
        )

    return {"deleted": key}


# -----------------------------------------------------------------------------
#  Endpoint: GET /api/stats  —  FEATURE EXTRA P-07
# -----------------------------------------------------------------------------
#  Devuelve el tamaño TOTAL ocupado en el bucket (bajo uploads/) y el porcentaje
#  frente a la cuota de 1 GB. Es el endpoint adicional que exige la feature extra
#  obligatoria de la pareja P-07.
@app.get("/api/stats")
def bucket_stats():
    s3 = build_s3_client()
    total = 0
    count = 0
    try:
        #  list_objects_v2 devuelve como MUCHO 1000 objetos por llamada. Para
        #  sumar TODOS (aunque haya más de 1000) paginamos con el
        #  ContinuationToken hasta que la respuesta deja de estar truncada.
        token = None
        while True:
            params = {"Bucket": settings.S3_BUCKET_NAME, "Prefix": settings.UPLOAD_PREFIX}
            if token:
                params["ContinuationToken"] = token
            resp = s3.list_objects_v2(**params)
            for obj in resp.get("Contents", []):
                total += obj["Size"]
                count += 1
            if resp.get("IsTruncated"):
                token = resp.get("NextContinuationToken")
            else:
                break
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 stats error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="No se pudieron calcular las estadísticas.",
        )

    limite = settings.BUCKET_LIMIT_BYTES
    #  Porcentaje ocupado frente a 1 GB, redondeado a 2 decimales.
    porcentaje = round(total / limite * 100, 2) if limite else 0

    return {
        "count": count,            # número de archivos
        "totalBytes": total,       # bytes ocupados en total
        "limitBytes": limite,      # cuota de referencia (1 GB)
        "porcentaje": porcentaje,  # % ocupado frente a la cuota
    }
