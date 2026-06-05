import type { Semaforo } from "./types";

// Tokens de cor do semáforo (contraste AA sobre fundo claro). Único lugar onde a cor é definida.
export const CORES: Record<Semaforo, string> = {
  verde: "#16a34a",
  amarelo: "#b45309",
  vermelho: "#dc2626",
};

// Rótulo textual — acessibilidade: nunca comunicar só por cor.
export const ROTULOS: Record<Semaforo, string> = {
  verde: "baixa vulnerabilidade",
  amarelo: "vulnerabilidade média",
  vermelho: "alta vulnerabilidade",
};

export function corSemaforo(estado: Semaforo): string {
  return CORES[estado] ?? "#6b7280";
}

export function rotuloSemaforo(estado: Semaforo): string {
  return ROTULOS[estado] ?? estado;
}

// Mesma regra do backend (ADR-0008): < 33 verde, 33–66 amarelo, > 66 vermelho.
export function classificar(ivm: number): Semaforo {
  if (ivm < 33) return "verde";
  if (ivm <= 66) return "amarelo";
  return "vermelho";
}

export function formatarIVM(valor: number): string {
  return valor.toFixed(1);
}
