# archivacloud-p07

Proyecto universitario de ciberseguridad. Backend FastAPI para subida de archivos a Amazon S3 mediante presigned URLs.

## Stack
- Python 3.10+
- FastAPI + Uvicorn
- boto3 (AWS SDK)
- python-dotenv
- Pydantic

## Estructura
```
archivacloud-p07/
├── backend/
│   ├── app/
│   │   ├── config.py   # Variables de entorno y parámetros P-07
│   │   └── main.py     # FastAPI: /healthz y /api/upload/presigned-url
│   └── requirements.txt
├── .env.example        # Plantilla de variables (nunca subir .env real a git)
└── .gitignore
```

## Variables de entorno requeridas
Ver `.env.example`. Crear `.env` en la raíz con:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (credenciales temporales AWS Academy)
- `AWS_REGION=us-east-1`
- `S3_BUCKET_NAME=archivacloud-p07`
- `FRONTEND_ORIGIN=http://localhost:5173` (ajustar al origen real del frontend)

## Cómo ejecutar
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Reglas del proyecto (P-07)
- Solo se permiten archivos `.zip` y `.tar.gz`
- Tamaño máximo: 50 MB
- Prefijo S3: `uploads/`
- CORS: solo el origen de `FRONTEND_ORIGIN`, nunca `"*"`
