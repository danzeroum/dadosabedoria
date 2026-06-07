import type { Banda } from "../lib/types";

const COR: Record<Banda, string> = {
  alta: "var(--exec-alta)",
  parcial: "var(--exec-parcial)",
  baixa: "var(--exec-baixa)",
  indef: "var(--cor-texto-suave)",
};

// Donut de execução: o % gasto sobre a base divulgada, em anel. Acessível (role=img + aria-label);
// a cor vem da banda, mas o número e o aria-label dizem tudo (nunca só cor).
export function Donut({ pct, banda }: { pct: number; banda: Banda }) {
  const r = 56;
  const c = 2 * Math.PI * r;
  const usado = (c * Math.max(0, Math.min(100, pct))) / 100;
  return (
    <div className="donut" role="img" aria-label={`Executou ${pct}% do recebido divulgado por função`}>
      <svg viewBox="0 0 132 132" width="132" height="132">
        <circle cx="66" cy="66" r={r} fill="none" stroke="var(--cor-borda)" strokeWidth="14" />
        <circle
          cx="66"
          cy="66"
          r={r}
          fill="none"
          stroke={COR[banda]}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${usado} ${c}`}
          transform="rotate(-90 66 66)"
        />
      </svg>
      <span className="donut-num" aria-hidden="true">
        <b className="tnum">{pct}%</b>
        <span>do divulgado</span>
      </span>
    </div>
  );
}
