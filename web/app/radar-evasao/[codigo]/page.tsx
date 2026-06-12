import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarRadarEvasao } from "../../../lib/api";
import type { NivelEvasao } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelEvasao, string> = {
  adequada: "Cobertura adequada (≥ 90 %)",
  atencao: "Atenção (75–89 %)",
  alerta: "Alerta — baixa cobertura (< 75 %)",
  sem_dado: "Sem dados",
};
const CORES_NIVEL: Record<NivelEvasao, string> = {
  adequada: "#15803d",
  atencao: "#b45309",
  alerta: "#b91c1c",
  sem_dado: "#6b7280",
};

export default async function RadarEvasaoPage({ params }: { params: { codigo: string } }) {
  const r = await buscarRadarEvasao(params.codigo);
  if (!r) {
    notFound();
  }

  const taxaFormatada =
    r.taxa_cobertura != null
      ? r.taxa_cobertura.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " %"
      : null;

  return (
    <main className="pagina">
      <Link href={`/bussola-edu-trabalho/${r.codigo_ibge}`} className="voltar">
        ← Ver a Bússola Educação-Trabalho
      </Link>
      <p className="pulso-pergunta">
        Radar de Evasão Escolar — cobertura do ensino fundamental municipal
      </p>
      <h1>
        {r.nome}
        {r.uf ? ` · ${r.uf}` : ""}
      </h1>
      {r.populacao != null && (
        <p className="giro-populacao">
          {r.populacao.toLocaleString("pt-BR")} hab · população estimada IBGE
          {r.populacao_escolar_estimada != null && (
            <> · {r.populacao_escolar_estimada.toLocaleString("pt-BR")} em idade escolar (14 %)</>
          )}
        </p>
      )}

      <div className="giro-painel">
        {/* Bloco principal — taxa de cobertura */}
        <div className="giro-bloco">
          <p className="giro-label">
            Taxa de cobertura do ensino fundamental{r.periodo ? ` · ${r.periodo}` : ""}
          </p>
          {taxaFormatada != null ? (
            <>
              <p className="giro-numero">
                <strong>{taxaFormatada}</strong>
                <span className="giro-rotulo-numero">de cobertura estimada</span>
              </p>
              {r.taxa_cobertura != null && r.taxa_cobertura > 100 && (
                <p style={{ fontSize: "0.82rem", color: "#1d4ed8", marginTop: "6px" }}>
                  Acima de 100 %: o município recebe alunos de cidades vizinhas — polo de atração escolar.
                </p>
              )}
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
          <p
            className="giro-nivel"
            style={{ color: CORES_NIVEL[r.nivel] }}
            aria-label={`Nível: ${ROTULOS_NIVEL[r.nivel]}`}
          >
            ● <span>{ROTULOS_NIVEL[r.nivel]}</span>
          </p>
        </div>

        {/* Bloco de matrículas */}
        <div className="giro-bloco">
          <p className="giro-label">Matrículas no ensino fundamental (INEP/Censo Escolar)</p>
          {r.matriculas != null ? (
            <>
              <p className="giro-numero">
                <strong>{r.matriculas.toLocaleString("pt-BR")}</strong>
                <span className="giro-rotulo-numero">alunos matriculados</span>
              </p>
              {r.matriculas_por_mil != null && (
                <p className="giro-per-capita">
                  {r.matriculas_por_mil.toLocaleString("pt-BR", { minimumFractionDigits: 1 })} por 1.000 hab
                </p>
              )}
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
          <p style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "8px" }}>
            Cobre matrículas do EF em escolas municipais, estaduais e privadas.
            Não inclui EJA, creche nem pré-escola.
          </p>
        </div>
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{r.nota}</p>
      </section>

      {r.meta && (
        <dl className="giro-meta">
          <div>
            <dt>Fonte</dt>
            <dd>
              {r.meta.fonte} · {r.meta.metodologia}
              {r.meta.lag_tipico_dias != null ? ` · atraso ~${r.meta.lag_tipico_dias} dias` : ""}{" "}
              · {r.meta.licenca}
            </dd>
          </div>
        </dl>
      )}

      <p style={{ marginTop: "16px" }}>
        <Link href={`/bussola-edu-trabalho/${r.codigo_ibge}`}>
          Ver a Bússola Educação-Trabalho (EDU-01) →
        </Link>
        <br />
        <Link href={`/municipio/${r.codigo_ibge}`}>Ver o panorama completo do município →</Link>
        <br />
        <Link href={`/ivm/${r.codigo_ibge}`}>Ver o Índice de Vulnerabilidade Municipal →</Link>
      </p>
    </main>
  );
}
