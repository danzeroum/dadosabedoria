import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarViaViva } from "../../../lib/api";
import type { NivelTransporte } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarViaViva(params.codigo);
  if (!data) return { title: "ViaViva · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `ViaViva — ${local} · DadoSabedoria`,
    description: `Investimento público em transporte em ${local}: SICONFI Função 26.`,
  };
}

const ROTULOS_NIVEL: Record<NivelTransporte, string> = {
  elevado: "Elevado",
  moderado: "Moderado",
  baixo: "Baixo",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelTransporte, string> = {
  elevado: "#16a34a",
  moderado: "#ca8a04",
  baixo: "#b45309",
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

export default async function ViaVivaPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarViaViva(params.codigo);
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
        <h1>ViaViva</h1>
        <p className="produto-subtitulo">
          Investimento público municipal em transporte — SICONFI Função 26
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
          aria-label="Investimento municipal em transporte"
        >
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Despesa liquidada — Função 26 (Transporte)</td>
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
        <h2>Escala de Referência (Limiares Provisórios — MOB-01)</h2>
        <table
          className="produto-tabela"
          aria-label="Escala de classificação do investimento em transporte"
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
              <td>Elevado</td>
              <td>≥ R$ 300</td>
              <td>Município com programa de mobilidade urbana ativo</td>
            </tr>
            <tr>
              <td>Moderado</td>
              <td>R$ 80 – R$ 299</td>
              <td>Investimento significativo em estradas e transporte</td>
            </tr>
            <tr>
              <td>Baixo</td>
              <td>&lt; R$ 80 ou zero</td>
              <td>Investimento mínimo ou ausente na função 26</td>
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
