import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Credenciales temporales AWS Academy (voclabs) ─────────────────────────
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")  # obligatorio en cuentas federeadas
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # ── Bucket S3 destino ─────────────────────────────────────────────────────
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "archivacloud-p07")

    # ── CORS: origen exacto del frontend (NUNCA "*") ──────────────────────────
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # ── Parámetros obligatorios P-07 ──────────────────────────────────────────
    ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".zip", ".tar.gz"})
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024   # 50 MiB exactos
    UPLOAD_PREFIX: str = "uploads/"

    # Vida de la presigned URL — 5 min es el mínimo razonable para una subida
    PRESIGNED_URL_EXPIRY: int = 300


settings = Settings()

# Validación de arranque: si falta alguna credencial crítica, el proceso muere
# aquí con un mensaje claro en lugar de fallar en la primera petición real.
_REQUIRED_VARS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "S3_BUCKET_NAME",
)
_missing = [v for v in _REQUIRED_VARS if not getattr(settings, v)]
if _missing:
    raise EnvironmentError(
        f"Variables de entorno requeridas no configuradas: {', '.join(_missing)}"
    )
