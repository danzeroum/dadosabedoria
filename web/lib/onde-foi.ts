import type { Banda } from "./types";

// Tokens do OndeFoi (TRANSP-06). A BANDA é sinal de ATENÇÃO ("merece a pergunta"), não veredito
// (ADR-0026/0029): liquidado÷empenhado — empenhar ≠ liquidar ≠ serviço. Cor redundante com texto
// (ADR-0009), num único lugar.

export const CORES_BANDA: Record<Banda, string> = {
  alta: "#16a34a", // liquidou quase tudo que empenhou — confira se virou serviço
  parcial: "#b45309",
  baixa: "#dc2626", // liquidou pouco do que empenhou — merece a pergunta
  indef: "#6b7280", // sem liquidação divulgada
};

export const ROTULOS_BANDA: Record<Banda, string> = {
  alta: "liquidou quase tudo",
  parcial: "liquidou parte",
  baixa: "liquidou pouco",
  indef: "sem liquidação divulgada",
};

// Descrição honesta do que a banda sinaliza (vai no title/sr-only — nunca só a cor).
export const DESCRICAO_BANDA: Record<Banda, string> = {
  alta: "liquidou ≥80% do que empenhou — confira se virou serviço (liquidar não é entregar)",
  parcial: "liquidou entre 55% e 80% do que empenhou",
  baixa: "liquidou menos de 55% do que empenhou — merece a pergunta",
  indef: "sem valor de liquidação divulgado para a base",
};

const COR_NEUTRA = "#6b7280";

export function corBanda(b: Banda): string {
  return CORES_BANDA[b] ?? COR_NEUTRA;
}

export function rotuloBanda(b: Banda): string {
  return ROTULOS_BANDA[b] ?? b;
}

// Valor orçamentário em reais, milhar pt-BR, sem centavos (grão do agregado).
export function formatarReais(n: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatarPct(p: number | null): string {
  return p == null ? "—" : `${p}%`;
}

// Banda por função a partir do % (mesma regra do backend, ADR-0026; espelha o handoff de design).
export function banda(pct: number | null): Banda {
  if (pct == null) return "indef";
  if (pct >= 80) return "alta";
  if (pct >= 55) return "parcial";
  return "baixa";
}

// Valor em R$ milhões (intenção do handoff: orçamentos municipais em bi/mi). Grau-demo — os números
// do OndeFoi são ilustrativos até a 1ª busca real no SICONFI/DCA (#0).
export function formatarMilhoes(n: number): string {
  if (n >= 1000) return `R$ ${(n / 1000).toFixed(1).replace(".", ",")} bi`;
  return `R$ ${Math.round(n)} mi`;
}

// Mensagem honesta de acompanhamento conforme a banda (sinal de atenção, nunca veredito).
export function mensagemBanda(b: Banda): string {
  if (b === "baixa") return "Liquidou pouco do que empenhou — recurso pode estar parado, vale cobrar.";
  if (b === "alta") return "Liquidou quase tudo — o próximo passo é checar se virou serviço na ponta.";
  if (b === "parcial") return "Liquidação parcial — acompanhe onde o recurso travou.";
  return "Sem liquidação divulgada para a base.";
}
