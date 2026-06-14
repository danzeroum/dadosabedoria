import type { RespostaQuota } from "../lib/types";

// Anel de cota (mesmo padrão do Donut do OndeFoi): arco e número mostram o RESTANTE da janela —
// alinhados, conforme o handoff. Acessível (role=img + aria-label): a cor reforça, mas o número e
// o rótulo dizem tudo (nunca só cor).
export function BarraQuota({ q }: { q: RespostaQuota }) {
  const r = 56;
  const c = 2 * Math.PI * r;
  const frac = q.limite > 0 ? Math.max(0, Math.min(1, q.restante / q.limite)) : 0;
  const arco = c * frac;
  // Verde quando sobra folga, âmbar quando aperta, vermelho quando quase esgotado.
  const cor =
    frac >= 0.5 ? "var(--exec-alta)" : frac >= 0.2 ? "var(--exec-parcial)" : "var(--exec-baixa)";
  return (
    <div
      className="barra-quota"
      role="img"
      aria-label={`Restam ${q.restante} de ${q.limite} requisições na janela atual`}
    >
      <svg viewBox="0 0 132 132" width="132" height="132">
        <circle cx="66" cy="66" r={r} fill="none" stroke="var(--cor-borda)" strokeWidth="14" />
        <circle
          cx="66"
          cy="66"
          r={r}
          fill="none"
          stroke={cor}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${arco} ${c}`}
          transform="rotate(-90 66 66)"
        />
      </svg>
      <span className="barra-quota-num" aria-hidden="true">
        <b className="tnum">{q.restante}</b>
        <span>restantes</span>
      </span>
    </div>
  );
}
