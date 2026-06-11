import Link from "next/link";

import { buscarTerritorios, perguntarIA } from "../../lib/api";
import type { RespostaIA, TerritorioSimples } from "../../lib/types";

export const dynamic = "force-dynamic";

// Exemplos navegáveis (sem JS no cliente): cada link faz uma pergunta. O 3º usa palavra do dia a
// dia ("alunos/escolas") SEM informar o indicador — a IA acha pelo sinônimo. O 4º é fora do acervo
// → mostra a IA se ABSTENDO (não inventa). A IA só afirma o que recupera, sempre com citação.
const EXEMPLOS: { q: string; indicador?: string; territorio?: string }[] = [
  {
    q: "Como está o emprego formal em São Paulo?",
    indicador: "trabalho.emprego.saldo_caged",
    territorio: "3550308",
  },
  {
    q: "E as internações respiratórias em São Paulo?",
    indicador: "saude.resp.internacoes_j",
    territorio: "3550308",
  },
  { q: "Quantos alunos nas escolas de São Paulo?", territorio: "3550308" },
  { q: "Qual será a cotação do dólar amanhã?" },
];

function linkExemplo(e: { q: string; indicador?: string; territorio?: string }): string {
  const p = new URLSearchParams({ q: e.q });
  if (e.indicador) p.set("indicador", e.indicador);
  if (e.territorio) p.set("territorio", e.territorio);
  return `/perguntar?${p.toString()}`;
}

