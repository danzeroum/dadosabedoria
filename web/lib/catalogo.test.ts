import { describe, expect, it } from "vitest";

import { CATALOGO, DESTAQUES, DOMINIOS, produtosDoDominio, type DominioId } from "./catalogo";

describe("catalogo", () => {
  it("todo produto tem campos preenchidos e href de rota interna", () => {
    for (const p of CATALOGO) {
      expect(p.titulo.length).toBeGreaterThan(0);
      expect(p.pergunta.length).toBeGreaterThan(0);
      expect(p.descricao.length).toBeGreaterThan(0);
      expect(p.cta.length).toBeGreaterThan(0);
      expect(p.fonte.length).toBeGreaterThan(0);
      expect(p.href.startsWith("/")).toBe(true);
    }
  });

  it("todo produto pertence a um domínio declarado", () => {
    const ids = new Set<DominioId>(DOMINIOS.map((d) => d.id));
    for (const p of CATALOGO) {
      expect(ids.has(p.dominio)).toBe(true);
    }
  });

  it("todo domínio declarado tem ao menos um produto", () => {
    for (const d of DOMINIOS) {
      expect(produtosDoDominio(d.id).length).toBeGreaterThan(0);
    }
  });

  it("tem 4 telas de síntese e 28 produtos temáticos", () => {
    const sintese = CATALOGO.filter((p) => p.dominio === "sintese");
    const tematicos = CATALOGO.filter((p) => p.dominio !== "sintese");
    expect(sintese.length).toBe(4);
    expect(tematicos.length).toBe(28);
  });

  it("não há href duplicado", () => {
    const hrefs = CATALOGO.map((p) => p.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  it("DESTAQUES é subconjunto do catálogo e todos marcados", () => {
    expect(DESTAQUES.length).toBeGreaterThan(0);
    expect(DESTAQUES.length).toBeLessThan(CATALOGO.length);
    for (const p of DESTAQUES) {
      expect(p.destaque).toBe(true);
      expect(CATALOGO).toContain(p);
    }
  });
});
