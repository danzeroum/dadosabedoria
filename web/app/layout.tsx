import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "DadoSabedoria — IVM",
  description: "Índice de Vulnerabilidade Municipal — mapa semafórico de dados públicos brasileiros.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <header className="topo">
          <Link href="/ivm" className="topo-marca">
            DadoSabedoria <span aria-hidden="true">·</span> IVM
          </Link>
        </header>
        <div className="conteudo">{children}</div>
        <footer className="rodape">
          Dados públicos (Novo CAGED · BCB/ESTBAN). Índice composto v1 — metodologia em cada tela.
        </footer>
      </body>
    </html>
  );
}
