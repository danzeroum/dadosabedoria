import { describe, expect, it } from "vitest";

import { formatarValor } from "./formato";

describe("formatarValor", () => {
  it("reais com R$ e milhar, sem centavos", () => {
    const s = formatarValor(1500000000, "reais");
    expect(s).toContain("R$");
    expect(s).toContain("1.500.000.000");
    expect(s).not.toContain(",");
  });

  it("contagem em milhar pt-BR, com sinal quando negativo", () => {
    expect(formatarValor(980000, "contagem")).toBe("980.000");
    expect(formatarValor(-9100, "contagem")).toBe("-9.100"); // saldo pode ser negativo
  });
});
