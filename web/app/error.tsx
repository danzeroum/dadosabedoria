"use client";

import Link from "next/link";

// Boundary de erro (único arquivo "use client" — exigência do Next para error.tsx). Captura falhas
// de render/fetch (fonte fora do ar, erro de SSR) sem tela branca. Honesto: "o erro é nosso";
// distingue "falha na consulta" de "dado perdido". O botão chama reset() para tentar de novo.
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="sistema-centro">
      <p className="sistema-codigo" aria-hidden="true">
        ⚠
      </p>
      <h1>Algo deu errado ao montar esta página</h1>
      <p>
        O erro é nosso, não seu. Pode ser uma fonte pública temporariamente fora do ar ou uma falha
        nossa ao consultar o acervo. Os dados em si não se perdem — só esta consulta falhou.
      </p>
      <div className="sistema-acoes">
        <button className="botao botao-primario" type="button" onClick={() => reset()}>
          Tentar de novo
        </button>
        <Link className="botao botao-secundario" href="/produtos">
          Ver os produtos
        </Link>
      </div>
      <p className="nota" style={{ marginTop: "18px" }}>
        Se persistir, a página de <Link href="/fontes">Fontes</Link> mostra o frescor de cada origem.
      </p>
      {error.digest ? (
        <p
          className="nota"
          style={{
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            fontSize: "0.78rem",
            opacity: 0.8,
          }}
        >
          ref: {error.digest} — informe este código no contato
        </p>
      ) : null}
    </main>
  );
}
