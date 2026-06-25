// =============================================================================
//  FileList.jsx  —  Tabla de archivos subidos, con confirmación al eliminar
// =============================================================================
import { useState } from "react";
import { eliminarArchivo } from "../api";
import { formatoTamano } from "../utils";
import Modal from "./Modal";

//  La key en S3 es "uploads/<uuid>_nombre.zip". Para mostrarla al usuario
//  quitamos el prefijo "uploads/" y el UUID, dejando solo el nombre original.
function nombreLegible(key) {
  const sinPrefijo = key.replace(/^uploads\//, "");
  const guion = sinPrefijo.indexOf("_");
  return guion === -1 ? sinPrefijo : sinPrefijo.slice(guion + 1);
}

export default function FileList({ archivos, onCambio, notificar }) {
  //  Guarda la key del archivo que se está por borrar. Si es null, no hay
  //  confirmación abierta. Sustituye al window.confirm() nativo por un modal.
  const [porBorrar, setPorBorrar] = useState(null);

  async function confirmarBorrado() {
    const key = porBorrar;
    setPorBorrar(null); // cierra el modal
    try {
      await eliminarArchivo(key);
      notificar("ok", "Archivo eliminado correctamente.");
      onCambio(); // refresca la lista
    } catch (err) {
      const detalle = err.response?.data?.detail || err.message;
      notificar("error", "Error al eliminar: " + detalle);
    }
  }

  return (
    <>
      {!archivos || archivos.length === 0 ? (
        <p className="vacio">No hay archivos subidos todavía.</p>
      ) : (
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
                  <button className="btn-borrar" onClick={() => setPorBorrar(f.key)}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Modal de confirmación de borrado (centrado) */}
      {porBorrar && (
        <Modal onClose={() => setPorBorrar(null)}>
          <div className="confirm">
            <h3>¿Eliminar archivo?</h3>
            <p>{nombreLegible(porBorrar)}</p>
            <p className="confirm-sub">Esta acción no se puede deshacer.</p>
            <div className="confirm-botones">
              <button className="btn-cancelar" onClick={() => setPorBorrar(null)}>
                Cancelar
              </button>
              <button className="btn-borrar" onClick={confirmarBorrado}>
                Eliminar
              </button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
