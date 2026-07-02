# ArchivaCloud P-07

Portal web para **subir, listar y eliminar archivos** en Amazon S3 mediante el
patrón de **presigned URLs** (el archivo viaja directo del navegador a S3, sin
pasar por el backend). Incluye una **feature extra** (uso del bucket) y una
**evaluación de continuación** que conecta el proyecto a **DynamoDB**.
Proyecto universitario de ciberseguridad — pareja P-07.

## Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, boto3, python-dotenv, Pydantic
- **Frontend:** React 18, Vite, axios
- **Nube:** Amazon S3 (archivos) + DynamoDB (continuación), cuenta AWS Academy

## Arquitectura

```
Navegador (React)  ──(1) pide URL firmada──>  Backend (FastAPI)
       │                                            │
       │                                            └──(firma con boto3)
       └──(2) PUT del archivo DIRECTO a S3──>  Amazon S3 (bucket archivacloud-p07)
```

El backend nunca recibe el archivo: solo **firma** un permiso temporal (5 min).

## Estructura

```
archivacloud-p07/
├── backend/
│   ├── app/
│   │   ├── config.py        # variables de entorno y parámetros P-07
│   │   └── main.py          # FastAPI: presigned-url, files (GET/DELETE), stats, healthz
│   ├── requirements.txt
│   └── venv/                # entorno virtual (no se versiona)
├── frontend/
│   └── src/
│       ├── api.js           # capa de comunicación con el backend (axios)
│       ├── App.jsx          # componente raíz
│       └── components/      # UploadForm, FileList, BucketStats, Modal
├── dynamodb/                # evaluación de continuación
│   ├── main.py              # sube datos a la tabla database_dynamo
│   └── gestionar.py         # CRUD por línea de comandos
├── docs/                    # documentación (ver sección Documentación)
├── iniciar.ps1              # arranca backend + frontend + DynamoDB
├── .env.example             # plantilla de variables (NUNCA subir el .env real)
└── README.md
```

## Parámetros únicos P-07 (Anexo B)

| Parámetro | Valor |
|---|---|
| Extensiones permitidas | solo `.zip` y `.tar.gz` |
| Tamaño máximo | 50 MB |
| Bucket S3 | `archivacloud-p07` |
| Prefijo de subida | `uploads/` |
| Feature extra | tamaño total del bucket + % frente a 1 GB |

> **Región:** el Anexo B pedía `us-west-1`, pero AWS Academy solo permite
> `us-east-1`, que es la que usa el proyecto.

---

## Requisitos previos

- **Python 3.10+** y **Node.js 18+**
- Cuenta AWS Academy con el bucket `archivacloud-p07` y la tabla DynamoDB
  `database_dynamo` creados, y credenciales temporales

## Instalación

**Backend** (una sola vez):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Frontend** (una sola vez):
```powershell
cd frontend
npm install
```

## Configuración

Copia `.env.example` como `backend\.env` (o en la raíz) y rellena las
credenciales reales de AWS Academy:

```
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=archivacloud-p07
FRONTEND_ORIGIN=http://localhost:5173
DEBUG=true            # activa Swagger en /docs (solo desarrollo local)
```

> ⚠️ El `.env` **nunca** se sube a Git (está en `.gitignore`). Solo se versiona
> `.env.example` con placeholders (control SEC-01).

---

## Cómo ejecutar

**Atajo:** desde la raíz, `.\iniciar.ps1` abre backend (8000), frontend (5173)
y ejecuta el script de DynamoDB, cada uno en su ventana. Luego abre
**http://localhost:5173**.

**Manual** (dos terminales):
```powershell
# Terminal 1 — Backend (8000)
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend (5173)
cd frontend
npm run dev
```

## Endpoints del backend

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/healthz` | Health-check |
| POST | `/api/upload/presigned-url` | Genera URL firmada (valida extensión y tamaño) |
| GET | `/api/files` | Lista los objetos bajo `uploads/` |
| DELETE | `/api/files/{key}` | Elimina un objeto por su key |
| GET | `/api/stats` | **Feature extra:** tamaño total del bucket + % de 1 GB |

Documentación interactiva (Swagger) en `/docs` cuando `DEBUG=true`.

## Feature extra P-07 — uso del bucket

`GET /api/stats` recorre los objetos de `uploads/` (con paginación de S3), suma
sus tamaños y calcula el porcentaje frente a una cuota de 1 GiB. El frontend lo
muestra como una barra de progreso. Detalle en `docs/feature-extra.md`.

## DynamoDB (evaluación de continuación)

La tabla `database_dynamo` usa **clave compuesta**: `id_tabla` (partition key) +
`nombre_proyecto` (sort key). Las credenciales se leen del `.env` (no
hardcodeadas — SEC-01).

```powershell
# Subir datos de ejemplo
.\backend\venv\Scripts\python.exe dynamodb\main.py

# CRUD (agregar / editar / borrar / listar)
.\backend\venv\Scripts\python.exe dynamodb\gestionar.py listar
.\backend\venv\Scripts\python.exe dynamodb\gestionar.py agregar 3 "Proyecto" "Descripcion"
.\backend\venv\Scripts\python.exe dynamodb\gestionar.py editar 3 "Proyecto" "Nueva desc"
.\backend\venv\Scripts\python.exe dynamodb\gestionar.py borrar 3 "Proyecto"
```

## Seguridad (SEC-01 a SEC-10)

Los 10 controles están verificados y explicados en `docs/reporte_seguridad.md`.
Resumen:

- **SEC-01** secretos fuera del repo · **SEC-02** CORS restrictivo (nunca `*`) ·
  **SEC-03** validación Pydantic + sanitización + lista blanca · **SEC-04** límite
  de tamaño (cliente y servidor) · **SEC-05** IAM mínimo privilegio
  (`docs/politica-iam-s3.json`) · **SEC-06** Block Public Access · **SEC-07**
  errores sin stack traces · **SEC-08** cifrado en reposo (AES256) · **SEC-09**
  escaneo de dependencias (`pip-audit` / `npm audit`, 0 vulnerabilidades) ·
  **SEC-10** TLS de extremo a extremo.

## Documentación (`docs/`)

| Archivo | Contenido |
|---|---|
| `reporte_seguridad.md` | los 10 controles SEC explicados |
| `feature-extra.md` | qué hace la feature extra y por qué ese diseño |
| `politica-iam-s3.json` | política IAM de mínimo privilegio (SEC-05) |
| `errores_y_complicaciones.md` | registro de errores del desarrollo y su solución |
| `pruebas_sprint1.txt` | guía de pruebas manuales de los endpoints |
| `bitacora.md` | bitácora de las sesiones de trabajo |
| `uso-ia.md` | declaración de uso de IA por sprint (Anexo A) |

## Notas sobre AWS Academy

Las credenciales son **temporales** y caducan al cerrar el laboratorio. Si algo
falla con `502` / `InvalidToken`:
1. En AWS Academy: **End Lab → Start Lab**.
2. Pega las 3 credenciales nuevas en `backend\.env`.
