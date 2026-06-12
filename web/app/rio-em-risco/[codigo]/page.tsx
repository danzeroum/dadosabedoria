import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarRioEmRisco } from "../../../lib/api";
import type { NivelSeca } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: { codigo: string } }): Promise<Metadata> {
  const data = await buscarRioEmRisco(params.codigo);
  if (!data) return { title: "Rio em Risco · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Rio em Risco — ${local} · DadoSabedoria`,
    description: `Risco hídrico de seca em ${local}: índice do Monitor de Secas da ANA.`,
  };
}

const ROTULOS_NIVEL: Record<NivelSeca, string> = {
  normal: "Normal",
  atencao: "Atenção",
  critico: "Crítico",
  sem_dado: "Sem dados disponíveis",
};
const CORES_NIVEL: Record<NivelSeca, string> = {
  normal: "#16a34a",
  atencao: "#b45309",
  critico: "#dc2626",
  sem_dado: "#6b7280",
};

const CLASSES_SECA: Record<number, string> = {
  0: "Normal",
  1: "D0 — Anormalmente Seco",
  2: "D1 — Seco Moderado",
  3: "D2 — Seco Grave",
  4: "D3 — Seco Extremo",
  5: "D4 — Seco Excepcional",
};

function classeTexto(indice: number | null): string {
  if (indice === null) return "—";
  return CLASSES_SECA[Math.round(indice)] ?? `Índice ${indice.toFixed(1)}`;
}

export default async function RioEmRiscoPage({ params }: { params: { codigo: string } }) {
  const data = await buscarRioEmRisco(params.codigo);
  if (!data) notFound();

  const cor = CORES_NIVEL[data.nivel];
  const rotulo = ROTULOS_NIVEL[data.nivel];

  return (
    <main className="produto-page">
      <nav className="produto-nav">
        <Link href={`/municipio/${data.codigo_ibge}`}>← {data.nome}{data.uf ? ` (${data.uf})` : ""}</Link>
      </nav>

      <header className="produto-header">
        <h1>Rio em Risco</h1>
        <p className="produto-subtitulo">Risco hídrico de seca — ANA Monitor de Secas</p>
        {data.periodo && (
          <p className="produto-periodo">Período: {data.periodo}</p>
        )}
      </header>

      {/* aviso de demonstração */}
      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte ANA/Monitor de Secas está configurada;
        o dado real flui após a 1ª ingestão no ambiente com rede aberta.
      </div>

      <section className="produto-secao" aria-label="Nível de risco">
        <div
          className="nivel-destaque"
          style={{ borderLeftColor: cor }}
          role="img"
          aria-label={`Nível: ${rotulo}`}
        >
          <p className="nivel-rotulo" style={{ color: cor }}>
            <strong>{rotulo}</strong>
          </p>
          {data.seca_indice !== null ? (
            <p className="nivel-detalhe">
              {classeTexto(data.seca_indice)}
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">Sem dado disponível para este município.</p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Índice de seca">
        <h2>Índice de Seca</h2>
        <table className="produto-tabela" aria-label="Índice de seca e classe">
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
              <th scope="col">Classificação</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Índice de seca (pior mês do ano)</td>
              <td>{data.seca_indice !== null ? data.seca_indice.toFixed(1) : "—"}</td>
              <td>{classeTexto(data.seca_indice)}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="produto-secao" aria-label="Escala de referência">
        <h2>Escala de Referência (USDM adaptada pela ANA)</h2>
        <table className="produto-tabela" aria-label="Escala de classificação de seca">
          <thead>
            <tr>
              <th scope="col">Índice</th>
              <th scope="col">Classe</th>
              <th scope="col">Nível do produto</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>0</td><td>Normal</td><td>Normal</td></tr>
            <tr><td>1</td><td>D0 — Anormalmente Seco</td><td>Atenção</td></tr>
            <tr><td>2</td><td>D1 — Seco Moderado</td><td>Atenção</td></tr>
            <tr><td>3</td><td>D2 — Seco Grave</td><td>Crítico</td></tr>
            <tr><td>4</td><td>D3 — Seco Extremo</td><td>Crítico</td></tr>
            <tr><td>5</td><td>D4 — Seco Excepcional</td><td>Crítico</td></tr>
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
