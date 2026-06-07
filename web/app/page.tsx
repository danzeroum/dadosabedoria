import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "DadoSabedoria — produtos",
  description: "Produtos de inteligência sobre dados públicos brasileiros, com proveniência.",
};

// Porta de entrada: cada produto é uma PERGUNTA com uma tela mínima. Links de exemplo apontam para
// municípios no acervo (seed) — honesto sobre o que é dado real e o que é demonstração.
const PRODUTOS: {
  titulo: string;
  pergunta: string;
  descricao: string;
  href: string;
  cta: string;
  selo: string | null;
}[] = [
  {
    titulo: "IVM — mapa semafórico",
    pergunta: "Quão vulnerável é o meu município?",
    descricao:
      "Índice de Vulnerabilidade Municipal: emprego, finanças e saúde num só sinal, do verde ao vermelho — o que é protegido aparece como protegido.",
    href: "/ivm",
    cta: "Abrir o mapa",
    selo: null,
  },
  {
    titulo: "Pulso Produtivo",
    pergunta: "Como está o emprego formal no meu município?",
    descricao:
      "O saldo do Novo CAGED mês a mês — criando ou perdendo vagas com carteira, com a tendência honesta (o fluxo é volátil; merece a pergunta).",
    href: "/pulso/3550308",
    cta: "Ver exemplo (São Paulo)",
    selo: null,
  },
  {
    titulo: "OndeFoi",
    pergunta: "A transferência da União virou serviço?",
    descricao:
      "Recebido × executado por função do orçamento municipal. Executar não é entregar — o número que merece a pergunta, nunca o veredito.",
    href: "/onde-foi/3304557",
    cta: "Ver exemplo (Rio de Janeiro)",
    selo: "demonstração",
  },
];

export default function Home() {
  return (
    <main className="pagina home">
      <section className="home-hero">
        <h1>Inteligência de dados públicos brasileiros</h1>
        <p className="home-lead">
          A confiança é o ativo: <strong>privacidade estrutural</strong>, <strong>proveniência</strong>{" "}
          em cada número e <strong>qualidade provada</strong> a cada commit. Sem chave de pessoa; o
          que é protegido aparece como protegido.
        </p>
      </section>

      <section className="home-produtos" aria-label="Produtos">
        {PRODUTOS.map((p) => (
          <Link key={p.href} href={p.href} className="home-card">
            <div className="home-card-topo">
              <h2>{p.titulo}</h2>
              {p.selo ? <span className="home-selo">{p.selo}</span> : null}
            </div>
            <p className="home-pergunta">{p.pergunta}</p>
            <p className="home-descricao">{p.descricao}</p>
            <span className="home-cta">{p.cta} →</span>
          </Link>
        ))}
      </section>

      <p className="home-nota">
        Dados abertos (IBGE · Novo CAGED · BCB/ESTBAN · DATASUS/SIH · SICONFI/STN · INEP · PNCP). Cada
        tela traz sua metodologia e a fonte. O OndeFoi roda em demonstração até o dado vivo do Tesouro.
      </p>
    </main>
  );
}
