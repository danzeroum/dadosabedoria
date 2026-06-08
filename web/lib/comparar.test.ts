import { describe, expect, it } from "vitest";

import { agruparPorDominio, alinharIndicadores } from "./comparar";
import type { IndicadorValor } from "./types";

function ind(codigo: string, dominio: string, nome: string, valor: number | null): IndicadorValor {
  return {
    codigo,
    nome,
    dominio,
    subdominio: "",
    unidade: "contagem",
    polaridade: "neutra",
    periodo: "2026-04",
    valor,
    suprimido: valor === null,
    motivo_supressao: null,
    fonte: "X",
    lag_tipico_dias: null,
    metodologia: "",
  };
}

describe("alinharIndicadores", () => {
  it("alinha por código, ordena por domínio/nome, null onde falta", () => {
    const a = [ind("trabalho.x", "trabalho", "Emprego", 100), ind("saude.y", "saude", "Saúde", 5)];
    const b = [ind("trabalho.x", "trabalho", "Emprego", 80)]; // b não tem saúde
    const linhas = alinharIndicadores(a, b);
    // ordenado por domínio: "saude" < "trabalho"
    expect(linhas.map((l) => l.codigo)).toEqual(["saude.y", "trabalho.x"]);
    const saude = linhas[0];
    expect(saude.a?.valor).toBe(5);
    expect(saude.b).toBeNull(); // explícito: b não tem o indicador
    const trab = linhas[1];
    expect(trab.a?.valor).toBe(100);
    expect(trab.b?.valor).toBe(80);
  });

  it("preserva o indicador presente quando só um lado o tem (usa-o como referência)", () => {
    const linhas = alinharIndicadores([], [ind("compras.z", "compras", "Contratos", 9)]);
    expect(linhas).toHaveLength(1);
    expect(linhas[0].nome).toBe("Contratos");
    expect(linhas[0].a).toBeNull();
    expect(linhas[0].b?.valor).toBe(9);
  });
});

describe("agruparPorDominio", () => {
  it("agrupa preservando a ordem ordenada", () => {
    const linhas = alinharIndicadores(
      [ind("trabalho.x", "trabalho", "Emprego", 1), ind("saude.y", "saude", "Saúde", 2)],
      [],
    );
    const grupos = agruparPorDominio(linhas);
    expect(grupos.map(([d]) => d)).toEqual(["saude", "trabalho"]);
  });
});
