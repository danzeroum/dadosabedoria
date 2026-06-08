import Link from "next/link";

import { ExecPill } from "../../components/ExecPill";
import { SeloConfianca } from "../../components/SeloConfianca";
import { buscarListaOndeFoi } from "../../lib/api";

export const dynamic = "force-dynamic";

// Diretório do OndeFoi: porta para o detalhe por município. Busca server-side (sem JS), espelhando
// o /ivm. Dupla-face §17 (números grau-demo): ordenado por NOME (não ranking), com aviso forte de
// "ilustrativo" — nada de leaderboard de execução provisória; a ExecPill já enquadra "merece a
// pergunta, não veredito".
export default async function OndeFoiDiretorioPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const lista = await buscarListaOndeFoi();
  if (!lista) {
    return (
      <main className="pagina">
        <h1>Onde foi o dinheiro?</h1>
        <p className="erro">Não foi possível carregar o OndeFoi agora. Verifique se a API está no ar.</p>
      </main>
    );
  }

  const q = (searchParams.q ?? "").trim();
  const ql = q.toLowerCase();
  const dados = q
    ? lista.dados.filter((m) => m.nome.toLowerCase().includes(ql) || m.codigo_ibge.includes(q))
    : lista.dados;

  return (
    <main className="pagina">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Onde foi o dinheiro?</h1>
      <p className="of-sub">
        Execução orçamentária por função (liquidado ÷ empenhado) por município, no exercício. Escolha
        um município para ver o detalhe. Executar não é entregar — o número que merece a pergunta,
        nunca o veredito.
      </p>

      <p className="of-demo-aviso" role="note">
        <strong>Números ilustrativos (grau-demo).</strong> Exemplos até a 1ª busca real no
        SICONFI/DCA — <strong>não refletem a gestão real</strong> e estão ordenados por nome,{" "}
        <strong>sem ranking</strong>.
      </p>

      <SeloConfianca meta={lista.meta} />

      <form className="ivm-busca" method="get" role="search">
        <label htmlFor="busca-of">Buscar município</label>
        <input
          id="busca-of"
          name="q"
          type="search"
          defaultValue={q}
          placeholder="nome ou código IBGE"
        />
        <button type="submit">Buscar</button>
        {q ? (
          <Link href="/onde-foi" className="uf-limpar">
            limpar
          </Link>
        ) : null}
      </form>

      {dados.length === 0 ? (
        <p className="vazio">Nenhum município encontrado{q ? ` para “${q}”` : ""}.</p>
      ) : (
        <ul className="of-dir" aria-label="Municípios do OndeFoi">
          {dados.map((m) => (
            <li key={m.codigo_ibge} className="of-dir-card">
              <Link href={`/onde-foi/${m.codigo_ibge}`} className="of-dir-link">
                <span className="of-dir-nome">{m.nome}</span>
                <span className="of-dir-uf tnum">
                  {m.uf} · {m.codigo_ibge}
                </span>
              </Link>
              <ExecPill banda={m.banda} pct={m.pct} />
            </li>
          ))}
        </ul>
      )}

      <p className="metodologia">
        {lista.meta.metodologia} · grau-demo até a 1ª busca real no SICONFI/DCA (#0).
      </p>
    </main>
  );
}
