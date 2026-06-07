import { DESCRICAO_BANDA, corBanda, rotuloBanda } from "../lib/onde-foi";
import type { Banda } from "../lib/types";

// Selo da BANDA de execução (sinal de atenção, não veredito — ADR-0026). Acessível: a cor é
// redundante com o rótulo + a descrição em sr-only (executar ≠ entregar). Mesmo primitivo do
// Semaforo/PulsoSelo (ADR-0009).
export function BandaSelo({ banda }: { banda: Banda }) {
  const rotulo = rotuloBanda(banda);
  const descricao = DESCRICAO_BANDA[banda];
  return (
    <span className={`banda-selo banda-${banda}`} title={descricao}>
      <span className="banda-dot" style={{ backgroundColor: corBanda(banda) }} aria-hidden="true" />
      <span className="banda-rotulo">{rotulo}</span>
      <span className="sr-only"> — {descricao}</span>
    </span>
  );
}
