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
