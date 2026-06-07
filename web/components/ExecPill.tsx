import { rotuloBanda } from "../lib/onde-foi";
import type { Banda } from "../lib/types";

// Pílula de execução honesta: número + palavra. A cor é redundante com o texto + sr-only (a banda
// é sinal de atenção, não veredito — ADR-0026).
export function ExecPill({ banda, pct }: { banda: Banda; pct: number | null }) {
  return (
    <span className={`exec-pill exec-${banda}`}>
      <span>{pct != null ? `liquidou ${pct}%` : "—"}</span>
      <span className="sr-only"> — {rotuloBanda(banda)} do que empenhou</span>
    </span>
  );
}
