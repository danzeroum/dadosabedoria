import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarFomeOculta } from "../../../lib/api";
import type { NivelFomeOculta } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarFomeOculta(params.codigo);
  if (!data) return { title: "Fome Oculta · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Fome Oculta — ${local} · DadoSabedoria`,
    description: `Insegurança nutricional de crianças < 5 anos em ${local}: SISVAN/MS.`,
  };
}

const ROTULOS_NIVEL: Record<NivelFomeOculta, string> = {
  "crítico": "Crítico",
  elevado: "Elevado",
  moderado: "Moderado",
  baixo: "Baixo",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelFomeOculta, string> = {
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

export default async function FomeOcultaPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarFomeOculta(params.codigo);
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
        <h1>Fome Oculta</h1>
        <p className="produto-subtitulo">
          Insegurança nutricional de crianças &lt; 5 anos — SISVAN/Ministério da Saúde
        </p>
        {data.ano && <p className="produto-periodo">Exercício: {data.ano}</p>}
      </header>

      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte SISVAN está configurada; o dado real
        flui após a ingestão com <code>run_sisvan</code> no ambiente com rede aberta.
      </div>

      <section className="produto-secao" aria-label="Nível de insegurança nutricional">
        <div
          className="nivel-destaque"
          style={{ borderLeftColor: cor }}
          role="img"
          aria-label={`Nível: ${rotulo}`}
        >
          <p className="nivel-rotulo" style={{ color: cor }}>
            <strong>{rotulo}</strong>
          </p>
          {data.baixo_peso_pct !== null ? (
            <p className="nivel-detalhe">
              {formatarPct(data.baixo_peso_pct)} de crianças com baixo peso
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">Sem dado disponível para este município.</p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Indicadores nutricionais">
        <h2>Indicadores</h2>
        <table
          className="produto-tabela"
          aria-label="Insegurança nutricional municipal"
        >
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Prevalência de baixo peso (crianças &lt; 5 anos)</td>
              <td>{formatarPct(data.baixo_peso_pct)}</td>
            </tr>
            {data.n_acompanhadas !== null && (
              <tr>
                <td>Crianças acompanhadas pelo SISVAN</td>
                <td>{data.n_acompanhadas.toLocaleString("pt-BR")}</td>
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
        <h2>Escala de Referência (Limiares Provisórios — ALIM-02)</h2>
        <table
          className="produto-tabela"
          aria-label="Escala de classificação de insegurança nutricional"
        >
          <thead>
            <tr>
              <th scope="col">Nível</th>
              <th scope="col">Critério (% crianças &lt; 5 com baixo peso)</th>
              <th scope="col">Contexto</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Crítico</td>
              <td>≥ 10%</td>
              <td>Insegurança nutricional grave — atenção prioritária</td>
            </tr>
            <tr>
              <td>Elevado</td>
              <td>5% – 9,9%</td>
              <td>Taxa acima da média nacional — monitoramento reforçado</td>
            </tr>
            <tr>
              <td>Moderado</td>
              <td>2% – 4,9%</td>
              <td>Dentro do intervalo esperado para o país</td>
            </tr>
            <tr>
              <td>Baixo</td>
              <td>&lt; 2%</td>
              <td>Taxa abaixo da média — boa cobertura nutricional</td>
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
