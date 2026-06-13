import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarCacadorArboviroses } from "../../../lib/api";
import type { NivelArboviroses } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarCacadorArboviroses(params.codigo);
  if (!data) return { title: "Caçador de Arboviroses · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Caçador de Arboviroses — ${local} · DadoSabedoria`,
    description: `Dengue confirmada por 100 mil habitantes em ${local}: SINAN/MS.`,
  };
}

const ROTULOS_NIVEL: Record<NivelArboviroses, string> = {
  "crítico": "Crítico — situação epidêmica",
  elevado: "Elevado — alto risco",
  moderado: "Moderado",
  baixo: "Baixo",
  sem_dado: "Sem dados disponíveis",
};

const CORES_NIVEL: Record<NivelArboviroses, string> = {
  "crítico": "#dc2626",
  elevado: "#ea580c",
  moderado: "#ca8a04",
  baixo: "#16a34a",
  sem_dado: "#6b7280",
};

function formatarIncidencia(valor: number | null): string {
  if (valor === null) return "—";
  return (
    valor.toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + " casos/100k hab."
  );
}

function formatarCasos(valor: number | null): string {
  if (valor === null) return "Suprimido (privacidade)";
  return valor.toLocaleString("pt-BR") + " casos";
}

export default async function CacadorArboviroesPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarCacadorArboviroses(params.codigo);
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
        <h1>Caçador de Arboviroses</h1>
        <p className="produto-subtitulo">
          Dengue confirmada por 100 mil habitantes — SINAN/Ministério da Saúde
        </p>
        {data.ano && <p className="produto-periodo">Ano de notificação: {data.ano}</p>}
      </header>

      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte SINAN/DATASUS está configurada; o
        dado real flui após a ingestão com <code>run_sinan</code> no ambiente com rede
        aberta (ftp.datasus.gov.br).
      </div>

      <section className="produto-secao" aria-label="Nível de risco de arboviroses">
        <div
          className="nivel-destaque"
          style={{ borderLeftColor: cor }}
          role="img"
          aria-label={`Nível: ${rotulo}`}
        >
          <p className="nivel-rotulo" style={{ color: cor }}>
            <strong>{rotulo}</strong>
          </p>
          {data.incidencia_100k !== null ? (
            <p className="nivel-detalhe">
              {formatarIncidencia(data.incidencia_100k)} de dengue confirmada
              <span className="sr-only"> — {rotulo}</span>
            </p>
          ) : (
            <p className="nivel-detalhe">
              {data.casos_confirmados === null
                ? "Dado suprimido por privacidade (k-anonimato, menos de 5 casos)."
                : "Sem incidência disponível para este município."}
            </p>
          )}
        </div>
      </section>

      <section className="produto-secao" aria-label="Indicadores de dengue">
        <h2>Indicadores</h2>
        <table
          className="produto-tabela"
          aria-label="Indicadores de dengue municipal"
        >
          <thead>
            <tr>
              <th scope="col">Indicador</th>
              <th scope="col">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Incidência de dengue (casos/100k hab.)</td>
              <td>{formatarIncidencia(data.incidencia_100k)}</td>
            </tr>
            <tr>
              <td>Casos confirmados (CLASSI_FIN 1-3)</td>
              <td>{formatarCasos(data.casos_confirmados)}</td>
            </tr>
            {data.populacao !== null && (
              <tr>
                <td>População (Censo 2022)</td>
                <td>{data.populacao.toLocaleString("pt-BR")}</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="produto-secao" aria-label="Escala de referência">
        <h2>Escala de Referência (Limiares MS/PAHO — SAUDE-02)</h2>
        <table
          className="produto-tabela"
          aria-label="Escala de classificação de incidência de dengue"
        >
          <thead>
            <tr>
              <th scope="col">Nível</th>
              <th scope="col">Critério (casos/100k hab.)</th>
              <th scope="col">Contexto</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ color: CORES_NIVEL["crítico"] }}>Crítico</td>
              <td>≥ 300</td>
              <td>Situação epidêmica — atenção prioritária</td>
            </tr>
            <tr>
              <td style={{ color: CORES_NIVEL.elevado }}>Elevado</td>
              <td>100 – 299</td>
              <td>Alto risco — monitoramento intensificado</td>
            </tr>
            <tr>
              <td style={{ color: CORES_NIVEL.moderado }}>Moderado</td>
              <td>20 – 99</td>
              <td>Circulação viral ativa — vigilância reforçada</td>
            </tr>
            <tr>
              <td style={{ color: CORES_NIVEL.baixo }}>Baixo</td>
              <td>&lt; 20</td>
              <td>Incidência baixa — manutenção das ações de prevenção</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        className="produto-secao produto-nota"
        aria-label="Nota metodológica e limitações"
      >
        <h2>Nota e Limitações</h2>
        <p>{data.nota}</p>
        <ul>
          <li>
            <strong>Subnotificação:</strong> estima-se que apenas 1 em 3 a 10 casos seja
            notificado ao SINAN. A incidência real pode ser significativamente maior.
          </li>
          <li>
            <strong>Privacidade (k-anonimato):</strong> municípios com menos de 5 casos
            confirmados têm o dado suprimido para proteger a privacidade dos pacientes.
          </li>
          <li>
            <strong>Lag:</strong> os dados do SINAN têm defasagem típica de 6 a 12 meses
            após o ano de notificação.
          </li>
          <li>
            <strong>Cobertura:</strong> cobre dengue clássico (1), com sinais de alarme (2)
            e grave (3). Chikungunya e Zika requerem arquivos separados do SINAN.
          </li>
        </ul>
        {data.meta && (
          <p className="produto-meta">
            Fonte: {data.meta.nome} · Lag típico: ~{data.meta.lag_tipico_dias} dias
          </p>
        )}
      </section>
    </main>
  );
}
