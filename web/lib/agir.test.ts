import { describe, expect, it } from "vitest";

import {
  citacaoAbntIvm,
  citacaoAbntOndeFoi,
  linkEmail,
  linkWhatsapp,
  textoCompartilharIvm,
  textoCompartilharOndeFoi,
  urlCanonicaIvm,
  urlCanonicaOndeFoi,
} from "./agir";
import type { IVMItem, MetaIVM, OndeFoiProduto } from "./types";

const D: OndeFoiProduto = {
  codigo_ibge: "3550308",
  nome: "São Paulo",
  uf: "SP",
  empenhado_total: 50000,
  empenhado_base: 42000,
  empenhado_fora_base: 8000,
  liquidado: 33600,
  pct: 80,
  banda: "alta",
  funcoes: [],
  meta: {
    fontes: [{ sigla: "SICONFI", nome: "STN", orgao: "Tesouro", dominio: "x", ate: "2024", atraso: "—" }],
    periodo_rotulo: "exercício 2024",
    atraso_dias: 0,
    versao_metodologia: "v1",
    licenca: "CC BY 4.0",
    metodologia: "execução orçamentária, NÃO serviço entregue",
    periodo: "2024",
  },
};

describe("urlCanonicaOndeFoi", () => {
  it("aponta para a tela do município no domínio canônico", () => {
    expect(urlCanonicaOndeFoi("3550308")).toBe("https://dadosabedoria.org/onde-foi/3550308");
  });
});

describe("textoCompartilharOndeFoi (honesto, sem veredito)", () => {
  it("traz o %, o período e a ressalva execução≠serviço", () => {
    const t = textoCompartilharOndeFoi(D);
    expect(t).toContain("São Paulo");
    expect(t).toContain("80%");
    expect(t).toContain("exercício 2024");
    expect(t).toContain("não serviço entregue"); // a ressalva nunca some
  });
});

describe("linkWhatsapp / linkEmail", () => {
  it("WhatsApp embute texto + link, codificados", () => {
    const u = linkWhatsapp("oi mundo", "https://x.org/a");
    expect(u.startsWith("https://wa.me/?text=")).toBe(true);
    expect(u).toContain(encodeURIComponent("oi mundo https://x.org/a"));
  });

  it("mailto leva assunto e corpo codificados", () => {
    const u = linkEmail("Assunto X", "Corpo & coisa");
    expect(u.startsWith("mailto:?subject=")).toBe(true);
    expect(u).toContain("subject=" + encodeURIComponent("Assunto X"));
    expect(u).toContain("body=" + encodeURIComponent("Corpo & coisa"));
  });
});

describe("citacaoAbntOndeFoi (proveniência embutida)", () => {
  it("inclui obra, município/UF, período, fontes, versão e licença", () => {
    const c = citacaoAbntOndeFoi(D, new Date("2026-06-08T12:00:00Z"));
    expect(c).toContain("DadoSabedoria (2026)");
    expect(c).toContain("São Paulo/SP");
    expect(c).toContain("exercício 2024");
    expect(c).toContain("SICONFI"); // fonte citada
    expect(c).toContain("v1"); // versão da metodologia
    expect(c).toContain("CC BY 4.0"); // licença
  });
});

// ----------------------------------------------------------------- IVM (mesma superfície)

const ITEM: IVMItem = {
  codigo_ibge: "3106200",
  nome: "Belo Horizonte",
  uf: "MG",
  periodo: "2026-08",
  ivm: 42.7,
  semaforo: "amarelo",
  v_emprego: 0.4,
  v_financas: 0.5,
  v_saude: 0.3,
  v_saude_estado: "valor",
};

const META_IVM: MetaIVM = {
  fontes: [
    { sigla: "CAGED", nome: "Novo CAGED", orgao: "MTE", dominio: "x", ate: "2026-08", atraso: "—" },
    { sigla: "ESTBAN", nome: "ESTBAN", orgao: "BCB", dominio: "y", ate: "2026-08", atraso: "—" },
  ],
  periodo_rotulo: "agosto/2026",
  atraso_dias: 30,
  versao_metodologia: "v1.1",
  licenca: "CC BY 4.0",
  indicador: "ivm",
  nome: "Índice de Vulnerabilidade Municipal",
  metodologia: "min-max",
  componentes: ["emprego", "finanças", "saúde"],
  semaforo: {},
  periodo: "2026-08",
};

describe("urlCanonicaIvm", () => {
  it("aponta para o drill-down do IVM no domínio canônico", () => {
    expect(urlCanonicaIvm("3106200")).toBe("https://dadosabedoria.org/ivm/3106200");
  });
});

describe("textoCompartilharIvm (comparativo, não veredito)", () => {
  it("traz o valor, o período e a ressalva 'não veredito'", () => {
    const t = textoCompartilharIvm(ITEM);
    expect(t).toContain("Belo Horizonte");
    expect(t).toContain("42.7");
    expect(t).toContain("2026-08");
    expect(t).toContain("não veredito"); // honestidade do índice comparativo
  });
});

describe("citacaoAbntIvm (proveniência embutida)", () => {
  it("inclui obra IVM, município/UF, período, fontes, versão e licença", () => {
    const c = citacaoAbntIvm(ITEM, META_IVM, new Date("2026-06-08T12:00:00Z"));
    expect(c).toContain("DadoSabedoria (2026)");
    expect(c).toContain("Índice de Vulnerabilidade Municipal");
    expect(c).toContain("Belo Horizonte/MG");
    expect(c).toContain("agosto/2026");
    expect(c).toContain("CAGED"); // fonte citada
    expect(c).toContain("v1.1"); // versão da metodologia
    expect(c).toContain("CC BY 4.0"); // licença
  });
});
