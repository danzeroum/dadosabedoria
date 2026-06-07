import type { Pulso, Tendencia } from "./types";

// Tokens do Pulso Produtivo (TRAB-01). Único lugar onde a cor é definida — paleta do semáforo,
// contraste AA sobre fundo claro. Acessibilidade: a cor é SEMPRE redundante com texto (lib/pulso.ts
// + os rótulos abaixo), nunca comunica sozinha (ADR-0009).

export const CORES_PULSO: Record<Pulso, string> = {
  aquecido: "#16a34a", // verde — criando vagas
  estavel: "#6b7280", // neutro
  esfriando: "#dc2626", // vermelho — perdendo vagas
};

// Rótulo honesto do NÍVEL (a batida do mês): o que o sinal significa, sem veredito.
export const ROTULOS_PULSO: Record<Pulso, string> = {
  aquecido: "criando vagas formais",
  estavel: "estável",
  esfriando: "perdendo vagas formais",
};

// Rótulo do MOMENTO (mês vs anterior). "melhorando" pode coexistir com "esfriando": ainda perde
// vagas, mas a um ritmo melhor — a nuance honesta que o produto faz questão de mostrar.
export const ROTULOS_TENDENCIA: Record<Tendencia, string> = {
  melhorando: "melhorando vs. o mês anterior",
  estavel: "estável vs. o mês anterior",
  piorando: "piorando vs. o mês anterior",
};

export const SETA_TENDENCIA: Record<Tendencia, string> = {
  melhorando: "↑",
  estavel: "→",
  piorando: "↓",
};

const COR_NEUTRA = "#6b7280";

export function corPulso(p: Pulso): string {
  return CORES_PULSO[p] ?? COR_NEUTRA;
}

export function rotuloPulso(p: Pulso): string {
  return ROTULOS_PULSO[p] ?? p;
}

// Saldo é um fluxo com sinal: o sinal É a informação. Formata com sinal explícito e milhar pt-BR
// (ex.: +8.200, −9.100). Usa o sinal de menos tipográfico (−, U+2212).
export function formatarSaldo(n: number): string {
  const abs = new Intl.NumberFormat("pt-BR").format(Math.abs(n));
  if (n > 0) return `+${abs}`;
  if (n < 0) return `−${abs}`;
  return "0";
}
