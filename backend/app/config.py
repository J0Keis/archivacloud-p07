# =============================================================================
#  config.py  —  Configuración central del backend ArchivaCloud P-07
# -----------------------------------------------------------------------------
#  Este módulo tiene UNA sola responsabilidad: leer las variables del archivo
#  .env y exponerlas como un objeto "settings" que el resto de la aplicación
#  importa. Centralizar la configuración aquí evita tener credenciales o
#  números mágicos repartidos por el código (buena práctica + control SEC-01).
# =============================================================================

import os                          # acceso a las variables de entorno (os.getenv)
from pathlib import Path           # para construir la ruta al .env de forma portable
from dotenv import load_dotenv     # python-dotenv: carga el .env dentro de os.environ


# -----------------------------------------------------------------------------
#  Carga del archivo .env
# -----------------------------------------------------------------------------
#  __file__               = ruta de este archivo (backend/app/config.py)
#  .resolve()             = la convierte en ruta absoluta y resuelve symlinks
#  .parents[2]            = sube 2 niveles:  app/  ->  backend/  ->  raíz/
#  / ".env"               = apunta al .env que está en la raíz del proyecto
#
#  ¿Por qué la ruta explícita? Porque load_dotenv() a secas busca el .env en el
#  directorio DESDE donde se ejecuta el comando. Si arrancamos uvicorn desde
#  backend/, no encontraría el .env de la raíz y todas las credenciales
#  quedarían vacías. Fijar la ruta hace que funcione sin importar desde dónde
#  se lance el servidor.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


# -----------------------------------------------------------------------------
#  Clase Settings  —  contenedor de toda la configuración
# -----------------------------------------------------------------------------
#  Usamos una clase simple (no pydantic-settings) porque el stack obligatorio
#  no incluye esa librería. Cada atributo se evalúa UNA vez al importar el
#  módulo, así que actúa como configuración inmutable y compartida.
class Settings:

    # ── Credenciales temporales de AWS Academy (voclabs) ──────────────────────
    #  os.getenv("CLAVE", "")  ->  lee la variable; si no existe, devuelve "".
    #  Estas tres credenciales son STS temporales: caducan al cerrar el lab.
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    #  AWS_SESSION_TOKEN es OBLIGATORIO en cuentas federadas/temporales como
    #  AWS Academy. Sin él, boto3 rechaza la petición con InvalidClientTokenId.
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")
    #  Región AWS. El Anexo B pide us-west-1, pero la cuenta de alumno solo
    #  permite us-east-1; por eso ese es el valor por defecto.
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # ── Bucket S3 de destino ──────────────────────────────────────────────────
    #  Nombre exacto exigido por el Anexo B para la pareja P-07.
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "archivacloud-p07")

    # ── Origen del frontend para CORS (control SEC-02) ────────────────────────
    #  Se lee del .env. El valor por defecto es localhost (entorno de
    #  desarrollo). NUNCA debe ser "*": eso permitiría que cualquier web del
    #  mundo llame a nuestra API. Aquí solo autorizamos el dominio del frontend.
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # ── Modo desarrollo ───────────────────────────────────────────────────────
    #  DEBUG=true en el .env LOCAL activa la documentación Swagger (/docs).
    #  En producción se deja sin definir o en "false" para no exponer la API.
    #  Convierte el texto del .env a booleano: solo "true" (sin importar
    #  mayúsculas/minúsculas) cuenta como verdadero.
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Parámetros OBLIGATORIOS de la pareja P-07 (Anexo B) ───────────────────
    #  Lista blanca de extensiones permitidas (control SEC-03).
    #  frozenset = conjunto inmutable: nadie puede añadir extensiones en caliente
    #  y la búsqueda "x in conjunto" es O(1) (más rápida que una lista).
    ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".zip", ".tar.gz"})

    #  Tamaño máximo: 50 MB (control SEC-04).
    #  50 * 1024 * 1024 = 52.428.800 bytes. Lo escribimos como multiplicación
    #  para que se lea claro que son 50 MiB exactos y no un número mágico.
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024

    #  Prefijo (carpeta lógica) bajo el cual se guardan todas las subidas en S3.
    UPLOAD_PREFIX: str = "uploads/"

    # ── Feature extra P-07: cuota total del bucket ────────────────────────────
    #  Límite de referencia de 1 GB para calcular el porcentaje ocupado.
    #  1024**3 = 1.073.741.824 bytes (1 GiB), coherente con cómo medimos los MiB.
    BUCKET_LIMIT_BYTES: int = 1024 ** 3

    # ── Tiempo de vida de la presigned URL, en segundos ───────────────────────
    #  300 s = 5 minutos. La URL firmada solo es válida durante esta ventana;
    #  después caduca. Cuanto más corta, menos tiempo tiene un atacante para
    #  reutilizarla si la intercepta (principio de exposición mínima).
    PRESIGNED_URL_EXPIRY: int = 300


#  Instancia única que el resto del código importa con:  from app.config import settings
settings = Settings()


# -----------------------------------------------------------------------------
#  Validación de arranque ("fail-fast")
# -----------------------------------------------------------------------------
#  Comprobamos que las variables críticas existan AL INICIAR. Si falta alguna,
#  la aplicación muere aquí mismo con un mensaje claro, en lugar de arrancar
#  y reventar con un error críptico de AWS en la primera petición real.
#  Principio de diseño: fallar pronto y de forma evidente.
_REQUIRED_VARS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "S3_BUCKET_NAME",
)
#  getattr(settings, v) lee dinámicamente el atributo cuyo nombre está en "v".
#  "not valor" es True si la cadena está vacía -> esa variable falta.
_missing = [v for v in _REQUIRED_VARS if not getattr(settings, v)]
if _missing:
    #  ", ".join(...) arma la lista de nombres separados por comas para el mensaje.
    raise EnvironmentError(
        f"Variables de entorno requeridas no configuradas: {', '.join(_missing)}"
    )
