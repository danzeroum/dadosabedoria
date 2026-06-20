import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import {
  buscarCoberturaSiconfi,
  buscarFontes,
  buscarIVM,
  buscarPanorama,
} from "./api";

// Exercita os 3 helpers de fetch (pedir/pedirOuNull/pedirSilencioso) pela API pública,
// fixando os modos de erro e de cache — guarda contra um flip silencioso (Bloco 4.3).

let fetchMock: Mock;

function resposta(status: number, body: unknown = {}): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("cliente api — modos de erro", () => {
  it("pedirOuNull: 404 → null", async () => {
    fetchMock.mockResolvedValue(resposta(404));
    expect(await buscarPanorama("3550308")).toBeNull();
  });

  it("pedirOuNull: 200 → corpo", async () => {
    const corpo = { codigo_ibge: "3550308" };
    fetchMock.mockResolvedValue(resposta(200, corpo));
    expect(await buscarPanorama("3550308")).toEqual(corpo);
  });

  it("pedirOuNull: 500 → lança (não engole)", async () => {
    fetchMock.mockResolvedValue(resposta(500));
    await expect(buscarPanorama("3550308")).rejects.toThrow();
  });

  it("pedirSilencioso: qualquer !ok → null (degrada em silêncio)", async () => {
    fetchMock.mockResolvedValue(resposta(503));
    expect(await buscarFontes()).toBeNull();
  });

  it("pedir: !ok → lança (recurso obrigatório, ex.: IVM)", async () => {
    fetchMock.mockResolvedValue(resposta(503));
    await expect(buscarIVM()).rejects.toThrow();
  });
});

describe("cliente api — modo de cache explícito por chamada", () => {
  it("cobertura (flag-demo) usa no-store; leitura de produto usa revalidate=300", async () => {
    fetchMock.mockResolvedValue(resposta(200, {}));

    await buscarCoberturaSiconfi();
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ cache: "no-store" });

    fetchMock.mockClear();
    await buscarPanorama("3550308");
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ next: { revalidate: 300 } });
  });
});
