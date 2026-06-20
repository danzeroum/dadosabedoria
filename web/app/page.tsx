import type { Metadata } from "next";
import Link from "next/link";

import { Onboarding } from "../components/Onboarding";
import { buscarFontes } from "../lib/api";
import { DESTAQUES } from "../lib/catalogo";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "DadoSabedoria — produtos",
  description: "Produtos de inteligência sobre dados públicos brasileiros, com proveniência.",
};

// Resumo honesto do acervo (vivo), pelo próprio /v1/fontes. Degrada em silêncio: se a API não
// responder (ex.: build sem backend), a porta de entrada segue inteira, só sem o resumo.
async function acervoResumo(): Promise<{
  fontes: number;
  indicadores: number;
  dominios: number;
} | null> {
  try {
    const r = await buscarFontes();
    if (!r) return null;
    return {
      fontes: r.total,
      indicadores: r.dados.reduce((s, f) => s + f.n_indicadores, 0),
      dominios: new Set(r.dados.flatMap((f) => f.dominios)).size,
    };
  } catch {
    return null;
  }
}

export default async function Home() {
  const acervo = await acervoResumo();
  return (
    <main className="pagina home">
      <Onboarding />
      <section className="home-hero">
        <h1>Inteligência de dados públicos brasileiros</h1>
        <p className="home-lead">
          A confiança é o ativo: <strong>privacidade estrutural</strong>,{" "}
          <strong>proveniência</strong> em cada número e <strong>qualidade provada</strong> a cada
          commit. Sem chave de pessoa; o que é protegido aparece como protegido.
        </p>
        {acervo ? (
          <Link href="/fontes" className="home-acervo">
            <strong>{acervo.fontes}</strong> fontes públicas ·{" "}
            <strong>{acervo.indicadores}</strong> indicadores ·{" "}
            <strong>{acervo.dominios}</strong> domínios — com proveniência e supressão honesta em
            cada número →
          </Link>
        ) : null}
      </section>

      <section className="home-produtos" aria-label="Produtos em destaque">
        {DESTAQUES.map((p) => (
          <Link key={p.href} href={p.href} className="home-card">
            <div className="home-card-topo">
              <h2>{p.titulo}</h2>
            </div>
            <p className="home-pergunta">{p.pergunta}</p>
            <p className="home-descricao">{p.descricao}</p>
            <span className="home-cta">{p.cta} →</span>
          </Link>
        ))}
      </section>

      <p className="home-nota">
        <Link href="/produtos">
          <strong>Ver todos os 28 produtos, por domínio →</strong>
        </Link>
        <br />
        Conheça a missão e o Valor Triplo em <Link href="/sobre">Sobre</Link>, ou construa sobre o
        acervo com a <Link href="/desenvolvedores">API &amp; Desenvolvedores</Link>.
      </p>

      <p className="home-nota">
        Dados abertos (IBGE · Novo CAGED · BCB/ESTBAN · DATASUS/SIH · SICONFI/STN · INEP · PNCP ·
        SNIS/MDR). Cada tela traz sua metodologia e a fonte. O OndeFoi usa dados reais do SICONFI/STN
        (Anexo I-E, exercício 2024). <Link href="/fontes">De onde vêm os dados e como protegemos →</Link>
      </p>
    </main>
  );
}
