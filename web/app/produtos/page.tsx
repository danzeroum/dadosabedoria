import type { Metadata } from "next";
import Link from "next/link";

import { buscarFontes } from "../../lib/api";
import { DOMINIOS, produtosDoDominio } from "../../lib/catalogo";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Produtos · DadoSabedoria",
  description:
    "O acervo por pergunta: 28 produtos temáticos e 4 telas de síntese, agrupados por domínio, com a fonte de cada número.",
};

// Resumo honesto do acervo (vivo), pelo próprio /v1/fontes. Degrada em silêncio: se a API não
// responder, o catálogo segue inteiro, só sem o resumo.
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

export default async function ProdutosPage() {
  const acervo = await acervoResumo();
  return (
    <main className="pagina">
      <section className="home-hero">
        <h1>O acervo, por pergunta</h1>
        <p className="home-lead">
          Cada produto é uma <strong>pergunta</strong> sobre o seu município, respondida com a fonte
          ao lado. 28 produtos temáticos e 4 telas de síntese — o que é protegido aparece como
          protegido.
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

      {DOMINIOS.map((d) => {
        const produtos = produtosDoDominio(d.id);
        const unidade = d.id === "sintese" ? "telas" : "produtos";
        return (
          <div key={d.id}>
            <div className="cat-dominio">
              <h2>
                {d.titulo}{" "}
                <span className="cat-dominio-conta">
                  {produtos.length} {unidade}
                </span>
              </h2>
              <p className="cat-dominio-desc">{d.descricao}</p>
            </div>
            <section className="home-produtos" aria-label={d.titulo}>
              {produtos.map((p) => (
                <Link key={p.href} href={p.href} className="home-card">
                  <div className="home-card-topo">
                    <h3>{p.titulo}</h3>
                  </div>
                  <p className="home-pergunta">{p.pergunta}</p>
                  <p className="home-descricao">{p.descricao}</p>
                  <p className="home-fonte">{p.fonte}</p>
                  <span className="home-cta">{p.cta} →</span>
                </Link>
              ))}
            </section>
          </div>
        );
      })}

      <p className="home-nota">
        Dados abertos (IBGE · Novo CAGED · BCB/ESTBAN · DATASUS/SIH · SICONFI/STN · INEP · PNCP ·
        SNIS/MDR · ANA · ANEEL). Cada tela traz sua metodologia e a fonte. Onde a fonte ainda não foi
        ingerida, o produto avisa que está em demonstração — o dado real flui pela esteira.{" "}
        <Link href="/metodologia">Como tudo é calculado e protegido →</Link>
      </p>
    </main>
  );
}
