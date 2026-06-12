import type { Metadata } from "next";
import Link from "next/link";

import { buscarFontes } from "../lib/api";

export const dynamic = "force-dynamic";

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
    pergunta: "Do que a prefeitura empenhou por função, quanto saiu do papel?",
    descricao:
      "Liquidado × empenhado por função do orçamento municipal (SICONFI). Empenhar não é liquidar, liquidar não é entregar — o número que merece a pergunta, nunca o veredito.",
    href: "/onde-foi",
    cta: "Explorar municípios",
    selo: null,
  },
  {
    titulo: "ObraViva",
    pergunta: "Quanto o município contrata publicamente via PNCP?",
    descricao:
      "Soma do valor global de contratos publicados no PNCP no exercício (obras, serviços e bens). Per capita para comparar municípios de portes diferentes. Nota: ausência de dado ≠ ausência de contratação — PNCP ainda não tem adesão universal.",
    href: "/obra-viva/3550308",
    cta: "Ver exemplo (São Paulo)",
    selo: null,
  },
  {
    titulo: "Panorama do município",
    pergunta: "O que sabemos sobre o meu município?",
    descricao:
      "Todos os indicadores do acervo num só lugar — emprego, crédito, saúde, finanças, educação, compras — com a fonte de cada número. O protegido aparece como protegido.",
    href: "/municipio/3550308",
    cta: "Ver exemplo (São Paulo)",
    selo: null,
  },
  {
    titulo: "Bússola Educação-Trabalho",
    pergunta: "Como está a base educacional e o emprego formal no município?",
    descricao:
      "Matrículas no ensino fundamental (INEP/Censo Escolar) + saldo de emprego formal + salário médio das admissões (CAGED). Contexto para enquadrar — não causalidade: mais matrículas não é garantia de mais empregos.",
    href: "/bussola-edu-trabalho/3550308",
    cta: "Ver exemplo (São Paulo)",
    selo: null,
  },
  {
    titulo: "Radar de Evasão Escolar",
    pergunta: "Quantas crianças em idade escolar estão fora do ensino fundamental?",
    descricao:
      "Matrículas do ensino fundamental (INEP/Censo Escolar) divididas por uma estimativa da população em idade escolar (14 % da população). Taxa > 100 % indica polo de atração — não erro. Só cobre o EF formal; não inclui EJA, creche nem pré-escola.",
    href: "/radar-evasao/3550308",
    cta: "Ver exemplo (São Paulo)",
    selo: null,
  },
  {
    titulo: "Sentinela Respiratória",
    pergunta: "Como estão as internações por doenças respiratórias no município?",
    descricao:
      "Contagem de AIH com diagnóstico no grupo J do CID-10 (J00–J99) no SIH/SUS por mês. Cobre só o SUS público; células com menos de 5 internações são protegidas pelo k-anonimato e aparecem como 'Protegido' — nunca como zero.",
    href: "/sentinela-resp/3550308",
    cta: "Ver exemplo (São Paulo)",
    selo: null,
  },
  {
    titulo: "Comparar municípios",
    pergunta: "Como meu município se compara a outro?",
    descricao:
      "Dois municípios lado a lado, indicador por indicador, com fonte e período. Descritivo — contexto para perguntar, não um ranking de melhor ou pior; o protegido segue protegido.",
    href: "/comparar",
    cta: "Comparar",
    selo: null,
  },
  {
    titulo: "Pergunte aos dados",
    pergunta: "Posso perguntar em vez de procurar?",
    descricao:
      "A IA responde só com o que recupera do repositório, sempre com citação da fonte. Sem dado, abstém-se — não inventa número nem causalidade.",
    href: "/perguntar",
    cta: "Fazer uma pergunta",
    selo: null,
  },
];

// Resumo honesto do acervo (vivo), pelo próprio /v1/fontes. Degrada em silêncio: se a API não
// responder (ex.: build sem backend), a porta de entrada segue inteira, só sem o resumo.
async function acervoResumo(): Promise<{ fontes: number; indicadores: number; dominios: number } | null> {
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

export default async function Home() {
  const acervo = await acervoResumo();
  return (
    <main className="pagina home">
      <section className="home-hero">
        <h1>Inteligência de dados públicos brasileiros</h1>
        <p className="home-lead">
          A confiança é o ativo: <strong>privacidade estrutural</strong>, <strong>proveniência</strong>{" "}
          em cada número e <strong>qualidade provada</strong> a cada commit. Sem chave de pessoa; o
          que é protegido aparece como protegido.
        </p>
        {acervo ? (
          <Link href="/fontes" className="home-acervo">
            <strong>{acervo.fontes}</strong> fontes públicas ·{" "}
            <strong>{acervo.indicadores}</strong> indicadores ·{" "}
            <strong>{acervo.dominios}</strong> domínios — com proveniência e supressão honesta em cada
            número →
          </Link>
        ) : null}
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
        tela traz sua metodologia e a fonte. O OndeFoi usa dados reais do SICONFI/STN (Anexo I-E, exercício 2024).{" "}
        <Link href="/fontes">De onde vêm os dados e como protegemos →</Link>
      </p>
    </main>
  );
}
