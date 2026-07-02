                                                                                                                                                                                              b# Bitácora de trabajo — ArchivaCloud P-07

Registro de las sesiones de desarrollo del proyecto. Complementa la bitácora
presencial firmada (Anexo C).

> **Plantilla para una sesión nueva** (copiar y rellenar):
> ```
> ## Sesión N — <fecha>
> - Objetivo:
> - Trabajo realizado:
> - Problemas / soluciones:
> - Estado al final:
> - Commits relevantes:
> ```

---

## Sesión 1 — Setup y Sprint 1 (10-11 jun 2026)

- **Objetivo:** montar el backend mínimo con el patrón de presigned URLs y
  conectar el bucket S3 `archivacloud-p07`.
- **Trabajo realizado:**
  - `config.py`: parámetros P-07 (extensiones `.zip`/`.tar.gz`, límite 50 MB,
    prefijo `uploads/`) y lectura de credenciales desde el `.env`.
  - `main.py`: endpoints `POST /api/upload/presigned-url` y `GET /healthz`.
  - Validación de extensión y tamaño, sanitización de `fileName`, CORS
    restrictivo, manejo de errores sin stack traces.
  - Subida real a S3 probada de punta a punta (HTTP 200).
- **Problemas / soluciones:**
  - `pip` ausente en Python 3.14 → `ensurepip`.
  - El `.env` no se cargaba (ruta relativa) → ruta absoluta con `Path`.
  - El `.env` con credenciales reales se subió a Git → se purgó del historial
    con `git filter-branch` y se rotaron las credenciales.
- **Estado al final:** Sprint 1 (backend) completo y probado.

## Sesión 2 — Sprint 2 (17-18 jun 2026)

- **Objetivo:** completar el backend (listar/eliminar) y crear el frontend base.
- **Trabajo realizado:**
  - `GET /api/files` (lista `uploads/` con paginación) y
    `DELETE /api/files/{key}` (con validación de prefijo y anti path-traversal).
  - Frontend React + Vite + axios: subir, listar, borrar, validar en cliente.
  - Tema oscuro, modal de confirmación al borrar y avisos centrados.
  - Swagger habilitado solo en modo `DEBUG=true`.
- **Problemas / soluciones:**
  - `curl` daba 422 en PowerShell 5.1 (rompía el JSON) → usar `Invoke-RestMethod`.
  - `DELETE` daba "Network Error" en el navegador → faltaba `DELETE` en el CORS
    del backend.
  - React 19 (Vite lo instala por defecto) vs stack que pide React 18 → se bajó
    a React 18 y quedó el lint limpio.
- **Estado al final:** Sprint 2 completo (backend + frontend), README y script
  de arranque.

## Sesión 3 — Sprint 3 (24-25 jun 2026)

- **Objetivo:** implementar la feature extra P-07 y verificar los 10 controles
  de seguridad.
- **Trabajo realizado:**
  - Feature extra: `GET /api/stats` (tamaño total del bucket + % de 1 GiB, con
    paginación) y barra de uso en el frontend.
  - Auditoría de seguridad: SEC-06 (Block Public Access) y SEC-08 (SSE AES256)
    verificados; reporte de seguridad con los 10 controles.
  - `pip-audit` detectó 2 CVEs en `starlette` 1.2.1 → actualizado a 1.3.1
    (SEC-09). `npm audit`: 0 vulnerabilidades.
- **Problemas / soluciones:**
  - `requirements.txt` en UTF-16 rompía `pip-audit` → reescrito en UTF-8.
- **Estado al final:** Sprint 3 cerrado (código + documentación). Pendiente
  presencial: diagrama manuscrito y bitácora firmada.

## Sesión 4 — Evaluación de continuación: DynamoDB (1 jul 2026)

- **Objetivo:** conectar el proyecto a la tabla DynamoDB `database_dynamo` ya
  creada en AWS.
- **Trabajo realizado:**
  - `dynamodb/main.py`: sube datos a `database_dynamo` leyendo las credenciales
    del `.env` (mejora del ejemplo, que las tenía hardcodeadas — SEC-01).
  - `dynamodb/gestionar.py`: CRUD por línea de comandos (agregar / editar /
    borrar / listar).
  - `iniciar.ps1` ahora también ejecuta el script de DynamoDB.
- **Problemas / soluciones:**
  - `editar`/`borrar` fallaban ("key does not match schema") → la tabla usa
    **clave compuesta** (`id_tabla` + `nombre_proyecto`); se corrigió el script
    para usar ambas claves.
- **Estado al final:** conexión a DynamoDB funcionando; CRUD probado.
