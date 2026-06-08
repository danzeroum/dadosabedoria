import Link from "next/link";

import { buscarFontes } from "../../lib/api";
import type { FonteAcervo } from "../../lib/types";

export const dynamic = "force-dynamic";

const ROTULO_DOMINIO: Record<string, string> = {
  trabalho: "Trabalho",
  credito: "Crédito",
  saude: "Saúde",
  financas: "Finanças",
  educacao: "Educação",
  compras: "Compras",
};

const ROTULO_CADENCIA: Record<string, string> = {
  diaria: "atualização diária",
  semanal: "atualização semanal",
  mensal: "atualização mensal",
  trimestral: "atualização trimestral",
  anual: "atualização anual",
  irregular: "atualização irregular",
};

function FonteCard({ f }: { f: FonteAcervo }) {
  return (
    <article className="fonte-card">
      <h3 className="fonte-nome">
        {f.nome} <span className="fonte-orgao">· {f.orgao}</span>
      </h3>
      <p className="fonte-cobertura">
        {f.dominios.length > 0 ? (
          <>
            Alimenta{" "}
            {f.dominios.map((d, i) => (
              <span key={d}>
                {i > 0 ? ", " : ""}
                <strong>{ROTULO_DOMINIO[d] ?? d}</strong>
              </span>
            ))}{" "}
            ({f.n_indicadores} {f.n_indicadores === 1 ? "indicador" : "indicadores"} no acervo)
          </>
        ) : (
          <span className="fonte-sem">Conectada, ainda sem indicador no acervo</span>
        )}
      </p>
      <ul className="fonte-meta">
        <li>{ROTULO_CADENCIA[f.atualizacao] ?? f.atualizacao}</li>
        {f.lag_tipico_dias != null ? <li>atraso típico ~{f.lag_tipico_dias} dias</li> : null}
        <li>licença: {f.licenca}</li>
        <li>{f.permite_uso_comercial ? "uso comercial permitido" : "uso comercial restrito"}</li>
        <li>{f.permite_redistribuicao ? "redistribuição permitida" : "redistribuição restrita"}</li>
      </ul>
      <p className="fonte-base">
        Base legal: <strong>{f.base_legal_artigo}</strong> — {f.base_legal_hipotese}
      </p>
      {f.url_doc ? (
        <p className="fonte-doc">
          <a href={f.url_doc} target="_blank" rel="noopener noreferrer">
            Documentação da fonte ↗
          </a>
        </p>
      ) : null}
    </article>
  );
}

export default async function FontesPage() {
  const resp = await buscarFontes();
  const fontes = resp?.dados ?? [];

  return (
    <main className="pagina">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Fontes &amp; confiança</h1>
      <p className="home-lead">
        Todo número aqui tem origem, licença e atraso declarados — a confiança não como promessa, mas
        como fato verificável. Estas são as fontes públicas por trás do acervo, lidas do próprio banco,
        com a base legal (LGPD) de cada uma.
      </p>

      {fontes.length === 0 ? (
        <p className="vazio">Não foi possível carregar as fontes agora. Tente novamente em instantes.</p>
      ) : (
        <section aria-label="Fontes do acervo">
          <h2>As fontes do acervo</h2>
          <div className="fonte-grid">
            {fontes.map((f) => (
              <FonteCard key={f.codigo} f={f} />
            ))}
          </div>
        </section>
      )}

      <section className="confianca">
        <h2>Como protegemos e como provamos</h2>
        <ul className="confianca-lista">
          <li>
            <strong>Privacidade por estrutura.</strong> O grão é sempre território × período — nunca
            pessoa. Células pequenas demais (origem sensível, como saúde) são <em>suprimidas antes de
            gravar</em>: a tela mostra um cadeado, jamais o número por baixo.
          </li>
          <li>
            <strong>Dado pessoal isolado.</strong> Contato de quem opta por alertas vive num schema
            à parte, que a camada analítica não consegue ler — garantido por um teste que reprova o
            build se a separação vazar.
          </li>
          <li>
            <strong>Proveniência sempre.</strong> Cada indicador carrega fonte, método e atraso; esta
            página é a vista consolidada disso — origem e licença auditáveis a cada consulta.
          </li>
          <li>
            <strong>IA ancorada.</strong> Quando há resposta em linguagem natural, ela só afirma o que
            o acervo sustenta e cita a fonte; sem dado, ela se abstém — não inventa número.
          </li>
        </ul>
      </section>

      <p className="metodologia">
        Cadência e atraso são típicos da fonte, não garantias de tempo real. &ldquo;Conectada, ainda
        sem indicador&rdquo; significa que a esteira existe e o indicador entra quando o dado real
        flui — honesto sobre o que já está no acervo e o que ainda não.
      </p>
    </main>
  );
}
