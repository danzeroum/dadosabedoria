import { describe, expect, it } from "vitest";

import {
  banda,
  corBanda,
  formatarMilhoes,
  formatarPct,
  formatarReais,
  mensagemBanda,
  rotuloBanda,
} from "./onde-foi";

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

describe("banda por % (mesma regra do backend)", () => {
  it("limiares: ≥80 alta, ≥55 parcial, <55 baixa, null indef", () => {
    expect(banda(95)).toBe("alta");
    expect(banda(80)).toBe("alta");
    expect(banda(79)).toBe("parcial");
    expect(banda(55)).toBe("parcial");
    expect(banda(54)).toBe("baixa");
    expect(banda(null)).toBe("indef");
  });
});

describe("formatarMilhoes (grau-demo: orçamentos em bi/mi)", () => {
  it("≥1000 vira bilhões (vírgula pt-BR), senão milhões", () => {
    expect(formatarMilhoes(41200)).toBe("R$ 41,2 bi");
    expect(formatarMilhoes(900)).toBe("R$ 900 mi");
    expect(formatarMilhoes(1000)).toBe("R$ 1,0 bi");
  });
});

describe("mensagemBanda (acompanhamento honesto, não veredito)", () => {
  it("baixa pede a pergunta; alta manda checar o serviço", () => {
    expect(mensagemBanda("baixa")).toContain("cobrar");
    expect(mensagemBanda("alta")).toContain("virou serviço");
  });
});
