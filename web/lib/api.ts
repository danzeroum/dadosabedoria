import type {
  FeatureCollectionIVM,
  PulsoProduto,
  RespostaIVM,
  RespostaIVMSerie,
} from "./types";

// Fetch server-side (sem CORS). Em compose, API_URL = http://api:8000 (rede interna).
const BASE = process.env.API_URL ?? "http://localhost:8000";

// Cache de leitura de 5 min — alinha com o cache do backend e a periodicidade mensal do dado.
const REVALIDATE = 300;

export async function buscarIVM(periodo?: string): Promise<RespostaIVM> {
  const url = new URL("/v1/ivm", BASE);
  if (periodo) url.searchParams.set("periodo", periodo);
  const resp = await fetch(url, { next: { revalidate: REVALIDATE } });
  if (!resp.ok) {
    throw new Error(`Falha ao buscar IVM (${resp.status})`);
  }
  return resp.json();
}

export async function buscarMalhaIVM(
  uf: string,
  periodo?: string,
): Promise<FeatureCollectionIVM> {
  const url = new URL("/v1/mapa/ivm", BASE);
  url.searchParams.set("uf", uf);
  if (periodo) url.searchParams.set("periodo", periodo);
  const resp = await fetch(url, { next: { revalidate: REVALIDATE } });
  if (!resp.ok) {
    throw new Error(`Falha ao buscar malha do IVM (${resp.status})`);
  }
  return resp.json();
}

export async function buscarSerieIVM(codigoIbge: string): Promise<RespostaIVMSerie | null> {
  const resp = await fetch(new URL(`/v1/ivm/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar série do IVM (${resp.status})`);
  }
  return resp.json();
}

export async function buscarPulso(codigoIbge: string): Promise<PulsoProduto | null> {
  const resp = await fetch(new URL(`/v1/pulso-produtivo/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar o Pulso Produtivo (${resp.status})`);
  }
  return resp.json();
}
