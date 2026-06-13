import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarPerfilOrcamentario } from "../../../lib/api";
import type { FuncaoPerfilItem } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { codigo: string };
}): Promise<Metadata> {
  const data = await buscarPerfilOrcamentario(params.codigo);
  if (!data) return { title: "Perfil Orçamentário · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Perfil Orçamentário — ${local} · DadoSabedoria`,
    description: `Investimento municipal por função orçamentária com percentil nacional — ${local}.`,
  };
}

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
    }) + "/hab"
  );
}

function corPercentil(percentil: number | null): string {
  if (percentil === null) return "#6b7280";
  if (percentil >= 75) return "#16a34a";
  if (percentil >= 50) return "#2563eb";
  if (percentil >= 25) return "#ca8a04";
  return "#b45309";
}

function BarraPercentil({ percentil }: { percentil: number | null }) {
  if (percentil === null) {
    return <span className="sr-only">sem dado</span>;
  }
  const cor = corPercentil(percentil);
  return (
    <div
      style={{ display: "flex", alignItems: "center", gap: "0.5rem", minWidth: "140px" }}
      role="img"
      aria-label={`Percentil ${percentil.toFixed(1)}%`}
    >
      <div
        style={{
          flexGrow: 1,
          height: "8px",
          background: "#e5e7eb",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(100, Math.max(0, percentil))}%`,
            height: "100%",
            background: cor,
            borderRadius: "4px",
          }}
        />
      </div>
      <span style={{ color: cor, fontWeight: 600, fontSize: "0.85rem", minWidth: "3.5rem" }}>
        {percentil.toFixed(1)}%
      </span>
    </div>
  );
}

function LinhaFuncao({ f }: { f: FuncaoPerfilItem }) {
  return (
    <tr>
      <td>
        <span
          style={{
            fontFamily: "monospace",
            background: "#f3f4f6",
            padding: "0.1rem 0.35rem",
            borderRadius: "3px",
            fontSize: "0.85rem",
          }}
        >
          {f.funcao_cod}
        </span>
      </td>
      <td>{f.funcao_nome}</td>
      <td style={{ textAlign: "right" }}>{formatarBRLHab(f.valor_por_hab)}</td>
      <td style={{ textAlign: "right" }}>{formatarBRL(f.valor_liquidado)}</td>
      <td>
        <BarraPercentil percentil={f.percentil} />
      </td>
    </tr>
  );
}

export default async function PerfilOrcamentarioPage({
  params,
}: {
  params: { codigo: string };
}) {
  const data = await buscarPerfilOrcamentario(params.codigo);
  if (!data) notFound();

  const funcoes = [...data.funcoes].sort((a, b) => {
    const pa = a.percentil ?? -1;
    const pb = b.percentil ?? -1;
    return pb - pa;
  });

  return (
    <main className="produto-page">
      <nav className="produto-nav">
        <Link href={`/municipio/${data.codigo_ibge}`}>
          ← {data.nome}
          {data.uf ? ` (${data.uf})` : ""}
        </Link>
      </nav>

      <header className="produto-header">
        <h1>Perfil Orçamentário</h1>
        <p className="produto-subtitulo">
          Investimento por função — SICONFI Anexo I-E (Portaria 42/1999)
        </p>
        {data.ano && <p className="produto-periodo">Exercício: {data.ano}</p>}
        {data.populacao && (
          <p className="produto-periodo">
            População: {data.populacao.toLocaleString("pt-BR")} hab
          </p>
        )}
      </header>

      <div className="demo-banner" role="note" aria-label="Aviso de demonstração">
        <strong>Dados de demonstração.</strong> A fonte SICONFI está configurada; o dado real
        flui após a ingestão com <code>run_siconfi_funcoes</code> no ambiente com rede aberta.
      </div>

      <section className="produto-secao" aria-label="Funções orçamentárias">
        <h2>Funções e Percentil Nacional</h2>
        <p style={{ fontSize: "0.9rem", color: "#6b7280", marginBottom: "1rem" }}>
          O percentil compara o município com todos os demais com dado no mesmo exercício.
          <br />
          <span style={{ color: "#16a34a", fontWeight: 600 }}>▌</span> ≥ 75%&nbsp;
          <span style={{ color: "#2563eb", fontWeight: 600 }}>▌</span> 50–74%&nbsp;
          <span style={{ color: "#ca8a04", fontWeight: 600 }}>▌</span> 25–49%&nbsp;
          <span style={{ color: "#b45309", fontWeight: 600 }}>▌</span> &lt; 25%
        </p>
        <table className="produto-tabela" aria-label="Perfil orçamentário por função">
          <thead>
            <tr>
              <th scope="col">Cod.</th>
              <th scope="col">Função</th>
              <th scope="col">R$/hab/ano</th>
              <th scope="col">Total liquidado</th>
              <th scope="col">Percentil nacional</th>
            </tr>
          </thead>
          <tbody>
            {funcoes.map((f) => (
              <LinhaFuncao key={f.funcao_cod} f={f} />
            ))}
          </tbody>
        </table>
      </section>

      <section
        className="produto-secao produto-nota"
        aria-label="Nota metodológica"
      >
        <h2>Nota</h2>
        <p>{data.nota}</p>
      </section>
    </main>
  );
}
