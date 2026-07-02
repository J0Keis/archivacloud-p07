# Declaración de uso de IA — ArchivaCloud P-07 (Anexo A)

## Herramienta utilizada
**Claude Code** (Anthropic) — asistente de IA generativa, usado desde la terminal.

## Alcance del uso
La IA se usó como **asistente de programación**: generar código base, depurar
errores, explicar conceptos, documentar y aprender buenas prácticas. Todo el
código fue **revisado, entendido y probado** por los integrantes, que pueden
defender cada línea. Las conversaciones completas se conservan y se muestran
presencialmente como evidencia.

---

## Uso por sprint

### Sprint 1 (10-11 jun 2026) — Setup y backend
- **Para qué se usó:** generar `config.py` y `main.py` (presigned URL,
  validaciones de extensión/tamaño, sanitización, CORS), resolver el error de
  carga del `.env` y remediar el incidente de credenciales en Git.
- **Prompt representativo (10 jun 2026):** *"Genera dentro de backend/: config.py que lee las
  variables del .env... main.py con FastAPI: GET /healthz y POST
  /api/upload/presigned-url; valida extensión y tamaño; CORS restrictivo..."*

### Sprint 2 (17-18 jun 2026) — Endpoints y frontend
- **Para qué se usó:** implementar `GET /api/files` y `DELETE /api/files/{key}`,
  crear el frontend (React + Vite + axios) con subida/lista/borrado, tema oscuro
  y modales; depurar el error de CORS en el DELETE y el quoting de PowerShell.
- **Prompt representativo (17 jun 2026):** *"podemos seguir con el sprint 2 ayudándome a
  realizar commits entre cada uno de los cambios..."*

### Sprint 3 (24-25 jun 2026) — Feature extra y seguridad
- **Para qué se usó:** implementar la feature extra P-07 (`GET /api/stats` +
  barra de uso), auditoría de los controles SEC-01 a SEC-10, escaneo con
  `pip-audit` (que detectó y mitigó 2 CVEs) y el reporte de seguridad.
- **Prompt representativo (24 jun 2026):** *"ahora hay que realizar el sprint 3"*

### Sesión 4 (1 jul 2026) — DynamoDB (evaluación de continuación)
- **Para qué se usó:** conectar el proyecto a la tabla `database_dynamo`, crear
  el script CRUD (`gestionar.py`) y resolver el problema de la clave compuesta.
- **Prompt representativo (1 jul 2026):** *"cómo puedo conectar dynamoDB a este proyecto...
  esto es para la siguiente evaluación..."*

---

## Transparencia y autoría
- Los integrantes **entienden y pueden explicar** cada archivo y decisión.
- Las **conversaciones completas** con la IA se conservan y se presentan como
  evidencia ante la docente.
- Cuando la IA cometió errores (p. ej. olvidar `DELETE` en el CORS), se
  detectaron probando el proyecto y se corrigieron entendiendo la causa — no se
  copió código a ciegas.
