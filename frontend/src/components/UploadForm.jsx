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
//  mejora la experiencia (avisa al instante, sin molestar al servidor).
//  Controles SEC-03 (extensión) y SEC-04 (tamaño).
const EXTENSIONES_OK = [".zip", ".tar.gz"];
const TAM_MAX = 50 * 1024 * 1024; // 50 MB

//  Detecta la extensión tratando bien la doble extensión .tar.gz
//  (igual que get_extension() del backend).
function extensionDe(nombre) {
  const lower = nombre.toLowerCase();
  if (lower.endsWith(".tar.gz")) return ".tar.gz";
  const punto = lower.lastIndexOf(".");
  return punto === -1 ? "" : lower.slice(punto);
}

export default function UploadForm({ onSubido }) {
  const [archivo, setArchivo] = useState(null);
  const [estado, setEstado] = useState("");
  const [subiendo, setSubiendo] = useState(false);

  async function manejarSubida(e) {
    e.preventDefault();
    if (!archivo) return;

    //  Validación de extensión (lista blanca)
    const ext = extensionDe(archivo.name);
    if (!EXTENSIONES_OK.includes(ext)) {
      setEstado("Solo se permiten archivos .zip y .tar.gz");
      return;
    }
    //  Validación de tamaño
    if (archivo.size > TAM_MAX) {
      setEstado("El archivo supera el límite de 50 MB");
      return;
    }

    try {
      setSubiendo(true);
      //  El Content-Type debe ser el mismo al firmar y al subir. Lo calculamos
      //  una sola vez aquí para garantizar que coincida en ambas llamadas.
      const contentType = archivo.type || "application/octet-stream";

      setEstado("Pidiendo permiso de subida...");
      const { presignedUrl } = await pedirPresignedUrl(
        archivo.name,
        contentType,
        archivo.size
      );

      setEstado("Subiendo a S3...");
      await subirAS3(presignedUrl, archivo, contentType);

      setEstado("✓ Subido correctamente.");
      setArchivo(null);
      e.target.reset();
      if (onSubido) onSubido(); // avisa al padre para refrescar la lista
    } catch (err) {
      //  Mostramos el mensaje del backend si lo hay, o el de red.
      const detalle = err.response?.data?.detail || err.message;
      setEstado("Error al subir: " + detalle);
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
      {estado && <p className="estado">{estado}</p>}
    </form>
  );
}
