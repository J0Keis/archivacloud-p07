// =============================================================================
//  UploadForm.jsx  —  Formulario de subida de archivos
// -----------------------------------------------------------------------------
//  Flujo: el usuario elige un archivo -> se valida en el cliente -> se pide la
//  URL firmada al backend -> se sube DIRECTO a S3 con esa URL.
// =============================================================================
import { useState } from "react";
import { pedirPresignedUrl, subirAS3 } from "../api";

//  Validaciones del lado del cliente. Son un ESPEJO de las del backend: el
//  backend SIEMPRE revalida (no confiamos en el cliente), pero validar aquí
//  mejora la experiencia. Controles SEC-03 (extensión) y SEC-04 (tamaño).
const EXTENSIONES_OK = [".zip", ".tar.gz"];
const TAM_MAX = 50 * 1024 * 1024; // 50 MB

//  Detecta la extensión tratando bien la doble extensión .tar.gz.
function extensionDe(nombre) {
  const lower = nombre.toLowerCase();
  if (lower.endsWith(".tar.gz")) return ".tar.gz";
  const punto = lower.lastIndexOf(".");
  return punto === -1 ? "" : lower.slice(punto);
}

export default function UploadForm({ onSubido, notificar }) {
  const [archivo, setArchivo] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [progreso, setProgreso] = useState(""); // texto de progreso, inline

  async function manejarSubida(e) {
    e.preventDefault();
    if (!archivo) return;

    //  Validación de extensión (lista blanca) -> aviso centrado si falla
    const ext = extensionDe(archivo.name);
    if (!EXTENSIONES_OK.includes(ext)) {
      notificar("error", "Solo se permiten archivos .zip y .tar.gz");
      return;
    }
    //  Validación de tamaño
    if (archivo.size > TAM_MAX) {
      notificar("error", "El archivo supera el límite de 50 MB");
      return;
    }

    try {
      setSubiendo(true);
      //  El Content-Type debe ser el mismo al firmar y al subir.
      const contentType = archivo.type || "application/octet-stream";

      setProgreso("Pidiendo permiso de subida...");
      const { presignedUrl } = await pedirPresignedUrl(
        archivo.name,
        contentType,
        archivo.size
      );

      setProgreso("Subiendo a S3...");
      await subirAS3(presignedUrl, archivo, contentType);

      setProgreso("");
      notificar("ok", "Archivo subido correctamente.");
      setArchivo(null);
      e.target.reset();
      if (onSubido) onSubido(); // refresca la lista
    } catch (err) {
      setProgreso("");
      const detalle = err.response?.data?.detail || err.message;
      notificar("error", "Error al subir: " + detalle);
    } finally {
      setSubiendo(false);
    }
  }

  return (
    <form onSubmit={manejarSubida} className="upload-form">
      <input
        type="file"
        accept=".zip,.tar.gz"
        onChange={(e) => setArchivo(e.target.files[0] || null)}
      />
      <button type="submit" disabled={subiendo || !archivo}>
        {subiendo ? "Subiendo..." : "Subir"}
      </button>
      {progreso && <p className="estado">{progreso}</p>}
    </form>
  );
}
