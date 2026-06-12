import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarEsgotoInvisivel } from "../../../lib/api";
import { DemoAvisoSnis } from "../../../components/DemoAvisoSnis";
import type { NivelGap } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelGap, string> = {
  adequado: "Adequado (≥ 70%)",
  atencao: "Atenção (40–69%)",
  critico: "Crítico (< 40%)",
  sem_dado: "Sem dados disponíveis",
};
const CORES_NIVEL: Record<NivelGap, string> = {
  adequado: "#16a34a",
  atencao: "#b45309",
  critico: "#dc2626",
  sem_dado: "#6b7280",
};

function formatarPct(n: number | null): string {
  if (n === null) return "—";
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " %";
}

function BarraSimples({
  label,
  pct,
  cor,
}: {
  label: string;
  pct: number | null;
  cor: string;
}) {
  const largura = pct !== null ? Math.min(Math.max(pct, 0), 100) : 0;
  return (
    <div className="giro-bloco">
      <p className="giro-label">{label}</p>
      {pct !== null ? (
        <>
          <p className="giro-numero">
            <strong>{formatarPct(pct)}</strong>
          </p>
          <div
            style={{
              background: "#e5e7eb",
              borderRadius: "4px",
              height: "12px",
              marginTop: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                background: cor,
                height: "100%",
                width: `${largura}%`,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </>
      ) : (
        <p className="giro-sem-dado">Sem dado disponível</p>
      )}
    </div>
  );
}

export default async function EsgotoInvisivelPage({
  params,
}: {
  params: { codigo: string };
}) {
  const ei = await buscarEsgotoInvisivel(params.codigo);
  if (!ei) {
    notFound();
  }

  const corNivel = CORES_NIVEL[ei.nivel_gap];
  const rotuloNivel = ROTULOS_NIVEL[ei.nivel_gap];

  return (
    <main className="pagina">
      <Link href={`/ivm/${ei.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <DemoAvisoSnis />
      <p className="pulso-pergunta">EsgotoInvisível — onde a água chega mas o esgoto some</p>
      <h1>
        {ei.nome}
        {ei.uf ? ` · ${ei.uf}` : ""}
      </h1>
      {ei.periodo && (
        <p className="giro-populacao">Exercício de referência: {ei.periodo}</p>
      )}

      <div
        className="giro-bloco"
        style={{
          borderLeft: `4px solid ${corNivel}`,
          paddingLeft: "12px",
          marginBottom: "16px",
        }}
      >
        <p className="giro-label">Coleta de esgoto (IN015_AE)</p>
        <p className="giro-numero" style={{ fontSize: "2rem" }}>
          <strong style={{ color: corNivel }}>{formatarPct(ei.esgoto_pct)}</strong>
        </p>
        <p
          className="giro-nivel"
          style={{ color: corNivel, marginTop: "4px" }}
          aria-label={`Nível: ${rotuloNivel}`}
        >
          ● <span>{rotuloNivel}</span>
        </p>
      </div>

      {ei.gap_pct !== null && ei.gap_pct > 0 && (
        <div className="giro-bloco" style={{ background: "#fef3c7", padding: "12px", borderRadius: "6px" }}>
          <p className="giro-label">Gap: água sem esgoto</p>
          <p className="giro-numero">
            <strong>{formatarPct(ei.gap_pct)}</strong> da população tem água encanada mas
            sem coleta de esgoto — o efluente vai para rios, solo ou fossas.
          </p>
        </div>
      )}

      <div className="giro-painel" style={{ marginTop: "16px" }}>
        <BarraSimples
          label={`Atendimento de água${ei.periodo ? ` · ${ei.periodo}` : ""}`}
          pct={ei.agua_pct}
          cor="#2563eb"
        />
        <BarraSimples
          label={`Coleta de esgoto${ei.periodo ? ` · ${ei.periodo}` : ""}`}
          pct={ei.esgoto_pct}
          cor={corNivel}
        />
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{ei.nota}</p>
      </section>

      {(ei.meta_esgoto || ei.meta_agua) && (
        <dl className="giro-meta">
          {ei.meta_esgoto && (
            <div>
              <dt>Fonte (esgoto)</dt>
              <dd>
                {ei.meta_esgoto.fonte} · {ei.meta_esgoto.metodologia}
                {ei.meta_esgoto.lag_tipico_dias != null
                  ? ` · atraso ~${ei.meta_esgoto.lag_tipico_dias} dias`
                  : ""}
                {" "}· {ei.meta_esgoto.licenca}
              </dd>
            </div>
          )}
          {ei.meta_agua && (
            <div>
              <dt>Fonte (água)</dt>
              <dd>
                {ei.meta_agua.fonte} · {ei.meta_agua.metodologia}
                {ei.meta_agua.lag_tipico_dias != null
                  ? ` · atraso ~${ei.meta_agua.lag_tipico_dias} dias`
                  : ""}
                {" "}· {ei.meta_agua.licenca}
              </dd>
            </div>
          )}
        </dl>
      )}

      <p style={{ marginTop: "16px" }}>
        <Link href={`/agua-viva/${ei.codigo_ibge}`}>
          Ver cobertura completa de água e esgoto (AguaViva) →
        </Link>
        <br />
        <Link href={`/ivm/${ei.codigo_ibge}`}>
          Ver o Índice de Vulnerabilidade Municipal →
        </Link>
        <br />
        <Link href={`/municipio/${ei.codigo_ibge}`}>
          Ver o panorama completo do município →
        </Link>
      </p>
    </main>
  );
}
