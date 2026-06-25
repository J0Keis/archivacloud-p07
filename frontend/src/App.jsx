// =============================================================================
//  App.jsx  —  Componente raíz: subida, espacio usado, lista y avisos
// =============================================================================
import { useState, useEffect, useCallback } from "react";
import UploadForm from "./components/UploadForm";
import FileList from "./components/FileList";
import BucketStats from "./components/BucketStats";
import Modal from "./components/Modal";
import { listarArchivos, obtenerStats } from "./api";
import "./App.css";

export default function App() {
  const [archivos, setArchivos] = useState([]);
  const [stats, setStats] = useState(null);
  //  Aviso global mostrado en un recuadro centrado: { tipo: 'ok'|'error', mensaje }
  const [aviso, setAviso] = useState(null);

  //  Función que cualquier hijo usa para mostrar un aviso centrado.
  const notificar = useCallback((tipo, mensaje) => {
    setAviso({ tipo, mensaje });
  }, []);

  //  Carga la lista y, por separado, las estadísticas del bucket. Si las
  //  estadísticas fallan, la lista igual se muestra (no son críticas).
  const cargar = useCallback(async () => {
    try {
      const data = await listarArchivos();
      setArchivos(data.files);
    } catch (err) {
      const detalle = err.response?.data?.detail || err.message;
      notificar("error", "No se pudo cargar la lista: " + detalle);
    }
    try {
      const s = await obtenerStats();
      setStats(s);
    } catch {
      setStats(null);
    }
  }, [notificar]);

  //  Al montar la app, carga lista + estadísticas una vez.
  useEffect(() => {
    cargar();
  }, [cargar]);

  return (
    <div className="contenedor">
      <header>
        <h1>ArchivaCloud P-07</h1>
        <p className="subtitulo">Portal de carga de archivos a Amazon S3</p>
      </header>

      <section className="card">
        <h2>Subir archivo</h2>
        <UploadForm onSubido={cargar} notificar={notificar} />
      </section>

      <section className="card">
        <h2>Espacio usado</h2>
        <BucketStats stats={stats} />
      </section>

      <section className="card">
        <h2>Archivos subidos</h2>
        <FileList archivos={archivos} onCambio={cargar} notificar={notificar} />
      </section>

      {/* Recuadro de aviso centrado (éxito o error) */}
      {aviso && (
        <Modal onClose={() => setAviso(null)}>
          <div className={"aviso aviso-" + aviso.tipo}>
            <p>{aviso.mensaje}</p>
            <button onClick={() => setAviso(null)}>Aceptar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
