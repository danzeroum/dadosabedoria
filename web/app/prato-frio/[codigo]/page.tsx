import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarPratoFrio } from "../../../lib/api";
import type { NivelProducao } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: { codigo: string } }): Promise<Metadata> {
  const data = await buscarPratoFrio(params.codigo);
  if (!data) return { title: "Prato no Frio · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Prato no Frio — ${local} · DadoSabedoria`,
    description: `Produção agrícola per capita em ${local}: IBGE PAM.`,
  };
}

const ROTULOS_NIVEL: Record<NivelProducao, string> = {
  alta: "Alta",
  moderada: "Moderada",
  baixa: "Baixa",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelProducao, string> = {
  alta: "#16a34a",
  moderada: "#ca8a04",
  baixa: "#b45309",
  sem_dado: "#6b7280",
};

function formatarBRL(valor: number | null): string {
  if (valor === null) return "—";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
}

function formatarBRLHab(valor: number | null): string {
  if (valor === null) return "—";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default async function PratoFrioPage({ params }: { params: { codigo: string } }) {
  const data = await buscarPratoFrio(params.codigo);
  if (!data) notFound();

  const cor = CORES_NIVEL[data.nivel];
  const rotulo = ROTULOS_NIVEL[data.nivel];

  return (
    <main className="produto-page">
      <nav className="produto-nav">
        <Link href={`/municipio/${data.codigo_ibge}`}>← {data.nome}{data.uf ? ` (${data.uf})` : ""}</Link>
      </nav>

      <header className="produto-header">
        <h1>Prato no Frio</h1>
        <p className="produto-subtitulo">Produção agrícola municipal per capita — IBGE PAM</p>
        {data.periodo && (
          <p className="produto-periodo">Período: {data.periodo}</p>
        )}
      </header>

      {/* aviso de demonstração */}
      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte IBGE PAM está configurada;
        o dado real flui após a 1ª ingestão no ambiente com rede aberta.
      </div>

      <section className="produto-secao" aria-label="Nível de produção">
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
              {formatarBRLHab(data.valor_por_hab)}/hab/ano
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">Sem dado disponível para este município.</p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Produção agrícola">
        <h2>Indicadores</h2>
        <table className="produto-tabela" aria-label="Produção agrícola municipal">
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Valor total da produção (lavouras)</td>
              <td>{formatarBRL(data.valor_total)}</td>
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
        <h2>Escala de Referência (Limiares Provisórios — ALIM-01)</h2>
        <table className="produto-tabela" aria-label="Escala de classificação de produção agrícola">
          <thead>
            <tr>
              <th scope="col">Nível</th>
              <th scope="col">Critério (BRL/hab/ano)</th>
              <th scope="col">Contexto</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Alta</td><td>≥ R$ 5.000</td><td>Município com forte vocação agrícola</td></tr>
            <tr><td>Moderada</td><td>R$ 500 – R$ 4.999</td><td>Produção agrícola relevante</td></tr>
            <tr><td>Baixa</td><td>&lt; R$ 500</td><td>Produção reduzida ou predominantemente urbano</td></tr>
          </tbody>
        </table>
      </section>

      <section className="produto-secao produto-nota" aria-label="Nota metodológica">
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
