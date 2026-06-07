import { EstadoSupressao } from "./EstadoSupressao";
import type { ExeEstado } from "../lib/types";

function Barra({ rotulo, valor }: { rotulo: string; valor: number }) {
  const pct = Math.max(0, Math.min(100, valor));
  return (
    <div className="barra-linha">
      <span className="barra-rotulo">{rotulo}</span>
      <span className="barra-trilha" aria-hidden="true">
        <span className="barra-preenchida" style={{ width: `${pct}%` }} />
      </span>
      <span className="barra-valor">{valor.toFixed(0)}</span>
    </div>
  );
}

// Compara os subíndices de vulnerabilidade (maior = mais vulnerável).
// Saúde é opcional: só aparece onde há dado não suprimido no período (multidomínio, ADR-0025).
export function Comparador({
  vEmprego,
  vFinancas,
  vSaude,
  vSaudeEstado,
}: {
  vEmprego: number;
  vFinancas: number;
  vSaude?: number | null;
  vSaudeEstado?: ExeEstado;
}) {
  return (
    <div className="comparador" role="group" aria-label="Subíndices de vulnerabilidade">
      <Barra rotulo="Emprego" valor={vEmprego} />
      <Barra rotulo="Finanças" valor={vFinancas} />
      {vSaudeEstado === "valor" && vSaude != null ? (
        <Barra rotulo="Saúde" valor={vSaude} />
      ) : vSaudeEstado && vSaudeEstado !== "valor" ? (
        <EstadoSupressao estado={vSaudeEstado} rotulo="Saúde" />
      ) : null}
    </div>
  );
}
