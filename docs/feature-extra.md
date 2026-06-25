# Documentación de la feature extra — Pareja P-07

## Qué hace

Muestra el **espacio total ocupado** en el bucket S3 y el **porcentaje frente a
una cuota de 1 GB**. En el frontend aparece como una barra de progreso en la
tarjeta **"Espacio usado"**, que se actualiza al subir o borrar archivos.

## Cómo funciona

- **Backend** — endpoint `GET /api/stats`: recorre todos los objetos bajo
  `uploads/`, suma sus tamaños y calcula el porcentaje frente a 1 GiB.
- **Frontend** — componente `BucketStats`: pinta la barra con los datos que
  devuelve el backend.

Ejemplo de respuesta del endpoint:
```json
{ "count": 4, "totalBytes": 3258049, "limitBytes": 1073741824, "porcentaje": 0.3 }
```
→ *4 archivos · 3.11 MB usados · 0.3 % de 1 GB.*

## Por qué se eligió este diseño

1. **El cálculo va en el backend, no en el cliente.** Por seguridad y para
   centralizar la lógica de negocio (mismo principio que las validaciones): el
   frontend solo pinta la barra, no decide nada.
2. **Paginación con `ContinuationToken`.** `list_objects_v2` devuelve como mucho
   1000 objetos por llamada; paginamos para sumar TODOS aunque el bucket tenga
   más de 1000 archivos. Así el total siempre es correcto.
3. **Cuota de 1 GiB (1024³).** Usamos base binaria para ser coherentes con el
   límite de tamaño de archivo (50 MB = 50 × 1024²). Es una cuota de referencia
   nuestra, no un límite real de S3.
4. **Configurable en una línea.** `config.py` → `BUCKET_LIMIT_BYTES = 1024 ** 3`.
5. **Aviso visual.** La barra se pinta de rojo al superar el 90 % de la cuota.

## Capturas

> Añadir aquí las capturas de pantalla:
> - **Captura 1:** la barra "Espacio usado" en el frontend (con un porcentaje).
> - **Captura 2:** subir un archivo y ver que la barra crece.
> - **Captura 3:** respuesta del endpoint `GET /api/stats` (en Swagger `/docs`).

## Archivos relevantes

| Archivo | Rol |
|---|---|
| `backend/app/main.py` | endpoint `bucket_stats()` (cálculo + paginación) |
| `backend/app/config.py` | `BUCKET_LIMIT_BYTES` (cuota de 1 GiB) |
| `frontend/src/components/BucketStats.jsx` | barra de progreso |
| `frontend/src/api.js` | `obtenerStats()` (llamada a la API) |
