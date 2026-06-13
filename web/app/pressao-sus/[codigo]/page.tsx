import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarPressaoSus } from "../../../lib/api";
import type { NivelPressaoSus } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarPressaoSus(params.codigo);
  if (!data) return { title: "Pressão no SUS · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Pressão no SUS — ${local} · DadoSabedoria`,
    description: `Capacidade de financiamento do SUS em ${local}: despesa per capita na Função 10 (Saúde).`,
  };
}

const ROTULOS_NIVEL: Record<NivelPressaoSus, string> = {
  adequado: "Adequado",
  "atenção": "Atenção",
  "crítico": "Crítico",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelPressaoSus, string> = {
  adequado: "#16a34a",
  "atenção": "#ca8a04",
  "crítico": "#dc2626",
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

export default async function PressaoSusPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarPressaoSus(params.codigo);
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
        <h1>Pressão no SUS</h1>
        <p className="produto-subtitulo">
          Capacidade de financiamento do sistema público de saúde local — SICONFI Função 10
        </p>
        {data.ano && <p className="produto-periodo">Exercício: {data.ano}</p>}
      </header>

      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte SICONFI está configurada; o dado real
        flui após a ingestão com <code>run_siconfi_funcoes</code> no ambiente com rede aberta.
      </div>

      <section className="produto-secao" aria-label="Nível de pressão">
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
              {formatarBRLHab(data.valor_por_hab)} em saúde
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">Sem dado disponível para este município.</p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Indicadores">
        <h2>Indicadores</h2>
        <table
          className="produto-tabela"
          aria-label="Financiamento municipal do SUS"
        >
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Despesa liquidada — Função 10 (Saúde)</td>
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
        <h2>Escala de Referência (Limiares Provisórios — SAUDE-11)</h2>
        <table
          className="produto-tabela"
          aria-label="Escala de classificação da capacidade do SUS"
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
              <td>Adequado</td>
              <td>≥ R$ 500</td>
              <td>Financiamento razoável para APS, vigilância e medicamentos</td>
            </tr>
            <tr>
              <td>Atenção</td>
              <td>R$ 200 – R$ 499</td>
              <td>Capacidade limitada; sistema sob pressão moderada</td>
            </tr>
            <tr>
              <td>Crítico</td>
              <td>&lt; R$ 200</td>
              <td>Risco de descumprimento da Lei 141/2012 (mínimo 15% da receita)</td>
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
        <p className="produto-privacidade" role="note">
          <strong>Dado agregado por município.</strong> Este indicador não identifica
          profissionais de saúde individualmente — é uma medida de capacidade financeira
          do sistema (SAUDE-11, dupla face §17).
        </p>
        {data.meta && (
          <p className="produto-meta">
            Fonte: {data.meta.nome} · Lag típico: ~{data.meta.lag_tipico_dias} dias
          </p>
        )}
      </section>
    </main>
  );
}
