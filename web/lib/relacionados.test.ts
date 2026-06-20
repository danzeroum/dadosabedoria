import { describe, expect, it } from "vitest";

import { produtosRelacionados, slugBase } from "./relacionados";

describe("relacionados", () => {
  it("slugBase extrai o slug de href municipal e ignora telas não-municipais", () => {
    expect(slugBase("/pulso/3550308")).toBe("pulso");
    expect(slugBase("/onde-foi/3304557")).toBe("onde-foi");
    expect(slugBase("/ivm")).toBeNull();
    expect(slugBase("/comparar")).toBeNull();
  });

  it("sugere produtos do mesmo domínio, reancorados no município, sem incluir o atual", () => {
    const rel = produtosRelacionados("pulso", "3550308");
    expect(rel.length).toBeGreaterThan(0);
    // Pulso é do domínio trabalho → relacionados são trabalho (Salário Radar, Giro Local, ...).
    for (const p of rel) {
      expect(p.href.startsWith("/")).toBe(true);
      expect(p.href.endsWith("/3550308")).toBe(true);
      expect(p.href).not.toBe("/pulso/3550308"); // nunca o próprio
    }
  });

  it("produto desconhecido não quebra (lista vazia)", () => {
    expect(produtosRelacionados("inexistente", "3550308")).toEqual([]);
  });

  it("respeita o limite máximo", () => {
    expect(produtosRelacionados("pulso", "3550308", 2).length).toBeLessThanOrEqual(2);
  });
});
