import Link from "next/link";

import { perguntarIA } from "../../lib/api";
import type { RespostaIA } from "../../lib/types";

export const dynamic = "force-dynamic";

// Exemplos navegáveis (sem JS no cliente): cada link faz uma pergunta. O 3º é fora do acervo —
// mostra a IA se ABSTENDO (não inventa). A IA só afirma o que recupera, sempre com citação.
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
  { q: "Qual será a cotação do dólar amanhã?" }, // fora do repositório → a IA se abstém
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

export default async function PerguntarPage({
  searchParams,
}: {
  searchParams: { q?: string; indicador?: string; territorio?: string };
}) {
  const { q, indicador, territorio } = searchParams;
  const resposta = q ? await perguntarIA({ pergunta: q, indicador, territorio }) : null;

  return (
    <main className="pagina">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <p className="pulso-pergunta">IA ancorada</p>
      <h1>Pergunte aos dados</h1>
      <p className="home-lead">
        A IA só afirma o que <strong>recupera</strong> do repositório, sempre com <strong>citação</strong>{" "}
        da fonte. Sem dado, ela <strong>se abstém</strong> — não inventa número nem causalidade. Sem
        chave de LLM, narra em modo <strong>template</strong> (degradação graciosa); o que não muda é a
        ancoragem.
      </p>

      <section>
        <h2>Sua pergunta</h2>
        <form method="get" action="/perguntar" className="ia-form">
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
          <div className="ia-form-campo">
            <label htmlFor="territorio">Município — código IBGE (opcional)</label>
            <input
              id="territorio"
              name="territorio"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              defaultValue={territorio ?? ""}
              placeholder="ex.: 3550308"
            />
          </div>
          <button type="submit">Perguntar</button>
        </form>
        <p className="ia-form-nota">
          Não precisa escolher o indicador — a IA tenta achar o mais relevante pela sua pergunta e
          cita a fonte. Sem dado, ela se abstém.
        </p>
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
          <h2>“{q}”</h2>
          <Resposta r={resposta} />
        </section>
      ) : null}
    </main>
  );
}
