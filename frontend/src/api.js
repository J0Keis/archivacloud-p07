// =============================================================================
//  api.js  —  Capa de comunicación con el backend FastAPI
// -----------------------------------------------------------------------------
//  Centraliza la configuración de axios y TODAS las llamadas a la API en un
//  solo sitio. Así los componentes no repiten URLs ni lógica de red, y si
//  cambia el backend solo se toca este archivo.
// =============================================================================
import axios from "axios";

//  URL base del backend. Se lee de la variable de entorno de Vite VITE_API_URL
//  si existe (útil para producción); si no, usa localhost:8000 (desarrollo).
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

//  Instancia de axios preconfigurada con la URL base del backend.
const api = axios.create({ baseURL: API_URL });

//  1) Pide al backend una URL firmada (presigned) para subir un archivo.
//     Devuelve { presignedUrl, key, publicUrl }.
export async function pedirPresignedUrl(fileName, fileType, fileSize) {
  const { data } = await api.post("/api/upload/presigned-url", {
    fileName,
    fileType,
    fileSize,
  });
  return data;
}

//  2) Sube el archivo DIRECTO a S3 con la URL firmada (PUT).
//     IMPORTANTE: el Content-Type del PUT debe ser EXACTAMENTE el mismo que se
//     usó al pedir la URL; si no, S3 responde SignatureDoesNotMatch. Por eso
//     el contentType se pasa explícito y no se deja a que axios lo adivine.
export async function subirAS3(presignedUrl, file, contentType) {
  await axios.put(presignedUrl, file, {
    headers: { "Content-Type": contentType },
  });
}

//  3) Lista los archivos subidos (el backend solo mira el prefijo uploads/).
//     Devuelve { count, files: [{ key, size, lastModified }] }.
export async function listarArchivos() {
  const { data } = await api.get("/api/files");
  return data;
}

//  4) Elimina un archivo por su key. Devuelve { deleted }.
export async function eliminarArchivo(key) {
  const { data } = await api.delete(`/api/files/${key}`);
  return data;
}
