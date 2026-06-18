// =============================================================================
//  FileList.jsx  —  Tabla de archivos subidos, con opción de eliminar
// =============================================================================
import { eliminarArchivo } from "../api";

//  Muestra el tamaño en B / KB / MB de forma legible.
function formatoTamano(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

//  La key en S3 es "uploads/<uuid>_nombre.zip". Para mostrarla al usuario
//  quitamos el prefijo "uploads/" y el UUID, dejando solo el nombre original.
function nombreLegible(key) {
  const sinPrefijo = key.replace(/^uploads\//, "");
  const guion = sinPrefijo.indexOf("_");
  return guion === -1 ? sinPrefijo : sinPrefijo.slice(guion + 1);
}

export default function FileList({ archivos, onCambio }) {
  async function borrar(key) {
    if (!window.confirm("¿Eliminar este archivo?")) return;
    try {
      await eliminarArchivo(key);
      if (onCambio) onCambio(); // refresca la lista en el padre
    } catch (err) {
      const detalle = err.response?.data?.detail || err.message;
      alert("Error al eliminar: " + detalle);
    }
  }

  //  Caso lista vacía.
  if (!archivos || archivos.length === 0) {
    return <p className="vacio">No hay archivos subidos todavía.</p>;
  }

  return (
    <table className="file-list">
      <thead>
        <tr>
          <th>Archivo</th>
          <th>Tamaño</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {archivos.map((f) => (
          <tr key={f.key}>
            <td>{nombreLegible(f.key)}</td>
            <td>{formatoTamano(f.size)}</td>
            <td>
              <button className="btn-borrar" onClick={() => borrar(f.key)}>
                Eliminar
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