function Resposta({ r }: { r: RespostaIA }) {
  return (
    <div className={`ia-resposta ${r.abstencao ? "ia-abstencao" : ""}`}>
      <div className="ia-topo">
        <span className="ia-badge">narrador: {r.narrador}</span>
        {r.abstencao ? <span className="ia-badge ia-badge-aviso">abstenção</span> : null}
        {r.revisao_humana ? (
          <span className="ia-badge ia-badge-aviso">revisão humana recomendada</span>
        ) : null}
      </div>
      <p className="ia-texto">{r.resposta}</p>

      {r.citacoes.length > 0 ? (
        <div className="ia-citacoes">
          <h3>Fontes citadas</h3>
          {r.citacoes.map((c) => (
            <div key={c.indicador} className="ia-citacao">
              <strong>{c.nome}</strong> · {c.fonte}
              {c.periodo_de ? ` · ${c.periodo_de}–${c.periodo_ate}` : ""}
              {c.lag_tipico_dias != null ? ` · atraso ~${c.lag_tipico_dias} dias` : ""}
              <span className="ia-metodologia">{c.metodologia}</span>
            </div>
          ))}
        </div>
      ) : null}

      {r.ressalvas.length > 0 ? (
        <ul className="ia-ressalvas">
          {r.ressalvas.map((rv) => (
            <li key={rv}>{rv}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function nomeTerritorioDisplay(t: TerritorioSimples): string {
  return t.uf ? `${t.nome} (${t.uf})` : t.nome;
}

export default async function PerguntarPage({
  searchParams,
}: {
  searchParams: { q?: string; indicador?: string; territorio?: string; bt?: string };
}) {
  const { q, indicador, territorio, bt } = searchParams;

  // Resolve nome legível quando território já está selecionado.
  let territorioNome: string | null = null;
  if (territorio) {
    const r = await buscarTerritorios(territorio);
    const t = r.dados[0];
    if (t) territorioNome = nomeTerritorioDisplay(t);
  }

  // Resultados da busca de território quando o usuário pesquisou por nome.
  const resultadosBusca = bt ? await buscarTerritorios(bt) : null;

  const resposta = q ? await perguntarIA({ pergunta: q, indicador, territorio }) : null;

  // URL base sem território (para "trocar" e limpar busca).
  const paramsBase = new URLSearchParams();
  if (q) paramsBase.set("q", q);
  if (indicador) paramsBase.set("indicador", indicador);
  const urlBase = `/perguntar?${paramsBase.toString()}`;

  return (
    <main className="pagina">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <p className="pulso-pergunta">IA ancorada</p>
      <h1>Pergunte aos dados</h1>
      <p className="home-lead">
        A IA só afirma o que <strong>recupera</strong> do repositório, sempre com{" "}
        <strong>citação</strong> da fonte. Sem dado, ela <strong>se abstém</strong> — não inventa
        número nem causalidade. Sem chave de LLM, narra em modo <strong>template</strong> (degradação
        graciosa); o que não muda é a ancoragem.
      </p>

      <section>
        <h2>Sua pergunta</h2>
        <form method="get" action="/perguntar" className="ia-form">
          {/* Preserva território quando já selecionado */}
          {territorio && <input type="hidden" name="territorio" value={territorio} />}
          <div className="ia-form-campo">
            <label htmlFor="q">Pergunte sobre os dados públicos</label>
            <input
              id="q"
              name="q"
              type="text"
              required
              defaultValue={q ?? ""}
              placeholder="ex.: como está o emprego em São Paulo?"
            />
          </div>
          <button type="submit">Perguntar</button>
        </form>
        <p className="ia-form-nota">
          Não precisa escolher o indicador — a IA tenta achar o mais relevante pela sua pergunta.
          Inclua o nome do município na pergunta (ex.: &ldquo;em Salvador&rdquo;) ou use o campo
          abaixo para filtrar por município.
        </p>
      </section>

      <section>
        <h2>
          Município <span className="ia-opcional">(opcional)</span>
        </h2>

        {territorio && territorioNome ? (
          // Território selecionado — mostra nome e link para trocar.
          <p className="picker-ativo-nome">
            {territorioNome}
            <Link href={urlBase} className="picker-trocar-link">
              trocar
            </Link>
          </p>
        ) : (
          // Formulário de busca por nome.
          <form method="get" action="/perguntar" className="picker-busca-form">
            {q && <input type="hidden" name="q" value={q} />}
            {indicador && <input type="hidden" name="indicador" value={indicador} />}
            <label htmlFor="bt-q">Buscar município</label>
            <input
              id="bt-q"
              name="bt"
              type="search"
              defaultValue={bt ?? ""}
              placeholder="ex.: Salvador, Campinas…"
            />
            <button type="submit">Buscar</button>
            {bt && (
              <Link href={urlBase} className="uf-limpar">
                limpar
              </Link>
            )}
          </form>
        )}

        {resultadosBusca !== null &&
          (resultadosBusca.dados.length === 0 ? (
            <p className="vazio">Nenhum município encontrado para &ldquo;{bt}&rdquo;.</p>
          ) : (
            <ul className="busca-resultados">
              {resultadosBusca.dados.map((t) => {
                const nome = nomeTerritorioDisplay(t);
                const p = new URLSearchParams();
                if (q) p.set("q", q);
                if (indicador) p.set("indicador", indicador);
                p.set("territorio", t.codigo_ibge);
                return (
                  <li key={t.codigo_ibge}>
                    <Link href={`/perguntar?${p.toString()}`}>
                      {nome}{" "}
                      <span className="busca-codigo tnum">{t.codigo_ibge}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          ))}

        {!territorio && !bt && (
          <p className="ia-form-nota">
            A IA resolve o município automaticamente quando você o menciona na pergunta. Use este
            campo apenas para ser mais preciso ou quando a pergunta for ambígua.
          </p>
        )}
      </section>

      <section>
        <h2>Exemplos</h2>
        <ul className="ia-exemplos">
          {EXEMPLOS.map((e) => (
            <li key={e.q}>
              <Link href={linkExemplo(e)}>{e.q}</Link>
            </li>
          ))}
        </ul>
      </section>

      {resposta ? (
        <section>
          <h2>&ldquo;{q}&rdquo;</h2>
          <Resposta r={resposta} />
        </section>
      ) : null}
    </main>
  );
}
