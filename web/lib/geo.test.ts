import { describe, expect, it } from "vitest";

import { projetar } from "./geo";
import type { FeatureCollectionIVM } from "./types";

function quadrado(cod: string, lon: number, lat: number, ivm: number | null) {
  const d = 0.2;
  return {
    type: "Feature" as const,
    geometry: {
      type: "Polygon" as const,
      coordinates: [
        [
          [lon, lat],
          [lon + d, lat],
          [lon + d, lat + d],
          [lon, lat + d],
          [lon, lat],
        ],
      ],
    },
    properties: {
      codigo_ibge: cod,
      nome: cod,
      ivm,
      semaforo: ivm == null ? null : ("amarelo" as const),
      v_emprego: null,
      v_financas: null,
    },
  };
}

const FC: FeatureCollectionIVM = {
  type: "FeatureCollection",
  features: [quadrado("3550308", -46.8, -23.7, 50), quadrado("3509502", -47.2, -23.0, null)],
};

describe("projetar", () => {
  it("gera viewBox e um path por feature", () => {
    const p = projetar(FC, 400, 400);
    expect(p.viewBox).toBe("0 0 400 400");
    expect(p.formas).toHaveLength(2);
    for (const forma of p.formas) {
      expect(forma.d.startsWith("M")).toBe(true);
      expect(forma.d.endsWith("Z")).toBe(true);
    }
  });

  it("preserva o IVM/semáforo (e o nulo)", () => {
    const p = projetar(FC);
    const sp = p.formas.find((f) => f.codigo_ibge === "3550308");
    const cps = p.formas.find((f) => f.codigo_ibge === "3509502");
    expect(sp?.ivm).toBe(50);
    expect(cps?.ivm).toBeNull();
  });
});
