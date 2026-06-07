import type { Banda } from "./types";

// Tokens do OndeFoi (TRANSP-06). A BANDA é sinal de ATENÇÃO ("merece a pergunta"), não veredito
// (ADR-0026): executar ≠ virar serviço. Cor sempre redundante com texto (ADR-0009), num único lugar.

export const CORES_BANDA: Record<Banda, string> = {
  alta: "#16a34a", // executou quase tudo — confira se virou serviço
  parcial: "#b45309",
  baixa: "#dc2626", // executou pouco do que recebeu — merece a pergunta
  indef: "#6b7280", // sem execução divulgada
};

export const ROTULOS_BANDA: Record<Banda, string> = {
  alta: "executou quase tudo",
  parcial: "executou parte",
  baixa: "executou pouco",
  indef: "sem execução divulgada",
};

// Descrição honesta do que a banda sinaliza (vai no title/sr-only — nunca só a cor).
export const DESCRICAO_BANDA: Record<Banda, string> = {
  alta: "executou ≥80% do que recebeu — confira se virou serviço (executar não é entregar)",
  parcial: "executou entre 55% e 80% do que recebeu",
  baixa: "executou menos de 55% do que recebeu — merece a pergunta",
  indef: "sem valor de execução divulgado para a base",
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
  if (b === "baixa") return "Executar pouco pode significar recurso parado — vale cobrar por quê.";
  if (b === "alta") return "Executou quase tudo — o próximo passo é checar se virou serviço na ponta.";
  if (b === "parcial") return "Execução parcial — acompanhe onde o recurso travou.";
  return "Sem execução divulgada para a base.";
}
