// =============================================================================
//  BucketStats.jsx  —  FEATURE EXTRA P-07
// -----------------------------------------------------------------------------
//  Muestra el espacio ocupado en el bucket con una barra de progreso y el
//  porcentaje frente a la cuota de 1 GB. Recibe las estadísticas ya calculadas
//  por el backend (endpoint /api/stats) a través de la prop `stats`.
// =============================================================================
import { formatoTamano } from "../utils";

export default function BucketStats({ stats }) {
  //  Mientras no hay datos (o el backend falló), no se muestra nada.
  if (!stats) return null;

  //  La barra nunca pasa de 100% aunque el bucket supere la cuota.
  const ancho = Math.min(stats.porcentaje, 100);
  //  Si supera el 90%, la barra se pinta de rojo como advertencia.
  const clase = stats.porcentaje >= 90 ? "stats-relleno lleno" : "stats-relleno";

  return (
    <div className="stats">
      <div className="stats-texto">
        <span>
          {formatoTamano(stats.totalBytes)} de {formatoTamano(stats.limitBytes)}
        </span>
        <span className="stats-pct">{stats.porcentaje}%</span>
      </div>
      <div className="stats-barra">
        <div className={clase} style={{ width: ancho + "%" }} />
      </div>
      <p className="stats-sub">{stats.count} archivo(s) en el bucket</p>
    </div>
  );
}
