import { CORES_PULSO, formatarSaldo } from "../lib/pulso";
import type { MesSaldo } from "../lib/types";

// Série do saldo mensal em barras a partir da linha do ZERO (positivo sobe/verde, negativo
// desce/vermelho) — SVG inline, sem biblioteca. Acessível: cada barra tem <title>, e a lista de
// rótulos abaixo repete período+saldo em texto (nunca só cor). O zero é explícito: o sinal importa.
export function SerieSaldo({ meses }: { meses: MesSaldo[] }) {
  if (meses.length === 0) {
    return <p>Sem série disponível.</p>;
  }
  const W = 480;
  const H = 180;
  const P = 28;
  const n = meses.length;
  const meio = H / 2;
  const maxAbs = Math.max(1, ...meses.map((m) => Math.abs(m.saldo)));
  const faixa = (W - 2 * P) / n;
  const larguraBarra = Math.min(48, faixa * 0.6);
  const centro = (i: number) => P + faixa * (i + 0.5);
  const altura = (s: number) => (Math.abs(s) / maxAbs) * (meio - P);

  return (
    <figure className="serie-saldo">
      <figcaption>
        Saldo de empregos formais por mês (a partir do zero; acima = criou, abaixo = perdeu)
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Série mensal do saldo de empregos formais"
        className="serie-saldo-svg"
      >
        <line x1={P} y1={meio} x2={W - P} y2={meio} className="serie-saldo-zero" />
        {meses.map((m, i) => {
          const h = altura(m.saldo);
          const y = m.saldo >= 0 ? meio - h : meio;
          const cor =
            m.saldo > 0
              ? CORES_PULSO.aquecido
              : m.saldo < 0
                ? CORES_PULSO.esfriando
                : CORES_PULSO.estavel;
          return (
            <rect
              key={m.periodo}
              x={centro(i) - larguraBarra / 2}
              y={y}
              width={larguraBarra}
              height={Math.max(1, h)}
              fill={cor}
              rx={2}
            >
              <title>{`${m.periodo}: ${formatarSaldo(m.saldo)} vagas`}</title>
            </rect>
          );
        })}
      </svg>
      <ol className="serie-saldo-rotulos">
        {meses.map((m) => (
          <li key={m.periodo}>
            <span className="serie-saldo-periodo">{m.periodo}</span>
            <span className="serie-saldo-valor">{formatarSaldo(m.saldo)}</span>
          </li>
        ))}
      </ol>
    </figure>
  );
}
