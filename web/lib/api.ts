import type {
  AguaVivaResponse,
  AssisVivaResponse,
  CacadorArboviroesResponse,
  CasaVivaResponse,
  CidadeVivaResponse,
  CulturaVivaResponse,
  CuriosidadesResposta,
  DistribuicaoFuncaoResponse,
  EcoVivaResponse,
  EscolaVivaResponse,
  PerfilOrcamentarioResponse,
  PressaoSusResponse,
  SaneFundoResponse,
  SegurancaVivaResponse,
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
  RespostaQuota,
  RespostaValores,
  SalarioRadarProduto,
  SentinelaMaternaResponse,
  SentinelaRespProduto,
  ViaVivaResponse,
} from "./types";

// Fetch server-side (sem CORS). Em compose, API_URL = http://api:8000 (rede interna).
const BASE = process.env.API_URL ?? "http://localhost:8000";

// Cache de leitura de 5 min — alinha com o cache do backend e a periodicidade mensal do dado.
const REVALIDATE = 300;

// ---------------------------------------------------------------------------
// Núcleo do cliente HTTP. Três modos de erro, um por degradação esperada:
//   pedir          — recurso que sempre existe; !ok → lança (a tela erra).
//   pedirOuNull    — recurso opcional; 404 → null (notFound), outro !ok → lança.
//   pedirSilencioso — bloco opcional/cobertura/quota; qualquer !ok → null.
// O modo de cache é EXPLÍCITO por chamada: "no-store" (cobertura/flag-demo, que
// o pipeline invalida e a tela reflete na hora) vs "revalidate" (leitura de 5 min).
// ---------------------------------------------------------------------------
type ModoCache = "revalidate" | "no-store";

function montarUrl(caminho: string, params?: Record<string, string | undefined>): URL {
  const url = new URL(caminho, BASE);
  for (const [chave, valor] of Object.entries(params ?? {})) {
    if (valor != null) url.searchParams.set(chave, valor);
  }
  return url;
}

function opcoes(modo: ModoCache, headers?: Record<string, string>): RequestInit {
  const base: RequestInit =
    modo === "no-store" ? { cache: "no-store" } : { next: { revalidate: REVALIDATE } };
  return headers ? { ...base, headers } : base;
}

async function pedir<T>(
  caminho: string,
  rotulo: string,
  modo: ModoCache = "revalidate",
  params?: Record<string, string | undefined>,
): Promise<T> {
  const resp = await fetch(montarUrl(caminho, params), opcoes(modo));
  if (!resp.ok) {
    throw new Error(`Falha ao buscar ${rotulo} (${resp.status})`);
  }
  return resp.json() as Promise<T>;
}

async function pedirOuNull<T>(
  caminho: string,
  rotulo: string,
  modo: ModoCache = "revalidate",
  params?: Record<string, string | undefined>,
): Promise<T | null> {
  const resp = await fetch(montarUrl(caminho, params), opcoes(modo));
  if (resp.status === 404) {
    return null;
  }
  if (!resp.ok) {
    throw new Error(`Falha ao buscar ${rotulo} (${resp.status})`);
  }
  return resp.json() as Promise<T>;
}

async function pedirSilencioso<T>(
  caminho: string,
  modo: ModoCache = "revalidate",
  params?: Record<string, string | undefined>,
  headers?: Record<string, string>,
): Promise<T | null> {
  const resp = await fetch(montarUrl(caminho, params), opcoes(modo, headers));
  if (!resp.ok) {
    return null;
  }
  return resp.json() as Promise<T>;
}

// --------------------------------------------------------------------------- IVM

export async function buscarIVM(periodo?: string): Promise<RespostaIVM> {
  return pedir<RespostaIVM>("/v1/ivm", "IVM", "revalidate", { periodo });
}

export async function buscarMalhaIVM(uf: string, periodo?: string): Promise<FeatureCollectionIVM> {
  return pedir<FeatureCollectionIVM>("/v1/mapa/ivm", "malha do IVM", "revalidate", { uf, periodo });
}

export async function buscarSerieIVM(codigoIbge: string): Promise<RespostaIVMSerie | null> {
  return pedirOuNull<RespostaIVMSerie>(`/v1/ivm/${codigoIbge}`, "série do IVM");
}

