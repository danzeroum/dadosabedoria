import { describe, expect, it } from "vitest";

import { corBanda, formatarPct, formatarReais, rotuloBanda } from "./onde-foi";

describe("formatarReais", () => {
  it("formata em reais com milhar pt-BR, sem centavos", () => {
    const s = formatarReais(41200);
    expect(s).toContain("R$"); // símbolo
    expect(s).toContain("41.200"); // milhar pt-BR
    expect(s).not.toContain(","); // sem centavos
  });
});

describe("formatarPct", () => {
  it("mostra % e um travessão quando não há valor", () => {
    expect(formatarPct(88)).toBe("88%");
    expect(formatarPct(0)).toBe("0%");
    expect(formatarPct(null)).toBe("—"); // sem cobertura → não é 0%
  });
});

describe("tokens da banda", () => {
  it("o rótulo nunca é só cor — cada banda tem texto honesto (atenção, não veredito)", () => {
    expect(rotuloBanda("alta")).toBe("executou quase tudo");
    expect(rotuloBanda("baixa")).toBe("executou pouco");
    expect(rotuloBanda("indef")).toBe("sem execução divulgada");
  });

  it("a cor vem de um único lugar (paleta do semáforo)", () => {
    expect(corBanda("alta")).toBe("#16a34a");
    expect(corBanda("baixa")).toBe("#dc2626");
  });
});
