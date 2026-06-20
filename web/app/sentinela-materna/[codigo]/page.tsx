import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarSentinelaMaterna } from "../../../lib/api";
import type { NivelMaterno } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarSentinelaMaterna(params.codigo);
  if (!data) return { title: "Sentinela Materna · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Sentinela Materna — ${local} · DadoSabedoria`,
    description: `Risco nutricional de gestantes em ${local}: SISVAN/MS.`,
  };
}

const ROTULOS_NIVEL: Record<NivelMaterno, string> = {
  "crítico": "Crítico",
  elevado: "Elevado",
  moderado: "Moderado",
  baixo: "Baixo",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelMaterno, string> = {
  "crítico": "#dc2626",
  elevado: "#b45309",
  moderado: "#ca8a04",
  baixo: "#16a34a",
  sem_dado: "#6b7280",
};

function formatarPct(valor: number | null): string {
  if (valor === null) return "—";
  return (
    valor.toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + "%"
  );
}

export default async function SentinelaMaternaPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarSentinelaMaterna(params.codigo);
  if (!data) notFound();

  const cor = CORES_NIVEL[data.nivel];
  const rotulo = ROTULOS_NIVEL[data.nivel];

  return (
    <main className="produto-page">
      <nav className="produto-nav">
        <Link href={`/municipio/${data.codigo_ibge}`}>
          ← {data.nome}
          {data.uf ? ` (${data.uf})` : ""}
        </Link>
      </nav>

      <header className="produto-header">
        <h1>Sentinela Materna</h1>
        <p className="produto-subtitulo">
          Risco nutricional de gestantes — SISVAN/Ministério da Saúde
        </p>
        {data.ano && <p className="produto-periodo">Exercício: {data.ano}</p>}
      </header>

      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte SISVAN gestante está configurada; o dado
        real flui após a ingestão com <code>run_sisvan_gestante</code> no ambiente com rede aberta.
      </div>

      <p className="produto-privacidade" role="note" aria-label="Aviso de privacidade">
        Este indicador não identifica gestantes. Dado agregado por município.
      </p>

      <section className="produto-secao" aria-label="Nível de risco nutricional materno">
        <div
          className="nivel-destaque"
          style={{ borderLeftColor: cor }}
          role="img"
          aria-label={`Nível: ${rotulo}`}
        >
          <p className="nivel-rotulo" style={{ color: cor }}>
            <strong>{rotulo}</strong>
          </p>
          {data.gestante_baixo_peso_pct !== null ? (
            <p className="nivel-detalhe">
              {formatarPct(data.gestante_baixo_peso_pct)} de gestantes com baixo peso
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">Sem dado disponível para este município.</p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Indicadores de saúde materna">
        <h2>Indicadores</h2>
        <table
          className="produto-tabela"
          aria-label="Saúde nutricional de gestantes"
        >
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Gestantes com baixo peso (SISVAN)</td>
              <td>{formatarPct(data.gestante_baixo_peso_pct)}</td>
            </tr>
            {data.n_gestantes !== null && (
              <tr>
                <td>Gestantes monitoradas pelo SISVAN</td>
                <td>{data.n_gestantes.toLocaleString("pt-BR")}</td>
              </tr>
            )}
            {data.populacao !== null && (
              <tr>
                <td>População</td>
                <td>{data.populacao.toLocaleString("pt-BR")}</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="produto-secao" aria-label="Escala de referência">
        <h2>Escala de Referência (Limiares Provisórios — SAUDE-03)</h2>
        <table
          className="produto-tabela"
          aria-label="Escala de classificação de risco nutricional materno"
        >
          <thead>
            <tr>
              <th scope="col">Nível</th>
              <th scope="col">Critério (% gestantes com baixo peso)</th>
              <th scope="col">Contexto</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Crítico</td>
              <td>≥ 30%</td>
              <td>Risco nutricional materno grave — atenção prioritária</td>
            </tr>
            <tr>
              <td>Elevado</td>
              <td>20% – 29,9%</td>
              <td>Acima da média esperada — monitoramento reforçado</td>
            </tr>
            <tr>
              <td>Moderado</td>
              <td>10% – 19,9%</td>
              <td>Dentro do intervalo de atenção</td>
            </tr>
            <tr>
              <td>Baixo</td>
              <td>&lt; 10%</td>
              <td>Taxa abaixo dos limiares de alerta</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        className="produto-secao produto-nota"
        aria-label="Nota metodológica"
      >
        <h2>Nota</h2>
        <p>{data.nota}</p>
        {data.meta && (
          <p className="produto-meta">
            Fonte: {data.meta.nome} · Lag típico: ~{data.meta.lag_tipico_dias} dias
          </p>
        )}
      </section>
    </main>
  );
}
