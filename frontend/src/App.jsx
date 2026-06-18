// =============================================================================
//  App.jsx  —  Componente raíz: une el formulario de subida y la lista
// =============================================================================
import { useState, useEffect, useCallback } from "react";
import UploadForm from "./components/UploadForm";
import FileList from "./components/FileList";
import { listarArchivos } from "./api";
import "./App.css";

export default function App() {
  const [archivos, setArchivos] = useState([]);
  const [error, setError] = useState("");

  //  Pide al backend la lista de archivos y la guarda en el estado.
  //  useCallback evita recrear la función en cada render (buena práctica con
  //  useEffect y al pasarla como prop a los hijos).
  const cargar = useCallback(async () => {
    try {
      const data = await listarArchivos();
      setArchivos(data.files);
      setError("");
    } catch (err) {
      const detalle = err.response?.data?.detail || err.message;
      setError("No se pudo cargar la lista: " + detalle);
    }
  }, []);

  //  Al montar la app, carga la lista una vez.
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
        {/* Cuando termina una subida, onSubido refresca la lista */}
        <UploadForm onSubido={cargar} />
      </section>

      <section className="card">
        <h2>Archivos subidos</h2>
        {error && <p className="estado error">{error}</p>}
        {/* onCambio refresca la lista tras un borrado */}
        <FileList archivos={archivos} onCambio={cargar} />
      </section>
    </div>
  );
}
