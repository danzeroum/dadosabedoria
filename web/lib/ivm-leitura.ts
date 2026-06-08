import type { IVMItem, Semaforo } from "./types";

// Leitura humana do IVM (handoff TelaDrill): traduz o número em significado e direção. Honesto — o
// IVM é COMPARATIVO (maior = mais vulnerável), sinal para priorizar atenção, nunca veredito sobre a
// gestão (ADR-0018/0025). Lógica pura, testável; a tela só renderiza.

const SIGNIFICADO: Record<Semaforo, (nome: string) => string> = {
  verde: (n) =>
    `${n} está entre as menos vulneráveis hoje. Vale acompanhar a tendência para não perder terreno.`,
  amarelo: (n) =>
    `${n} mostra sinais de atenção: não é emergência, mas a vulnerabilidade está acima das menos ` +
    `vulneráveis — acompanhe de perto.`,
  vermelho: (n) =>
    `${n} está entre as mais vulneráveis. Há razão concreta para cobrar prioridade de quem decide ` +
    `— é sinal comparativo, não sentença.`,
};

export function significadoIVM(nome: string, semaforo: Semaforo): string {
  return (SIGNIFICADO[semaforo] ?? SIGNIFICADO.amarelo)(nome);
}

export type DirecaoTendencia = "piora" | "melhora" | "estavel";

// Tendência no período: maior IVM = mais vulnerável, logo SUBIR = piora. Compara o 1º vs o último
// ponto; estável quando a variação é desprezível (< 0,5 ponto). Série curta → sem veredito.
export function tendenciaIVM(serie: IVMItem[]): { direcao: DirecaoTendencia; texto: string } {
  const valores = serie.map((d) => d.ivm);
  if (valores.length < 2) {
    return { direcao: "estavel", texto: "Série curta demais para uma tendência." };
  }
  const delta = valores[valores.length - 1] - valores[0];
  if (Math.abs(delta) < 0.5) {
    return { direcao: "estavel", texto: "Tendência estável no período." };
  }
  return delta > 0
    ? { direcao: "piora", texto: "Tendência de piora no período — vulnerabilidade subindo." }
    : { direcao: "melhora", texto: "Tendência de melhora no período — vulnerabilidade caindo." };
}
