import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarAssisViva } from "../../../lib/api";
import type { NivelAssistencia } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarAssisViva(params.codigo);
  if (!data) return { title: "AssisViva · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `AssisViva — ${local} · DadoSabedoria`,
    description: `Investimento público em assistência social em ${local}: SICONFI Função 08.`,
  };
}

const ROTULOS_NIVEL: Record<NivelAssistencia, string> = {
  expressivo: "Expressivo",
  moderado: "Moderado",
  incipiente: "Incipiente",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelAssistencia, string> = {
  expressivo: "#16a34a",
  moderado: "#ca8a04",
  incipiente: "#b45309",
  sem_dado: "#6b7280",
};

function formatarBRL(valor: number | null): string {
  if (valor === null) return "—";
  return valor.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  });
}

function formatarBRLHab(valor: number | null): string {
  if (valor === null) return "—";
  return (
    valor.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }) + "/hab/ano"
  );
}

export default async function AssisVivaPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarAssisViva(params.codigo);
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
        <h1>AssisViva</h1>
        <p className="produto-subtitulo">
          Investimento público municipal em assistência social — SICONFI Função 08
        </p>
        {data.ano && <p className="produto-periodo">Exercício: {data.ano}</p>}
      </header>

      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte SICONFI está configurada; o dado real
        flui após a ingestão com <code>run_siconfi_funcoes</code> no ambiente com rede aberta.
      </div>

      <section className="produto-secao" aria-label="Nível de investimento">
        <div
          className="nivel-destaque"
          style={{ borderLeftColor: cor }}
          role="img"
          aria-label={`Nível: ${rotulo}`}
        >
          <p className="nivel-rotulo" style={{ color: cor }}>
            <strong>{rotulo}</strong>
          </p>
          {data.valor_por_hab !== null ? (
            <p className="nivel-detalhe">
              {formatarBRLHab(data.valor_por_hab)}
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">Sem dado disponível para este município.</p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Indicadores de investimento">
        <h2>Indicadores</h2>
        <table
          className="produto-tabela"
          aria-label="Investimento municipal em assistência social"
        >
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Despesa liquidada — Função 08 (Assistência Social)</td>
              <td>{formatarBRL(data.valor_liquidado)}</td>
            </tr>
            <tr>
              <td>Valor por habitante</td>
              <td>{formatarBRLHab(data.valor_por_hab)}</td>
            </tr>
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
        <h2>Escala de Referência (Limiares Provisórios — SOCIAL-01)</h2>
        <table
          className="produto-tabela"
          aria-label="Escala de classificação do investimento em assistência social"
        >
          <thead>
            <tr>
              <th scope="col">Nível</th>
              <th scope="col">Critério (BRL/hab/ano)</th>
              <th scope="col">Contexto</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Expressivo</td>
              <td>≥ R$ 150</td>
              <td>Município com rede SUAS robusta e benefícios municipais ativos</td>
            </tr>
            <tr>
              <td>Moderado</td>
              <td>R$ 50 – R$ 149</td>
              <td>Esforço orçamentário compatível com o padrão médio</td>
            </tr>
            <tr>
              <td>Incipiente</td>
              <td>&lt; R$ 50 ou zero</td>
              <td>Baixo investimento direto — verificar cobertura estadual/federal</td>
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
