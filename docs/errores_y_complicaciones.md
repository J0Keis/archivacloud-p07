# Registro de errores y complicaciones — ArchivaCloud P-07

Bitácora técnica de los problemas encontrados durante el desarrollo, con su
causa y solución. Útil para la defensa oral y como evidencia de trabajo.

---

## Sprint 1 — Setup y backend

### 1. `No module named pip`
- **Síntoma:** al instalar dependencias, Python respondía `No module named pip`.
- **Causa:** la instalación de Python 3.14 venía sin `pip` activado.
- **Solución:** reconstruir pip con el módulo incorporado de Python:
  ```powershell
  python -m ensurepip --upgrade
  ```
- **Lección:** preparar el entorno (pip + dependencias) antes de ejecutar.

### 2. `ModuleNotFoundError: No module named 'dotenv'`
- **Síntoma:** el backend no arrancaba; faltaba la librería `python-dotenv`.
- **Causa:** las dependencias de `requirements.txt` no estaban instaladas aún.
- **Solución:**
  ```powershell
  python -m pip install -r requirements.txt
  ```

### 3. `Variables de entorno requeridas no configuradas` ⭐
- **Síntoma:** al ejecutar `uvicorn` desde `backend/`, la app moría con
  `EnvironmentError: Variables de entorno requeridas no configuradas:
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN`.
- **Causa:** las credenciales SÍ estaban en el `.env`, pero `load_dotenv()` sin
  ruta busca el `.env` en la carpeta desde donde se lanza el comando
  (`backend/`), no en la raíz del proyecto, donde estaba el archivo.
- **Solución:** dar a `load_dotenv()` la ruta absoluta al `.env`, subiendo dos
  niveles desde `config.py`:
  ```python
  from pathlib import Path
  load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
  ```
- **Nota positiva:** la validación *fail-fast* del `config.py` hizo que el error
  fuera claro e inmediato, en lugar de un fallo críptico de AWS más adelante.

### 4. Credenciales reales subidas a Git ⭐ (incidente de seguridad)
- **Síntoma:** el `.env` con las credenciales AWS reales quedó commiteado y
  subido a GitHub.
- **Causa:** se eliminó el `.gitignore`, así que el siguiente `git add` incluyó
  el `.env` y el `push` lo envió al repositorio.
- **Solución (3 pasos):**
  1. Restaurar el `.gitignore` con `.env` dentro.
  2. Purgar el `.env` de **todo** el historial:
     ```bash
     git filter-branch --force --index-filter \
       'git rm --cached --ignore-unmatch .env backend/.env' \
       --prune-empty -- --all
     git push origin main --force
     ```
  3. **Rotar las credenciales** (End Lab → Start Lab en AWS Academy), porque
     limpiar el repo NO invalida una credencial ya expuesta.
- **Control:** SEC-01 (secretos fuera del repositorio).

### 5. `[Errno 10048]` — puerto en uso
- **Síntoma:** `error while attempting to bind on address ('127.0.0.1', 8000)`.
- **Causa:** ya había un servidor uvicorn corriendo en el puerto 8000.
- **Solución:** usar otro puerto (`--port 8001`) o cerrar el servidor anterior.

---

## Sprint 2 — Pruebas y frontend

### 6. `curl` daba 422 en todos los casos ⭐
- **Síntoma:** al probar el endpoint con `curl.exe` y comillas simples, TODAS
  las peticiones devolvían `422 Datos de solicitud inválidos`, incluso las
  válidas.
- **Causa:** Windows PowerShell 5.1 tiene un defecto al pasar comillas dobles a
  programas externos (`curl.exe`): las elimina. El servidor recibía un JSON sin
  comillas, que no podía parsear.
- **Solución:** usar `Invoke-RestMethod` (comando nativo de PowerShell, sin ese
  problema) o Swagger. NO es un fallo del backend.
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/files" -Method Get
  ```

### 7. `/docs` devolvía `{"detail":"Not Found"}`
- **Síntoma:** abrir `http://localhost:8000/docs` daba *Not Found*.
- **Causa:** Swagger se deshabilitó a propósito (`docs_url=None`) como control
  de seguridad (no exponer la API en producción). NO era un error.
