import type {
  AguaVivaResponse,
  CacadorArboviroesResponse,
  CoberturaDatasus,
  CoberturaInep,
  CoberturaPncp,
  CoberturaSiconfi,
  CoberturaSnis,
  EsgotoInvisivelResponse,
  BussolaEduTrabProduto,
  CoberturaCAGED,
  FeatureCollectionIVM,
  FomeOcultaResponse,
  GiroLocalProduto,
  IndicadorDetalhe,
  LuzNoMapaResponse,
  PratoFrioResponse,
  SemeandoTransparenciaResponse,
  RioEmRiscoResponse,
  ObraVivaProduto,
  OndeFoiLista,
  OndeFoiProduto,
  Panorama,
  PerguntaInput,
  PulsoProduto,
  RadarEvasaoProduto,
  RegiaoEmpregaProduto,
  RespostaBuscaTerritorios,
  RespostaFontes,
  RespostaIA,
  RespostaIVM,
  RespostaIVMSerie,
  RespostaValores,
  SalarioRadarProduto,
  SentinelaMaternаResponse,
  SentinelaRespProduto,
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

// Cidades parecidas (mesma UF, IVM mais próximo). Degrada para [] em erro — bloco opcional na tela.
export async function buscarSimilaresIVM(codigoIbge: string): Promise<RespostaIVMSerie | null> {
  const resp = await fetch(new URL(`/v1/ivm/${codigoIbge}/similares`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (!resp.ok) {
    return null;
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

export async function buscarRegiaoEmprega(
  codigoIbge: string,
): Promise<RegiaoEmpregaProduto | null> {
  const resp = await fetch(new URL(`/v1/regiao-emprega/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar Região Emprega (${resp.status})`);
  }
  return resp.json();
}

export async function buscarSalarioRadar(codigoIbge: string): Promise<SalarioRadarProduto | null> {
  const resp = await fetch(new URL(`/v1/salario-radar/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar Salário Radar (${resp.status})`);
  }
  return resp.json();
}

export async function buscarGiroLocal(codigoIbge: string): Promise<GiroLocalProduto | null> {
  const resp = await fetch(new URL(`/v1/giro-local/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar Giro Local (${resp.status})`);
  }
  return resp.json();
}

// Diretório do OndeFoi (lista de municípios). Degrada para null em erro — a tela mostra o vazio.
export async function buscarListaOndeFoi(): Promise<OndeFoiLista | null> {
  const resp = await fetch(new URL("/v1/onde-foi", BASE), { next: { revalidate: REVALIDATE } });
  if (!resp.ok) {
    return null;
  }
  return resp.json();
}

export async function buscarOndeFoi(codigoIbge: string): Promise<OndeFoiProduto | null> {
  const resp = await fetch(new URL(`/v1/onde-foi/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar o OndeFoi (${resp.status})`);
  }
  return resp.json();
}

export async function buscarTerritorios(q: string): Promise<RespostaBuscaTerritorios> {
  const url = new URL("/v1/territorios", BASE);
  url.searchParams.set("q", q);
  url.searchParams.set("limit", "20");
  const resp = await fetch(url, { cache: "no-store" });
  if (!resp.ok) {
    return { dados: [], total: 0 };
  }
  return resp.json();
}

export async function buscarPanorama(codigoIbge: string): Promise<Panorama | null> {
  const resp = await fetch(new URL(`/v1/territorios/${codigoIbge}/panorama`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar o panorama (${resp.status})`);
  }
  return resp.json();
}

// Ficha técnica de um indicador. 404 → null (a tela responde com notFound).
export async function buscarIndicador(codigo: string): Promise<IndicadorDetalhe | null> {
  const resp = await fetch(new URL(`/v1/indicadores/${encodeURIComponent(codigo)}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar o indicador (${resp.status})`);
  }
  return resp.json();
}

// Série de um indicador num território (drill-down do panorama). 404/erro → null.
export async function buscarValores(
  indicador: string,
  territorio: string,
): Promise<RespostaValores | null> {
  const url = new URL("/v1/valores", BASE);
  url.searchParams.set("indicador", indicador);
  url.searchParams.set("territorio", territorio);
  const resp = await fetch(url, { next: { revalidate: REVALIDATE } });
  if (!resp.ok) {
    return null;
  }
  return resp.json();
}

// Fontes do acervo (proveniência consolidada). Degrada para null em erro — a tela mostra o vazio.
export async function buscarFontes(): Promise<RespostaFontes | null> {
  const resp = await fetch(new URL("/v1/fontes", BASE), { next: { revalidate: REVALIDATE } });
  if (!resp.ok) {
    return null;
  }
  return resp.json();
}

export async function buscarBussolaEduTrab(
  codigoIbge: string,
): Promise<BussolaEduTrabProduto | null> {
  const resp = await fetch(new URL(`/v1/bussola-edu-trabalho/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar a Bússola Educação-Trabalho (${resp.status})`);
  }
  return resp.json();
}

export async function buscarSentinelaResp(
  codigoIbge: string,
): Promise<SentinelaRespProduto | null> {
  const resp = await fetch(new URL(`/v1/sentinela-resp/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar a Sentinela Respiratória (${resp.status})`);
  }
  return resp.json();
}

export async function buscarCoberturaCAGED(): Promise<CoberturaCAGED | null> {
  // no-store: após ingestão o pipeline invalida o cache Redis do backend e a tela reflete
  // imediatamente — sem necessidade de rebuild. Backend Redis (300 s) absorve o custo.
  const resp = await fetch(new URL("/v1/cobertura/caged", BASE), { cache: "no-store" });
  if (!resp.ok) return null;
  return resp.json();
}

export async function perguntarIA(corpo: PerguntaInput): Promise<RespostaIA> {
  // POST server-side (a IA recupera no banco e ancora a resposta). Sem cache: cada pergunta é única.
  const resp = await fetch(new URL("/v1/ia/perguntar", BASE), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(corpo),
    cache: "no-store",
  });
  if (!resp.ok) {
    throw new Error(`Falha ao perguntar à IA (${resp.status})`);
  }
  return resp.json();
}

export async function buscarRadarEvasao(
  codigoIbge: string,
): Promise<RadarEvasaoProduto | null> {
  const resp = await fetch(new URL(`/v1/radar-evasao/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar o Radar de Evasão (${resp.status})`);
  }
  return resp.json();
}

export async function buscarObraViva(
  codigoIbge: string,
): Promise<ObraVivaProduto | null> {
  const resp = await fetch(new URL(`/v1/obra-viva/${codigoIbge}`, BASE), {
    next: { revalidate: REVALIDATE },
  });
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar o ObraViva (${resp.status})`);
  }
  return resp.json();
}

export async function buscarAguaViva(codigo: string): Promise<AguaVivaResponse | null> {
  const url = `${BASE}/v1/agua-viva/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`AguaViva ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<AguaVivaResponse>;
}

export async function buscarLuzNoMapa(codigo: string): Promise<LuzNoMapaResponse | null> {
  const url = `${BASE}/v1/luz-no-mapa/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`LuzNoMapa ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<LuzNoMapaResponse>;
}

export async function buscarRioEmRisco(codigo: string): Promise<RioEmRiscoResponse | null> {
  const url = `${BASE}/v1/rio-em-risco/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`RioEmRisco ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<RioEmRiscoResponse>;
}

export async function buscarCoberturaSnis(): Promise<CoberturaSnis | null> {
  const resp = await fetch(new URL("/v1/cobertura/snis", BASE), { cache: "no-store" });
  if (!resp.ok) return null;
  return resp.json();
}

export async function buscarCoberturaDatasus(): Promise<CoberturaDatasus | null> {
  const resp = await fetch(new URL("/v1/cobertura/datasus", BASE), { cache: "no-store" });
  if (!resp.ok) return null;
  return resp.json();
}

export async function buscarCoberturaInep(): Promise<CoberturaInep | null> {
  const resp = await fetch(new URL("/v1/cobertura/inep", BASE), { cache: "no-store" });
  if (!resp.ok) return null;
  return resp.json();
}

export async function buscarCoberturaPncp(): Promise<CoberturaPncp | null> {
  const resp = await fetch(new URL("/v1/cobertura/pncp", BASE), { cache: "no-store" });
  if (!resp.ok) return null;
  return resp.json();
}

export async function buscarCoberturaSiconfi(): Promise<CoberturaSiconfi | null> {
  const resp = await fetch(new URL("/v1/cobertura/siconfi", BASE), { cache: "no-store" });
  if (!resp.ok) return null;
  return resp.json();
}

export async function buscarEsgotoInvisivel(
  codigo: string,
): Promise<EsgotoInvisivelResponse | null> {
  const url = `${BASE}/v1/esgoto-invisivel/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`EsgotoInvisivel ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<EsgotoInvisivelResponse>;
}

export async function buscarPratoFrio(codigo: string): Promise<PratoFrioResponse | null> {
  const url = `${BASE}/v1/prato-frio/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`PratoFrio ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<PratoFrioResponse>;
}

export async function buscarSemeandoTransparencia(
  codigo: string
): Promise<SemeandoTransparenciaResponse | null> {
  const url = `${BASE}/v1/semeando-transparencia/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`SemeandoTransparencia ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<SemeandoTransparenciaResponse>;
}

export async function buscarFomeOculta(codigo: string): Promise<FomeOcultaResponse | null> {
  const url = `${BASE}/v1/fome-oculta/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`FomeOculta ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<FomeOcultaResponse>;
}

export async function buscarSentinelaMaterna(
  codigo: string,
): Promise<SentinelaMaternаResponse | null> {
  const url = `${BASE}/v1/sentinela-materna/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`SentinelaMaterna ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<SentinelaMaternаResponse>;
}

export async function buscarCacadorArboviroses(
  codigo: string,
): Promise<CacadorArboviroesResponse | null> {
  const url = `${BASE}/v1/cacador-arboviroses/${codigo}`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`CacadorArboviroses ${codigo}: HTTP ${res.status}`);
  return res.json() as Promise<CacadorArboviroesResponse>;
}
