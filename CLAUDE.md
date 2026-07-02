# archivacloud-p07

Proyecto universitario de ciberseguridad (pareja P-07). Portal web para
**subir, listar y eliminar archivos** en Amazon S3 mediante **presigned URLs**,
con una **feature extra** (uso del bucket) y una **evaluación de continuación**
que conecta el proyecto a **DynamoDB**.

## Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn, boto3, python-dotenv, Pydantic
- **Frontend:** React 18, Vite, axios
- **Nube:** Amazon S3 (archivos) + DynamoDB (continuación), cuenta AWS Academy

## Estructura
```
archivacloud-p07/
├── backend/
│   ├── app/
│   │   ├── config.py    # parámetros P-07 + lectura del .env
│   │   └── main.py      # FastAPI: healthz, presigned-url, files (GET/DELETE), stats
│   └── requirements.txt
├── frontend/            # React + Vite (subir, listar, borrar, barra de uso)
│   └── src/
│       ├── api.js
│       ├── App.jsx
│       └── components/  # UploadForm, FileList, BucketStats, Modal
├── dynamodb/            # evaluación de continuación
│   ├── main.py          # sube datos a la tabla database_dynamo
│   └── gestionar.py     # CRUD por línea de comandos
├── docs/                # política IAM, reporte de seguridad, bitácora, uso de IA, etc.
├── iniciar.ps1          # arranca backend + frontend + DynamoDB
├── .env.example         # plantilla (NUNCA subir el .env real)
└── README.md
```

## Cómo ejecutar
```powershell
.\iniciar.ps1     # abre backend (8000), frontend (5173) y ejecuta DynamoDB
```
Luego abrir http://localhost:5173. Instalación y detalle en `README.md`.

## Endpoints del backend
- `GET /healthz` — health-check
- `POST /api/upload/presigned-url` — URL firmada (valida extensión y tamaño)
- `GET /api/files` — lista objetos de `uploads/`
- `DELETE /api/files/{key}` — elimina un objeto (clave con `{key:path}`)
- `GET /api/stats` — **feature extra P-07**: tamaño total del bucket + % de 1 GiB

## Reglas del proyecto (P-07)
- Solo `.zip` y `.tar.gz` (la doble extensión `.tar.gz` se trata bien, no con splitext ingenuo)
- Tamaño máximo: 50 MB
- Prefijo S3: `uploads/`
- Región: `us-east-1` (AWS Academy solo permite esta; el Anexo B pedía us-west-1)
- CORS: solo el origen de `FRONTEND_ORIGIN`, nunca `"*"`

## Seguridad (SEC-01 a SEC-10)
Todos verificados/documentados en `docs/reporte_seguridad.md`. Resumen:
SEC-01 secretos fuera del repo · SEC-02 CORS restrictivo · SEC-03 validación +
sanitización · SEC-04 límite de tamaño · SEC-05 IAM mínimo privilegio ·
SEC-06 Block Public Access · SEC-07 errores sin trazas · SEC-08 cifrado AES256 ·
SEC-09 escaneo de dependencias (pip-audit / npm audit) · SEC-10 TLS.

## DynamoDB (evaluación de continuación)
Tabla `database_dynamo` con **clave compuesta**: `id_tabla` (partition) +
`nombre_proyecto` (sort). Las credenciales se leen del `.env` (no hardcodeadas).
- `python dynamodb/main.py` — sube datos de ejemplo.
- `python dynamodb/gestionar.py agregar|editar|borrar|listar ...` — CRUD.

## Convenciones
- Commits: mensajes claros en español, sin atribución de IA (autor J0keis).
  El uso de IA se declara en `docs/uso-ia.md`.
- Credenciales AWS Academy temporales: si algo da `502`/`InvalidToken`, reiniciar
  el Lab y actualizar el `.env`.
