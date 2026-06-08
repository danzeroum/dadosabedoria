import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "DadoSabedoria",
  description: "Inteligência de dados públicos brasileiros, com privacidade e proveniência.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <header className="topo">
          <Link href="/" className="topo-marca">
            DadoSabedoria
          </Link>
          <nav className="topo-nav" aria-label="Produtos">
            <Link href="/ivm">IVM</Link>
            <Link href="/comparar">Comparar</Link>
            <Link href="/pulso/3550308">Pulso</Link>
            <Link href="/onde-foi/3304557">OndeFoi</Link>
            <Link href="/perguntar">Perguntar</Link>
          </nav>
        </header>
        <div className="conteudo">{children}</div>
        <footer className="rodape">
          <nav className="rodape-nav" aria-label="Transparência">
            <Link href="/fontes">Fontes &amp; confiança</Link>
            <Link href="/comparar">Comparar municípios</Link>
            <Link href="/ivm">Mapa do IVM</Link>
          </nav>
          <p className="rodape-nota">
            Dados públicos abertos. Privacidade estrutural e proveniência em cada número —
            metodologia e fonte em cada tela.
          </p>
        </footer>
      </body>
    </html>
  );
}
