import Link from "next/link";
import type { ReactNode } from "react";

import { AUTH_HABILITADO, sessaoAtual, type SessaoCidadao } from "../lib/auth";

// Portão de autenticação honesto da área do cidadão. Enquanto o OIDC (gov.br) não está liberado —
// gate externo do dono — renderiza o aviso "ainda não liberado" + a prévia inerte (o lugar já está
// preparado). Quando houver sessão, entrega-a aos filhos (área viva). SSR puro (sem "use client"/
// Context): a verdade ("ninguém está logado") fica explícita, não fingida.
export async function PortaoAuth({
  children,
  previa,
}: {
  children: (sessao: SessaoCidadao) => ReactNode;
  previa?: ReactNode;
}) {
  const sessao = AUTH_HABILITADO ? await sessaoAtual() : null;
  if (!sessao) {
    return (
      <>
        <aside className="portao" role="note" aria-label="Área que requer login">
          <span className="portao-icone" aria-hidden="true">
            🔒
          </span>
          <div>
            <strong>Você não está autenticado.</strong> Esta área exige login gov.br, que ainda não
            foi liberado. Abaixo está a prévia do que ela vai oferecer — desabilitada, mas já
            desenhada. <Link href="/entrar">Ir para Entrar →</Link>
          </div>
        </aside>
        {previa}
      </>
    );
  }
  return <>{children(sessao)}</>;
}
