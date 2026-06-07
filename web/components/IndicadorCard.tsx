import { formatarValor } from "../lib/formato";
import type { IndicadorValor } from "../lib/types";
import { EstadoSupressao } from "./EstadoSupressao";

// Um indicador no panorama: nome, último valor (ou o chip de protegido), período e fonte.
// Célula suprimida → EstadoSupressao "suprimido" (cadeado de privacidade: há PII por baixo, ex.:
// internações). Nunca mostra o número de uma célula protegida.
export function IndicadorCard({ ind }: { ind: IndicadorValor }) {
  return (
    <div className="indicador-card">
      <span className="indicador-nome">{ind.nome}</span>
      <span className="indicador-valor">
        {ind.suprimido ? (
          <EstadoSupressao estado="suprimido" rotulo="Valor" />
        ) : ind.valor != null ? (
          formatarValor(ind.valor, ind.unidade)
        ) : (
          "—"
        )}
      </span>
      <span className="indicador-meta">
        {ind.periodo} · {ind.fonte}
      </span>
    </div>
  );
}
