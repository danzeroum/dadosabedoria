import { describe, expect, it } from "vitest";

import { significadoIVM, tendenciaIVM } from "./ivm-leitura";
import type { IVMItem } from "./types";

function item(ivm: number): IVMItem {
  return {
    codigo_ibge: "0",
    nome: "X",
    periodo: "2026-08",
    ivm,
    semaforo: "amarelo",
    v_emprego: 0,
    v_financas: 0,
    v_saude: 0,
    v_saude_estado: "valor",
  };
}

describe("significadoIVM (comparativo, não veredito)", () => {
  it("verde acompanha; amarelo atenção; vermelho cobra prioridade sem sentença", () => {
    expect(significadoIVM("Recife", "verde")).toContain("Recife");
    expect(significadoIVM("Recife", "verde")).toContain("menos vulneráveis");
    expect(significadoIVM("Recife", "amarelo")).toContain("atenção");
    const v = significadoIVM("Recife", "vermelho");
    expect(v).toContain("cobrar prioridade");
    expect(v).toContain("não sentença"); // honestidade: sinal, não veredito
  });
});

describe("tendenciaIVM (subir = piora, pois maior = mais vulnerável)", () => {
  it("série subindo → piora", () => {
    const t = tendenciaIVM([item(40), item(45), item(52)]);
    expect(t.direcao).toBe("piora");
    expect(t.texto).toContain("piora");
  });

  it("série caindo → melhora", () => {
    expect(tendenciaIVM([item(60), item(50), item(41)]).direcao).toBe("melhora");
  });

  it("variação desprezível → estável", () => {
    expect(tendenciaIVM([item(50.0), item(50.2)]).direcao).toBe("estavel");
  });

  it("série de 1 ponto → estável (sem veredito)", () => {
    expect(tendenciaIVM([item(50)]).direcao).toBe("estavel");
  });
});
