# ArchivaCloud P-07

Portal web para **subir, listar y eliminar archivos** en Amazon S3 mediante el
patrón de **presigned URLs** (el archivo viaja directo del navegador a S3, sin
pasar por el backend). Proyecto universitario de ciberseguridad — pareja P-07.

## Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, boto3, python-dotenv, Pydantic
- **Frontend:** React + Vite + axios
- **Nube:** Amazon S3 (cuenta AWS Academy / voclabs)

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
│   │   └── main.py          # FastAPI: presigned-url, files (GET/DELETE), healthz
│   ├── requirements.txt
│   └── venv/                # entorno virtual (no se versiona)
├── frontend/
│   └── src/
│       ├── api.js           # capa de comunicación con el backend (axios)
│       ├── App.jsx          # componente raíz
│       └── components/      # UploadForm, FileList, Modal
├── docs/
│   ├── politica-iam-s3.json # política IAM de mínimo privilegio (SEC-05)
│   └── pruebas_sprint1.txt  # guía de pruebas manuales
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

---

## Requisitos previos

- **Python 3.10+** y **Node.js 18+**
- Cuenta AWS Academy con bucket `archivacloud-p07` creado y credenciales temporales

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

Se necesitan **dos terminales** (una por servidor).

**Terminal 1 — Backend** (puerto 8000):
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend** (puerto 5173):
```powershell
cd frontend
npm run dev
```

Luego abre **http://localhost:5173** en el navegador.

> Atajo: ejecutar `.\iniciar.ps1` desde la raíz abre ambos servidores en
> ventanas separadas.

## Endpoints del backend

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/healthz` | Health-check |
| POST | `/api/upload/presigned-url` | Genera URL firmada (valida extensión y tamaño) |
| GET | `/api/files` | Lista los objetos bajo `uploads/` |
| DELETE | `/api/files/{key}` | Elimina un objeto por su key |

Documentación interactiva (Swagger) en `/docs` cuando `DEBUG=true`.

## Seguridad

- **CORS backend:** `allow_origins` = solo el origen del frontend (nunca `*`);
  métodos `GET, POST, DELETE`.
- **CORS del bucket S3:** solo `http://localhost:5173`, métodos `PUT, GET`.
- **IAM mínimo privilegio:** ver `docs/politica-iam-s3.json` (4 acciones sobre
  el bucket específico, sin comodines).
- **Validación:** Pydantic + sanitización de `fileName` + lista blanca de
  extensiones + límite de tamaño (cliente y servidor).
- **Errores:** sin stack traces al cliente; detalle solo en logs del servidor.

## Notas sobre AWS Academy

Las credenciales son **temporales** y caducan al cerrar el laboratorio. Si la
subida o el listado fallan con `502` / `InvalidToken`:
1. En AWS Academy: **End Lab → Start Lab**.
2. Pega las 3 credenciales nuevas en `backend\.env`.
