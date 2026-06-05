import { describe, expect, it } from "vitest";

import { classificar, corSemaforo, formatarIVM, rotuloSemaforo } from "./semaforo";

describe("semaforo", () => {
  it("classifica por faixa (mesma regra do backend)", () => {
    expect(classificar(0)).toBe("verde");
    expect(classificar(32.9)).toBe("verde");
    expect(classificar(33)).toBe("amarelo");
    expect(classificar(66)).toBe("amarelo");
    expect(classificar(66.1)).toBe("vermelho");
    expect(classificar(100)).toBe("vermelho");
  });

  it("mapeia cor e rótulo", () => {
    expect(corSemaforo("verde")).toMatch(/^#[0-9a-f]{6}$/i);
    expect(rotuloSemaforo("vermelho")).toContain("alta");
  });

  it("formata o IVM com uma casa", () => {
    expect(formatarIVM(12.345)).toBe("12.3");
    expect(formatarIVM(100)).toBe("100.0");
  });
});
