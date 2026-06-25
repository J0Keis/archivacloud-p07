# Reporte de seguridad — ArchivaCloud P-07

Explicación de cada control de seguridad (SEC-01 a SEC-10), cómo se implementó
y la evidencia de su verificación.

## Resumen

| Control | Estado | Evidencia |
|---|---|---|
| SEC-01 Secretos fuera del repo | ✅ | `.env` en `.gitignore`; historial purgado |
| SEC-02 CORS restrictivo | ✅ | `allow_origins` = solo el frontend |
| SEC-03 Validación de entrada | ✅ | Pydantic + sanitización + lista blanca |
| SEC-04 Límite de tamaño | ✅ | 50 MB en cliente y servidor |
| SEC-05 IAM mínimo privilegio | ✅ | política con 4 acciones, sin comodines |
| SEC-06 Block Public Access | ✅ | verificado: TODO ACTIVO |
| SEC-07 Errores sin info sensible | ✅ | sin stack traces al cliente |
| SEC-08 Encriptación en reposo | ✅ | verificado: SSE-S3 (AES256) |
| SEC-09 Escaneo de dependencias | ✅ | pip-audit y npm audit: 0 vulnerabilidades |
| SEC-10 TLS de extremo a extremo | ✅ | HTTPS a S3; TLS en producción documentado |

---

## SEC-01 — Secretos fuera del repositorio
Las credenciales de AWS viven solo en `backend/.env`, que está en `.gitignore`.
El repositorio versiona únicamente `.env.example` con valores de ejemplo
(placeholders). Durante el desarrollo, el `.env` real se llegó a commitear por
error; se **purgó del historial completo** con `git filter-branch` y se rotaron
las credenciales (ver `docs/errores_y_complicaciones.md`).
**Evidencia:** `git log --all -p -S "ASIA..."` no devuelve resultados.

## SEC-02 — CORS restrictivo
- **Backend** (`main.py`): `allow_origins=[settings.FRONTEND_ORIGIN]` (nunca
  `"*"`), `allow_methods=["GET","POST","DELETE"]` (solo los usados),
  `allow_credentials=False`.
- **Bucket S3:** regla CORS que permite solo `PUT, GET` desde
  `http://localhost:5173`.
**Evidencia:** preflight `OPTIONS` devuelve `Access-Control-Allow-Methods: GET, POST, DELETE`.

## SEC-03 — Validación de entrada
- **Pydantic** valida la forma del JSON (`PresignedUrlRequest`) y rechaza con
  422 lo malformado.
- **Lista blanca** de extensiones (`.zip`, `.tar.gz`) con manejo correcto de la
  doble extensión (`get_extension`).
- **Sanitización** del `fileName` (`sanitize_filename`): anti path-traversal,
  anti null-byte, solo caracteres ASCII seguros.
- Validación replicada en el frontend (mejora UX; el backend siempre revalida).
**Evidencia:** `../../../etc/passwd.zip` se guarda como `uploads/<uuid>_passwd.zip`.

## SEC-04 — Límite de tamaño
`MAX_FILE_SIZE_BYTES = 50 MB`. Se valida en el **servidor** (antes de firmar la
URL) y en el **cliente** (antes de subir). Además, la presigned URL firma el
`ContentLength`, así que S3 rechaza un PUT de tamaño distinto al declarado.
**Evidencia:** un archivo de 60 MB devuelve 400.

## SEC-05 — IAM de mínimo privilegio
Política documentada en `docs/politica-iam-s3.json`: exactamente **4 acciones**
(`s3:ListBucket`, `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`),
restringidas al bucket `archivacloud-p07` y al prefijo `uploads/`, **sin
comodines** de recurso. (En AWS Academy se documenta; el laboratorio usa el rol
preasignado.)

## SEC-06 — S3 cerrado al público
**Block Public Access** activado en el bucket (las 4 opciones). No hay bucket
policy permisiva. El acceso a los objetos es solo mediante presigned URLs
firmadas y temporales.
**Evidencia:** `get_public_access_block` devuelve todas las opciones en `True`.

## SEC-07 — Errores sin información sensible
Manejadores globales (`@app.exception_handler`) devuelven mensajes genéricos
(422/500) sin stack traces. Los errores de AWS se capturan y devuelven un 502
neutro; el detalle técnico queda solo en los **logs del servidor**.
**Evidencia:** un fallo de S3 responde `{"detail":"No se pudo..."}` sin trazas.

## SEC-08 — Encriptación en reposo
El bucket tiene **SSE-S3 (AES256)** activado por defecto: todos los objetos se
cifran al guardarse.
**Evidencia:** `get_bucket_encryption` devuelve `SSEAlgorithm: AES256`; el
`head_object` de un archivo subido muestra `ServerSideEncryption: AES256`.

## SEC-09 — Escaneo de dependencias
- **Backend:** `pip-audit -r requirements.txt`. Detectó 2 CVEs en
  `starlette==1.2.1` (CVE-2026-54282 y CVE-2026-54283); se actualizó a
  `starlette==1.3.1`. Re-escaneo: **0 vulnerabilidades**.
- **Frontend:** `npm audit`: **0 vulnerabilidades**.

## SEC-10 — TLS de extremo a extremo
- Las subidas y descargas a S3 usan **presigned URLs HTTPS** (S3 fuerza TLS).
- Las llamadas del backend a AWS van por HTTPS (boto3 por defecto).
- En desarrollo, el backend corre en `http://localhost` (tráfico local). En
  **producción** se desplegaría detrás de un reverse proxy (Nginx/ALB) con
  certificado TLS, sirviendo el frontend y el backend por HTTPS.
