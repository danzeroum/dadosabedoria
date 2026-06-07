import { describe, expect, it } from "vitest";

import { corPulso, formatarSaldo, rotuloPulso } from "./pulso";

describe("formatarSaldo", () => {
  it("mostra o sinal explícito (o sinal é a informação)", () => {
    expect(formatarSaldo(8200)).toBe("+8.200"); // milhar pt-BR
    expect(formatarSaldo(-9100)).toBe("−9.100"); // sinal de menos tipográfico (U+2212)
    expect(formatarSaldo(100)).toBe("+100");
  });

  it("zero não recebe sinal", () => {
    expect(formatarSaldo(0)).toBe("0");
  });
});

describe("tokens do pulso", () => {
  it("o rótulo nunca é só cor — cada nível tem texto honesto", () => {
    expect(rotuloPulso("aquecido")).toBe("criando vagas formais");
    expect(rotuloPulso("esfriando")).toBe("perdendo vagas formais");
    expect(rotuloPulso("estavel")).toBe("estável");
  });

  it("a cor vem de um único lugar (paleta do semáforo)", () => {
    expect(corPulso("aquecido")).toBe("#16a34a");
    expect(corPulso("esfriando")).toBe("#dc2626");
  });
});