// Cidades parecidas (mesma UF, IVM mais próximo). Degrada para null em erro — bloco opcional.
export async function buscarSimilaresIVM(codigoIbge: string): Promise<RespostaIVMSerie | null> {
  return pedirSilencioso<RespostaIVMSerie>(`/v1/ivm/${codigoIbge}/similares`);
}

// --------------------------------------------------------------------------- Produtos por território

export async function buscarPulso(codigoIbge: string): Promise<PulsoProduto | null> {
  return pedirOuNull<PulsoProduto>(`/v1/pulso-produtivo/${codigoIbge}`, "o Pulso Produtivo");
}

export async function buscarRegiaoEmprega(
  codigoIbge: string,
): Promise<RegiaoEmpregaProduto | null> {
  return pedirOuNull<RegiaoEmpregaProduto>(`/v1/regiao-emprega/${codigoIbge}`, "Região Emprega");
}

export async function buscarSalarioRadar(codigoIbge: string): Promise<SalarioRadarProduto | null> {
  return pedirOuNull<SalarioRadarProduto>(`/v1/salario-radar/${codigoIbge}`, "Salário Radar");
}

export async function buscarGiroLocal(codigoIbge: string): Promise<GiroLocalProduto | null> {
  return pedirOuNull<GiroLocalProduto>(`/v1/giro-local/${codigoIbge}`, "Giro Local");
}

// Diretório do OndeFoi (lista de municípios). Degrada para null em erro — a tela mostra o vazio.
export async function buscarListaOndeFoi(): Promise<OndeFoiLista | null> {
  return pedirSilencioso<OndeFoiLista>("/v1/onde-foi");
}

export async function buscarOndeFoi(codigoIbge: string): Promise<OndeFoiProduto | null> {
  return pedirOuNull<OndeFoiProduto>(`/v1/onde-foi/${codigoIbge}`, "o OndeFoi");
}

export async function buscarBussolaEduTrab(
  codigoIbge: string,
): Promise<BussolaEduTrabProduto | null> {
  return pedirOuNull<BussolaEduTrabProduto>(
    `/v1/bussola-edu-trabalho/${codigoIbge}`,
    "a Bússola Educação-Trabalho",
  );
}

export async function buscarSentinelaResp(
  codigoIbge: string,
): Promise<SentinelaRespProduto | null> {
  return pedirOuNull<SentinelaRespProduto>(
    `/v1/sentinela-resp/${codigoIbge}`,
    "a Sentinela Respiratória",
  );
}

export async function buscarRadarEvasao(codigoIbge: string): Promise<RadarEvasaoProduto | null> {
  return pedirOuNull<RadarEvasaoProduto>(`/v1/radar-evasao/${codigoIbge}`, "o Radar de Evasão");
}

export async function buscarObraViva(codigoIbge: string): Promise<ObraVivaProduto | null> {
  return pedirOuNull<ObraVivaProduto>(`/v1/obra-viva/${codigoIbge}`, "o ObraViva");
}

// --------------------------------------------------------------------------- Território / panorama

export async function buscarTerritorios(q: string): Promise<RespostaBuscaTerritorios> {
  // Busca interativa (no-store): cada tecla é uma consulta nova. Degrada para vazio.
  const resp = await pedirSilencioso<RespostaBuscaTerritorios>("/v1/territorios", "no-store", {
    q,
    limit: "20",
  });
  return resp ?? { dados: [], total: 0 };
}

export async function buscarPanorama(codigoIbge: string): Promise<Panorama | null> {
  return pedirOuNull<Panorama>(`/v1/territorios/${codigoIbge}/panorama`, "o panorama");
}

export async function buscarCuriosidades(
  codigoIbge: string,
): Promise<CuriosidadesResposta | null> {
  return pedirOuNull<CuriosidadesResposta>(
    `/v1/territorios/${codigoIbge}/curiosidades`,
    "curiosidades",
  );
}

// Ficha técnica de um indicador. 404 → null (a tela responde com notFound).
export async function buscarIndicador(codigo: string): Promise<IndicadorDetalhe | null> {
  return pedirOuNull<IndicadorDetalhe>(
    `/v1/indicadores/${encodeURIComponent(codigo)}`,
    "o indicador",
  );
}

