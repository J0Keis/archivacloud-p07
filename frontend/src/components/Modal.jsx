// =============================================================================
//  Modal.jsx  —  Ventana modal genérica, centrada en la pantalla
// -----------------------------------------------------------------------------
//  Dibuja una capa oscura semitransparente (overlay) que cubre toda la pantalla
//  y, encima, una caja centrada con el contenido. Hacer clic FUERA de la caja
//  (en el overlay) la cierra; el clic DENTRO no se propaga para no cerrarla.
// =============================================================================
export default function Modal({ children, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-caja" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}
