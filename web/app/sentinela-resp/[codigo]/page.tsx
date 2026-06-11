import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarSentinelaResp } from "../../../lib/api";
import type {
  MesInternacoesProduto,
  NivelSentinela,
  TendenciaSentinela,
} from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelSentinela, string> = {
  elevado: "Carga elevada (≥ 10/100k hab)",
  moderado: "Carga moderada (3–9/100k hab)",
  baixo: "Carga baixa (< 3/100k hab)",
  suprimido: "Protegido (k-anonimato)",
  sem_dado: "Sem dados",
};
const CORES_NIVEL: Record<NivelSentinela, string> = {
  elevado: "#b91c1c",
  moderado: "#b45309",
  baixo: "#15803d",
  suprimido: "#6b7280",
  sem_dado: "#6b7280",
};

const ROTULOS_TENDENCIA: Record<TendenciaSentinela, string> = {
  subindo: "↑ Subindo",
  caindo: "↓ Caindo",
  estavel: "→ Estável",
};
const CORES_TENDENCIA: Record<TendenciaSentinela, string> = {
  subindo: "#b91c1c",
  caindo: "#15803d",
  estavel: "#b45309",
};

function BarraHistorica({ meses }: { meses: MesInternacoesProduto[] }) {
  if (meses.length === 0) return null;
  const maxVal = Math.max(...meses.map((m) => m.internacoes ?? 0), 1);

  return (
    <div className="sentinela-historico" aria-label="Série histórica de internações">
      {meses.map((m) => (
        <div key={m.periodo} className="sentinela-barra-item">
          <div
            className="sentinela-barra"
            style={{
              height: m.suprimido ? "12px" : `${Math.max(4, ((m.internacoes ?? 0) / maxVal) * 80)}px`,
              backgroundColor: m.suprimido ? "#9ca3af" : "#3b82f6",
              opacity: m.suprimido ? 0.5 : 1,
              minHeight: "4px",
            }}
            title={
              m.suprimido
                ? `${m.periodo}: Protegido (k-anonimato)`
                : `${m.periodo}: ${m.internacoes?.toLocaleString("pt-BR")} internações`
            }
          />
          <span className="sentinela-barra-label">{m.periodo.slice(5)}</span>
        </div>
      ))}
    </div>
  );
}

export default async function SentinelaRespPage({ params }: { params: { codigo: string } }) {
  const s = await buscarSentinelaResp(params.codigo);
  if (!s) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${s.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <p className="pulso-pergunta">Sentinela Respiratória — internações SUS por doenças respiratórias</p>
      <h1>
        {s.nome}
        {s.uf ? ` · ${s.uf}` : ""}
      </h1>
      {s.populacao != null && (
        <p className="giro-populacao">{s.populacao.toLocaleString("pt-BR")} hab · população estimada IBGE</p>
      )}

      <div className="giro-painel">
        {/* Bloco principal — internações do mês mais recente */}
        <div className="giro-bloco">
          <p className="giro-label">
            Internações respiratórias (SIH/SUS){s.periodo ? ` · ${s.periodo}` : ""}
          </p>
          {s.suprimido ? (
            <>
              <p className="giro-numero">
                <strong style={{ color: "#6b7280" }}>Protegido</strong>
                <span className="giro-rotulo-numero">k-anonimato ADR-0004</span>
              </p>
              <p className="sentinela-suprimido-aviso">
                Houve internações, mas em número pequeno demais para divulgar com segurança (&lt; 5).
              </p>
            </>
          ) : s.internacoes != null ? (
            <>
              <p className="giro-numero">
                <strong>{s.internacoes.toLocaleString("pt-BR")}</strong>
                <span className="giro-rotulo-numero">internações no mês</span>
              </p>
              {s.internacoes_por_100k != null && (
                <p className="giro-per-capita">{s.internacoes_por_100k.toFixed(1)} por 100 mil hab</p>
              )}
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
          <p
            className="giro-nivel"
            style={{ color: CORES_NIVEL[s.nivel] }}
            aria-label={`Nível: ${ROTULOS_NIVEL[s.nivel]}`}
          >
            ● <span>{ROTULOS_NIVEL[s.nivel]}</span>
          </p>
        </div>

        {/* Bloco de tendência */}
        <div className="giro-bloco">
          <p className="giro-label">Tendência (mês atual vs. anterior)</p>
          {s.tendencia != null ? (
            <p
              className="giro-nivel"
              style={{ color: CORES_TENDENCIA[s.tendencia], fontSize: "1.4rem", marginTop: "12px" }}
              aria-label={`Tendência: ${ROTULOS_TENDENCIA[s.tendencia]}`}
            >
              {ROTULOS_TENDENCIA[s.tendencia]}
            </p>
          ) : (
            <p className="giro-sem-dado">Sem comparação disponível</p>
          )}
          <p style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "8px" }}>
            Calculada sobre os dois últimos meses com dado real (ignora meses protegidos).
          </p>
        </div>
      </div>

      {/* Série histórica */}
      {s.meses.length > 0 && (
        <section style={{ marginTop: "24px" }}>
          <h2 style={{ fontSize: "1rem", marginBottom: "8px" }}>Série histórica</h2>
          <BarraHistorica meses={s.meses} />
          <ul className="sentinela-lista-meses">
            {s.meses.map((m) => (
              <li key={m.periodo} className="sentinela-mes-item">
                <span className="sentinela-mes-periodo">{m.periodo}</span>
                {m.suprimido ? (
                  <span className="sentinela-mes-protegido" title="k-anonimato: menos de 5 internações">
                    Protegido
                  </span>
                ) : (
                  <span className="sentinela-mes-valor">
                    {m.internacoes?.toLocaleString("pt-BR")} internações
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{s.nota}</p>
      </section>

      {s.meta && (
        <dl className="giro-meta">
          <div>
            <dt>Fonte</dt>
            <dd>
              {s.meta.fonte} · {s.meta.metodologia}
              {s.meta.lag_tipico_dias != null ? ` · atraso ~${s.meta.lag_tipico_dias} dias` : ""}{" "}
              · {s.meta.licenca}
            </dd>
          </div>
        </dl>
      )}

      <p style={{ marginTop: "16px" }}>
        <Link href={`/municipio/${s.codigo_ibge}`}>Ver o panorama completo do município →</Link>
        <br />
        <Link href={`/ivm/${s.codigo_ibge}`}>Ver o Índice de Vulnerabilidade Municipal →</Link>
        <br />
        <Link href={`/pulso/${s.codigo_ibge}`}>Ver o Pulso Produtivo (emprego formal) →</Link>
      </p>
    </main>
  );
}