// Série de um indicador num território (drill-down do panorama). 404/erro → null.
export async function buscarValores(
  indicador: string,
  territorio: string,
): Promise<RespostaValores | null> {
  return pedirSilencioso<RespostaValores>("/v1/valores", "revalidate", { indicador, territorio });
}

// Fontes do acervo (proveniência consolidada). Degrada para null em erro — a tela mostra o vazio.
export async function buscarFontes(): Promise<RespostaFontes | null> {
  return pedirSilencioso<RespostaFontes>("/v1/fontes");
}

// --------------------------------------------------------------------------- IA ancorada

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

// --------------------------------------------------------------------------- Saúde / saneamento / função
// no-store: após ingestão o pipeline invalida o cache Redis do backend e a tela reflete na hora.

export async function buscarAguaViva(codigo: string): Promise<AguaVivaResponse | null> {
  return pedirOuNull<AguaVivaResponse>(`/v1/agua-viva/${codigo}`, "AguaViva", "no-store");
}

export async function buscarLuzNoMapa(codigo: string): Promise<LuzNoMapaResponse | null> {
  return pedirOuNull<LuzNoMapaResponse>(`/v1/luz-no-mapa/${codigo}`, "LuzNoMapa", "no-store");
}

export async function buscarRioEmRisco(codigo: string): Promise<RioEmRiscoResponse | null> {
  return pedirOuNull<RioEmRiscoResponse>(`/v1/rio-em-risco/${codigo}`, "RioEmRisco", "no-store");
}

export async function buscarEsgotoInvisivel(
  codigo: string,
): Promise<EsgotoInvisivelResponse | null> {
  return pedirOuNull<EsgotoInvisivelResponse>(
    `/v1/esgoto-invisivel/${codigo}`,
    "EsgotoInvisivel",
    "no-store",
  );
}

export async function buscarPratoFrio(codigo: string): Promise<PratoFrioResponse | null> {
  return pedirOuNull<PratoFrioResponse>(`/v1/prato-frio/${codigo}`, "PratoFrio", "no-store");
}

export async function buscarSemeandoTransparencia(
  codigo: string,
): Promise<SemeandoTransparenciaResponse | null> {
  return pedirOuNull<SemeandoTransparenciaResponse>(
    `/v1/semeando-transparencia/${codigo}`,
    "SemeandoTransparencia",
    "no-store",
  );
}

export async function buscarFomeOculta(codigo: string): Promise<FomeOcultaResponse | null> {
  return pedirOuNull<FomeOcultaResponse>(`/v1/fome-oculta/${codigo}`, "FomeOculta", "no-store");
}

export async function buscarSentinelaMaterna(
  codigo: string,
): Promise<SentinelaMaternaResponse | null> {
  return pedirOuNull<SentinelaMaternaResponse>(
    `/v1/sentinela-materna/${codigo}`,
    "SentinelaMaterna",
    "no-store",
  );
}

export async function buscarCacadorArboviroses(
  codigo: string,
): Promise<CacadorArboviroesResponse | null> {
  return pedirOuNull<CacadorArboviroesResponse>(
    `/v1/cacador-arboviroses/${codigo}`,
    "CacadorArboviroses",
    "no-store",
  );
}

export async function buscarPressaoSus(codigo: string): Promise<PressaoSusResponse | null> {
  return pedirOuNull<PressaoSusResponse>(`/v1/pressao-sus/${codigo}`, "PressaoSus", "no-store");
}

export async function buscarCasaViva(codigo: string): Promise<CasaVivaResponse | null> {
  return pedirOuNull<CasaVivaResponse>(`/v1/casa-viva/${codigo}`, "CasaViva", "no-store");
}

export async function buscarViaViva(codigo: string): Promise<ViaVivaResponse | null> {
  return pedirOuNull<ViaVivaResponse>(`/v1/via-viva/${codigo}`, "ViaViva", "no-store");
}

export async function buscarEcoVivo(codigo: string): Promise<EcoVivaResponse | null> {
  return pedirOuNull<EcoVivaResponse>(`/v1/eco-vivo/${codigo}`, "EcoVivo", "no-store");
}