- **Solución:** activarlo SOLO en desarrollo con una variable `DEBUG`:
  ```python
  app = FastAPI(
      docs_url="/docs" if settings.DEBUG else None,
      redoc_url="/redoc" if settings.DEBUG else None,
  )
  ```
  Con `DEBUG=true` en el `.env` local, Swagger queda disponible; en producción,
  apagado.

### 8. `InvalidToken` — credenciales caducadas ⭐
- **Síntoma:** la subida real a S3 fallaba con `HTTP 400`; al investigar,
  `InvalidToken: The provided token is malformed or otherwise invalid`.
- **Causa:** las credenciales temporales de AWS Academy caducan tras unas horas;
  el `AWS_SESSION_TOKEN` había expirado.
- **Solución:** reiniciar el Lab (End Lab → Start Lab) y pegar las 3
  credenciales nuevas en `backend\.env`.
- **Detalle:** el `POST /presigned-url` seguía dando 200 porque la firma se hace
  localmente; solo el `PUT` real a S3 reveló el token inválido.

### 9. `DELETE` daba "Network Error" en el navegador ⭐
- **Síntoma:** subir y listar funcionaban en el frontend, pero al **eliminar**
  salía `Error al eliminar: Network Error`.
- **Causa:** el CORS del backend solo permitía `GET` y `POST`. Cuando se añadió
  el endpoint `DELETE` en Sprint 2, se olvidó actualizar `allow_methods`. El
  navegador bloqueaba el preflight del DELETE.
- **Solución:** añadir `DELETE` a los métodos permitidos:
  ```python
  allow_methods=["GET", "POST", "DELETE"],
  ```
- **Lección clave:** CORS **solo existe en el navegador**. Por eso el DELETE
  funcionaba en Swagger/PowerShell (no aplican CORS) pero fallaba en el frontend.
  El CORS debe listar todos los métodos que el frontend usa (control SEC-02).

### 10. La subida desde el navegador necesitaba CORS en el bucket
- **Síntoma:** el `PUT` directo del navegador a S3 fallaría por CORS.
- **Causa:** el navegador sube el archivo directo a S3 (otro dominio); S3 debe
  autorizar explícitamente el origen del frontend.
- **Solución:** configurar CORS en el bucket S3 (consola AWS → bucket →
  Permissions → CORS):
  ```json
  [
    {
      "AllowedOrigins": ["http://localhost:5173"],
      "AllowedMethods": ["PUT", "GET"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
  ```
- **Detalle para la defensa:** CORS del bucket NO abre el bucket al público
  (SEC-06 sigue: Block Public Access activo). Solo dice qué origen de navegador
  puede intentar la petición; la autorización real la da la presigned URL firmada.

---

## Resumen

| # | Problema | Causa raíz | Solución |
|---|---|---|---|
| 1 | `No module named pip` | Python 3.14 sin pip | `ensurepip` |
| 2 | `No module named 'dotenv'` | dependencias sin instalar | `pip install -r requirements.txt` |
| 3 | Variables no configuradas | `.env` buscado en carpeta equivocada | ruta absoluta `Path(__file__)...parents[2]` |
| 4 | Credenciales en Git | `.gitignore` eliminado | purgar historial + restaurar `.gitignore` + rotar |
| 5 | Puerto en uso (10048) | dos servidores en 8000 | usar otro puerto |
| 6 | `curl` daba 422 | PowerShell 5.1 rompe el JSON | usar Invoke-RestMethod / Swagger |
| 7 | `/docs` Not Found | Swagger deshabilitado por seguridad | activar con `DEBUG=true` |
| 8 | `InvalidToken` | credenciales AWS caducadas | reiniciar Lab + actualizar `.env` |
| 9 | DELETE "Network Error" | CORS backend sin DELETE | añadir `DELETE` a `allow_methods` |
| 10 | Subida bloqueada | faltaba CORS en el bucket | configurar CORS del bucket S3 |
