import Link from "next/link";
import { notFound } from "next/navigation";

import { IndicadorCard } from "../../../components/IndicadorCard";
import { VoceSabia } from "../../../components/VoceSabia";
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
  saneamento: "Saneamento",
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
  const dominios = new Set(p.indicadores.map((i) => i.dominio));

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

      <nav aria-label="Produtos disponíveis" style={{ marginBottom: "16px" }}>
        <p style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "6px" }}>
          Produtos com dado para este município:
        </p>
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {dominios.has("trabalho") && (
            <>
              <li><Link href={`/pulso/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>Pulso Produtivo →</Link></li>
              <li><Link href={`/giro-local/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>Giro Local →</Link></li>
              <li><Link href={`/salario-radar/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>Salário Radar →</Link></li>
            </>
          )}
          {dominios.has("financas") && (
            <li><Link href={`/onde-foi/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>OndeFoi →</Link></li>
          )}
          {dominios.has("educacao") && (
            <>
              <li><Link href={`/bussola-edu-trabalho/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>Bússola Edu-Trabalho →</Link></li>
              <li><Link href={`/radar-evasao/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>Radar de Evasão →</Link></li>
            </>
          )}
          {dominios.has("saude") && (
            <li><Link href={`/sentinela-resp/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>Sentinela Respiratória →</Link></li>
          )}
          {dominios.has("compras") && (
            <li><Link href={`/obra-viva/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>ObraViva →</Link></li>
          )}
          {dominios.has("saneamento") && (
            <>
              <li><Link href={`/agua-viva/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>AguaViva →</Link></li>
              <li><Link href={`/esgoto-invisivel/${p.codigo_ibge}`} className="home-cta" style={{ fontSize: "0.85rem" }}>EsgotoInvisível →</Link></li>
            </>
          )}
        </ul>
      </nav>

      <VoceSabia codigoIbge={p.codigo_ibge} />

      {grupos.length === 0 ? (
        <p className="vazio">Sem indicadores para este território ainda.</p>
      ) : (
        grupos.map(([dominio, indicadores]) => (
          <section key={dominio}>
            <h2>{ROTULO_DOMINIO[dominio] ?? dominio}</h2>
            <div className="indicador-grid">
              {indicadores.map((ind) => (
                <IndicadorCard key={ind.codigo} ind={ind} codigoIbge={p.codigo_ibge} />
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