export async function buscarEscolaViva(codigo: string): Promise<EscolaVivaResponse | null> {
  return pedirOuNull<EscolaVivaResponse>(`/v1/escola-viva/${codigo}`, "EscolaViva", "no-store");
}

export async function buscarSaneFundo(codigo: string): Promise<SaneFundoResponse | null> {
  return pedirOuNull<SaneFundoResponse>(`/v1/sane-fundo/${codigo}`, "SaneFundo", "no-store");
}

export async function buscarAssisViva(codigo: string): Promise<AssisVivaResponse | null> {
  return pedirOuNull<AssisVivaResponse>(`/v1/assis-viva/${codigo}`, "AssisViva", "no-store");
}

export async function buscarCulturaViva(codigo: string): Promise<CulturaVivaResponse | null> {
  return pedirOuNull<CulturaVivaResponse>(`/v1/cultura-viva/${codigo}`, "CulturaViva", "no-store");
}

export async function buscarSegurancaViva(codigo: string): Promise<SegurancaVivaResponse | null> {
  return pedirOuNull<SegurancaVivaResponse>(
    `/v1/seguranca-viva/${codigo}`,
    "SegurancaViva",
    "no-store",
  );
}

export async function buscarCidadeViva(codigo: string): Promise<CidadeVivaResponse | null> {
  return pedirOuNull<CidadeVivaResponse>(`/v1/cidade-viva/${codigo}`, "CidadeViva", "no-store");
}

// --------------------------------------------------------------------------- Analytics inferencial

export async function buscarPerfilOrcamentario(
  codigo: string,
): Promise<PerfilOrcamentarioResponse | null> {
  return pedirOuNull<PerfilOrcamentarioResponse>(
    `/v1/inferencia/municipio/${codigo}/orcamento`,
    "PerfilOrcamentario",
    "no-store",
  );
}

export async function buscarDistribuicaoFuncao(
  funcaoCod: string,
): Promise<DistribuicaoFuncaoResponse | null> {
  return pedirOuNull<DistribuicaoFuncaoResponse>(
    `/v1/inferencia/distribuicao-funcao/${funcaoCod}`,
    "DistribuicaoFuncao",
    "no-store",
  );
}

// --------------------------------------------------------------------------- Cobertura (flag-demo)
// no-store: a cobertura reflete a última ingestão; o backend (Redis 300 s) absorve o custo.

export async function buscarCoberturaCAGED(): Promise<CoberturaCAGED | null> {
  return pedirSilencioso<CoberturaCAGED>("/v1/cobertura/caged", "no-store");
}

export async function buscarCoberturaSnis(): Promise<CoberturaSnis | null> {
  return pedirSilencioso<CoberturaSnis>("/v1/cobertura/snis", "no-store");
}

export async function buscarCoberturaDatasus(): Promise<CoberturaDatasus | null> {
  return pedirSilencioso<CoberturaDatasus>("/v1/cobertura/datasus", "no-store");
}

export async function buscarCoberturaInep(): Promise<CoberturaInep | null> {
  return pedirSilencioso<CoberturaInep>("/v1/cobertura/inep", "no-store");
}

export async function buscarCoberturaPncp(): Promise<CoberturaPncp | null> {
  return pedirSilencioso<CoberturaPncp>("/v1/cobertura/pncp", "no-store");
}

export async function buscarCoberturaSiconfi(): Promise<CoberturaSiconfi | null> {
  return pedirSilencioso<CoberturaSiconfi>("/v1/cobertura/siconfi", "no-store");
}

// --------------------------------------------------------------------------- Tier profundo (quota)

// Uso da cota de uma chave de API (GET /v1/quota, lê sem debitar). A chave é SEGREDO — esta função
// roda só no servidor (Server Action / RSC), nunca embarca no bundle do cliente. Sem chave válida
// (401/403/404/erro) → null, e a tela mostra o estado honesto.
export async function consultarQuota(chave: string): Promise<RespostaQuota | null> {
  return pedirSilencioso<RespostaQuota>("/v1/quota", "no-store", undefined, {
    Authorization: `Bearer ${chave}`,
  });
}
