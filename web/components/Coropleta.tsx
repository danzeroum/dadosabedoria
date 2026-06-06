import { projetar } from "../lib/geo";
import { COR_SEM_DADO, corSemaforo } from "../lib/semaforo";
import type { FeatureCollectionIVM } from "../lib/types";

// Mapa coroplético (SVG). Município com IVM é clicável (→ drill-down); sem dado fica cinza.
export function Coropleta({ malha, uf }: { malha: FeatureCollectionIVM; uf: string }) {
  if (malha.features.length === 0) {
    return (
      <p className="vazio">
        Sem geometrias para {uf}. Carregue com <code>python -m app.ingestao.run_ibge {uf}</code>.
      </p>
    );
  }
  const { viewBox, formas } = projetar(malha);
  return (
    <figure className="coropleta">
      <svg viewBox={viewBox} role="img" aria-label={`Mapa do IVM — ${uf}`} className="coropleta-svg">
        {formas.map((f) => {
          const cor = f.semaforo ? corSemaforo(f.semaforo) : COR_SEM_DADO;
          const titulo =
            f.ivm == null ? `${f.nome}: sem dado` : `${f.nome}: IVM ${f.ivm.toFixed(1)}`;
          const area = (
            <path d={f.d} fill={cor} className="coropleta-area">
              <title>{titulo}</title>
            </path>
          );
          return f.ivm == null ? (
            <g key={f.codigo_ibge}>{area}</g>
          ) : (
            <a key={f.codigo_ibge} href={`/ivm/${f.codigo_ibge}`} className="coropleta-link">
              {area}
            </a>
          );
        })}
      </svg>
    </figure>
  );
}
