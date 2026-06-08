import Link from "next/link";

import { formatarValor } from "../lib/formato";
import type { IndicadorValor } from "../lib/types";
import { EstadoSupressao } from "./EstadoSupressao";

// Um indicador no panorama: nome (→ ficha técnica), último valor (ou o chip de protegido), período,
// fonte e o atalho "ver série" (→ histórico no município). Célula suprimida → EstadoSupressao
// "suprimido" (cadeado de privacidade: há PII por baixo, ex.: internações). Nunca mostra o número
// de uma célula protegida.
export function IndicadorCard({ ind, codigoIbge }: { ind: IndicadorValor; codigoIbge: string }) {
  return (
    <div className="indicador-card">
      <Link href={`/indicador/${ind.codigo}`} className="indicador-nome">
        {ind.nome}
      </Link>
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
      <Link
        href={`/serie?territorio=${codigoIbge}&indicador=${ind.codigo}`}
        className="indicador-serie-link"
      >
        ver série ↗
      </Link>
    </div>
  );
}
