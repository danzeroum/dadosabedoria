import Link from "next/link";
import { notFound } from "next/navigation";

import { IndicadorCard } from "../../../components/IndicadorCard";
import { buscarPanorama } from "../../../lib/api";
import type { IndicadorValor } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULO_DOMINIO: Record<string, string> = {
  trabalho: "Trabalho",
  credito: "Crédito",
  saude: "Saúde",
  financas: "Finanças",
  educacao: "Educação",
  compras: "Compras",
};

function agrupar(indicadores: IndicadorValor[]): [string, IndicadorValor[]][] {
  const grupos = new Map<string, IndicadorValor[]>();
  for (const i of indicadores) {
    const g = grupos.get(i.dominio) ?? [];
    g.push(i);
    grupos.set(i.dominio, g);
  }
  return [...grupos.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

export default async function MunicipioPage({ params }: { params: { codigo: string } }) {
  const p = await buscarPanorama(params.codigo);
  if (!p) {
    notFound();
  }
  const grupos = agrupar(p.indicadores);
  const temEmprego = p.indicadores.some((i) => i.dominio === "trabalho");

  return (
    <main className="pagina">
      <Link href="/ivm" className="voltar">
        ← Voltar ao mapa
      </Link>
      <p className="pulso-pergunta">Panorama do município</p>
      <h1>
        {p.nome}
        {p.uf ? ` · ${p.uf}` : ""}
      </h1>
      <p className="home-lead">
        O que sabemos sobre este município: o último valor de cada indicador público do acervo, com a
        fonte. O que é protegido por privacidade aparece como protegido — nunca o número por baixo.
      </p>

      {temEmprego ? (
        <p className="ver-produto">
          <Link href={`/pulso/${p.codigo_ibge}`}>
            Ver o Pulso Produtivo (emprego formal mês a mês) →
          </Link>
        </p>
      ) : null}

      {grupos.length === 0 ? (
        <p className="vazio">Sem indicadores para este território ainda.</p>
      ) : (
        grupos.map(([dominio, indicadores]) => (
          <section key={dominio}>
            <h2>{ROTULO_DOMINIO[dominio] ?? dominio}</h2>
            <div className="indicador-grid">
              {indicadores.map((ind) => (
                <IndicadorCard key={ind.codigo} ind={ind} />
              ))}
            </div>
          </section>
        ))
      )}

      <p className="metodologia">
        Cada número traz seu período e sua fonte; a metodologia completa fica no indicador. Valores
        mais recentes disponíveis no acervo — a periodicidade varia por fonte.
      </p>
    </main>
  );
}
