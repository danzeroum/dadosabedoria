import { corSemaforo } from "../lib/semaforo";
import type { IVMItem } from "../lib/types";

// Série do IVM (0–100) em SVG inline — sem dependência de biblioteca de gráficos.
export function SerieTemporal({ serie }: { serie: IVMItem[] }) {
  if (serie.length === 0) {
    return <p>Sem série disponível.</p>;
  }
  const W = 480;
  const H = 160;
  const P = 24;
  const n = serie.length;
  const x = (i: number) => P + (i * (W - 2 * P)) / Math.max(1, n - 1);
  const y = (ivm: number) => H - P - (ivm / 100) * (H - 2 * P);
  const pontos = serie.map((d, i) => `${x(i)},${y(d.ivm)}`).join(" ");

  return (
    <figure className="serie">
      <figcaption>IVM ao longo do tempo (0–100, maior = mais vulnerável)</figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Série temporal do IVM" className="serie-svg">
        <line x1={P} y1={H - P} x2={W - P} y2={H - P} className="serie-eixo" />
        {n > 1 && <polyline points={pontos} className="serie-linha" fill="none" />}
        {serie.map((d, i) => (
          <circle key={d.periodo} cx={x(i)} cy={y(d.ivm)} r={4} fill={corSemaforo(d.semaforo)}>
            <title>{`${d.periodo}: IVM ${d.ivm.toFixed(1)}`}</title>
          </circle>
        ))}
      </svg>
      <ol className="serie-rotulos" aria-hidden="true">
        {serie.map((d) => (
          <li key={d.periodo}>{d.periodo}</li>
        ))}
      </ol>
    </figure>
  );
}
