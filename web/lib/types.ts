// Espelha os modelos de resposta da API (/v1/ivm).

export type Semaforo = "verde" | "amarelo" | "vermelho";

export type ExeEstado = "valor" | "suprimido" | "sem_cobertura";

export interface IVMItem {
  codigo_ibge: string;
  nome: string;
  uf?: string | null;
  periodo: string; // YYYY-MM
  ivm: number; // 0..100, maior = mais vulnerável
  semaforo: Semaforo;
  v_emprego: number;
  v_financas: number;
  v_saude: number | null; // subíndice de saúde (null onde não há dado não suprimido)
  v_saude_estado: ExeEstado; // valor | suprimido (privacidade) | sem_cobertura
}

// MetaIVM reusa o contrato do selo de confiança (SeloMeta: fontes/frescor/licença) — primitivo
// compartilhado com o OndeFoi, sem forkar. Acrescenta os campos próprios do índice composto.
export interface MetaIVM extends SeloMeta {
  indicador: string;
  nome: string;
  metodologia: string;
  componentes: string[];
  semaforo: Record<string, string>;
  periodo: string | null;
}

export interface Paginacao {
  pagina: number;
  por_pagina: number;
  total: number;
}

export interface TerritorioSimples {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
}

export interface RespostaBuscaTerritorios {
  dados: TerritorioSimples[];
  total: number;
}

export interface RespostaIVM {
  dados: IVMItem[];
  meta: MetaIVM;
  paginacao: Paginacao;
}

export interface RespostaIVMSerie {
  dados: IVMItem[];
  meta: MetaIVM;
}

// ----------------------------------------------------------------- Pulso Produtivo (TRAB-01)

export type Pulso = "aquecido" | "estavel" | "esfriando";
export type Tendencia = "melhorando" | "estavel" | "piorando";

export interface MesSaldo {
  periodo: string; // YYYY-MM
  saldo: number;
}

export interface MetaProveniencia {
  indicador: string;
  nome: string;
  fonte: string;
  metodologia: string;
  lag_tipico_dias: number | null;
  licenca: string;
}

// Série de um indicador num território (/v1/valores) — valores por período, supressão honesta.
export interface ValorSerie {
  periodo: string; // YYYY-MM
  valor: number | null; // null quando suprimido
  confiabilidade: number | null;
  suprimido: boolean;
  motivo_supressao: string | null;
}

export interface RespostaValores {
  dados: ValorSerie[];
  meta: MetaProveniencia;
  paginacao: Paginacao;
}

// Ficha técnica de um indicador (/v1/indicadores/{codigo}) — metodologia + proveniência completas.
export interface IndicadorDetalhe {
  codigo: string;
  nome: string;
  descricao: string;
  dominio: string;
  subdominio: string;
  unidade: string;
  polaridade: string;
  atualizacao: string;
  nivel_minimo_agregacao: string;
  metodologia: string;
  versao_metodologia: string;
  meta: MetaProveniencia;
}

export interface PulsoProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  periodo: string; // YYYY-MM (último mês)
  saldo_mes: number; // a batida atual
  saldo_acumulado: number; // soma da janela (contexto, não veredito)
  pulso: Pulso;
  tendencia: Tendencia | null; // null com 1 só mês
  meses_positivos: number;
  meses_negativos: number;
  meses: MesSaldo[];
  nota: string; // enquadramento honesto (formal, fluxo volátil, merece a pergunta)
  meta: MetaProveniencia;
}

// ----------------------------------------------------------------- Giro Local (TRAB-03)

export type NivelEmprego = "criando" | "estavel" | "reduzindo" | "sem_dado";
export type NivelCredito = "alto" | "medio" | "baixo" | "sem_dado";

export interface GiroLocalProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  // Emprego formal (CAGED)
  periodo_emprego: string | null;
  saldo_emprego: number | null;
  saldo_emprego_per_1000: number | null;
  nivel_emprego: NivelEmprego;
  // Crédito bancário (ESTBAN)
  periodo_credito: string | null;
  saldo_credito: number | null;
  saldo_credito_per_hab: number | null;
  nivel_credito: NivelCredito;
  nota: string;
  meta_emprego: MetaProveniencia | null;
  meta_credito: MetaProveniencia | null;
}

// ----------------------------------------------------------------- OndeFoi (TRANSP-06)

export type Banda = "alta" | "parcial" | "baixa" | "indef";

export interface FuncaoOut {
  funcao: string;
  empenhado: number;
  liquidado: number | null; // null onde exe_estado != "valor"
  exe_estado: ExeEstado; // no OndeFoi: "valor" | "sem_cobertura" (orçamento público, sem cadeado)
  pct: number | null;
}

// Contrato do selo de confiança (primitivo compartilhado OndeFoi ↔ IVM).
export interface SeloFonte {
  sigla: string;
  nome: string;
  orgao: string;
  dominio: string;
  ate: string;
  atraso: string;
}

export interface SeloMeta {
  fontes: SeloFonte[];
  periodo_rotulo: string;
  atraso_dias: number;
  versao_metodologia: string;
  licenca: string;
}

export type FonteOut = SeloFonte;

export interface MetaOndeFoi extends SeloMeta {
  metodologia: string; // "execução orçamentária, NÃO serviço entregue"
  periodo: string;
}

export interface OndeFoiProduto {
  codigo_ibge: string;
  nome: string;
  uf: string;
  empenhado_total: number; // contexto — nunca o denominador
  empenhado_base: number; // denominador do %
  empenhado_fora_base: number; // explícito: total − base
  liquidado: number;
  pct: number;
  banda: Banda;
  funcoes: FuncaoOut[];
  meta: MetaOndeFoi;
}

// Diretório do OndeFoi (/v1/onde-foi): resumo por município, ordenado por NOME (não ranking).
export interface OndeFoiResumo {
  codigo_ibge: string;
  nome: string;
  uf: string;
  pct: number;
  banda: Banda;
}

export interface OndeFoiLista {
  dados: OndeFoiResumo[];
  meta: MetaOndeFoi;
}

// ----------------------------------------------------------------- Panorama do município

export interface IndicadorValor {
  codigo: string;
  nome: string;
  dominio: string;
  subdominio: string;
  unidade: string;
  polaridade: string;
  periodo: string; // YYYY-MM
  valor: number | null; // null quando suprimido
  suprimido: boolean;
  motivo_supressao: string | null;
  fonte: string;
  lag_tipico_dias: number | null;
  metodologia: string;
}

export interface Panorama {
  codigo_ibge: string;
  nome: string;
  nivel: string;
  uf: string | null;
  indicadores: IndicadorValor[];
}

// ----------------------------------------------------------------- IA ancorada (/v1/ia/perguntar)

export interface Citacao {
  indicador: string;
  nome: string;
  fonte: string;
  metodologia: string;
  periodo_de: string | null;
  periodo_ate: string | null;
  lag_tipico_dias: number | null;
}

export interface RespostaIA {
  resposta: string;
  abstencao: boolean;
  citacoes: Citacao[];
  ressalvas: string[];
  revisao_humana: boolean;
  narrador: string; // model card do narrador (ex.: "template" sem chave de LLM)
}

export interface PerguntaInput {
  pergunta: string;
  indicador?: string;
  territorio?: string;
  de?: string;
  ate?: string;
}

// ----------------------------------------------------------------- Região Emprega (TRAB-04)

export interface MunicipioEmpregoProduto {
  codigo_ibge: string;
  nome: string;
  populacao: number | null;
  saldo: number | null;
  per_1000: number | null;
  nivel: NivelEmprego;
}

export interface RegiaoEmpregaProduto {
  codigo_ibge: string;
  nome: string;
  uf: string;
  periodo: string | null;
  saldo_total: number;
  municipios_criando: number;
  municipios_estaveis: number;
  municipios_reduzindo: number;
  municipios_sem_dado: number;
  municipios_total: number;
  nivel: NivelEmprego; // reuse — mesmo literal
  municipios: MunicipioEmpregoProduto[];
  nota: string;
  meta: MetaProveniencia;
}

// ----------------------------------------------------------------- Salário Radar (TRAB-02)

export type NivelSalario = "alto" | "medio" | "baixo" | "sem_dado";

export interface SalarioRadarProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  periodo: string | null; // YYYY-MM
  salario_medio: number | null; // R$ médio das admissões; null se sem dado
  nivel: NivelSalario;
  nota: string;
  meta: MetaProveniencia;
}

// ----------------------------------------------------------------- Cobertura CAGED

export interface CoberturaCAGED {
  n_municipios: number;
  demo: boolean;
  aviso: string | null;
}

// ----------------------------------------------------------------- Cobertura SNIS

export interface CoberturaSnis {
  n_municipios: number;
  demo: boolean;
  aviso: string | null;
}

// ----------------------------------------------------------------- Cobertura DATASUS

export interface CoberturaDatasus {
  n_municipios: number;
  demo: boolean;
  aviso: string | null;
}

// ----------------------------------------------------------------- Cobertura INEP

export interface CoberturaInep {
  n_municipios: number;
  demo: boolean;
  aviso: string | null;
}

export interface CoberturaPncp {
  n_municipios: number;
  demo: boolean;
  aviso: string | null;
}

export interface CoberturaSiconfi {
  n_municipios: number;
  demo: boolean;
  aviso: string | null;
}

// ----------------------------------------------------------------- Bússola Educação-Trabalho (EDU-01)

export type NivelEducacao = "alto" | "medio" | "baixo" | "sem_dado";

export interface BussolaEduTrabProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  // Educação (INEP — anual)
  periodo_educacao: string | null; // YYYY
  matriculas: number | null;
  matriculas_por_mil: number | null;
  nivel_educacao: NivelEducacao;
  // Emprego formal (CAGED — mensal)
  periodo_emprego: string | null; // YYYY-MM
  saldo_emprego: number | null;
  nivel_emprego: NivelEmprego;
  // Salário médio das admissões (CAGED — mensal)
  salario_medio: number | null;
  nivel_salario: NivelSalario;
  nota: string;
  meta_educacao: MetaProveniencia | null;
  meta_emprego: MetaProveniencia | null;
  meta_salario: MetaProveniencia | null;
}

// ---------------------------------------------- Sentinela Respiratória (SAUDE-01)

export type NivelSentinela = "elevado" | "moderado" | "baixo" | "suprimido" | "sem_dado";
export type TendenciaSentinela = "subindo" | "estavel" | "caindo";

export interface MesInternacoesProduto {
  periodo: string; // YYYY-MM
  internacoes: number | null; // null quando suprimido (k-anonimato)
  suprimido: boolean;
}

export interface SentinelaRespProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  periodo: string | null; // YYYY-MM do dado mais recente
  internacoes: number | null; // null se suprimido ou sem dado
  internacoes_por_100k: number | null; // null se suprimido ou sem população
  suprimido: boolean;
  nivel: NivelSentinela;
  tendencia: TendenciaSentinela | null; // null com < 2 meses reais
  meses: MesInternacoesProduto[]; // série histórica (inclui meses suprimidos)
  nota: string;
  meta: MetaProveniencia | null;
}

// GeoJSON do IVM (/v1/mapa/ivm) para a coropleta.
export type GeometriaGeoJSON =
  | { type: "Polygon"; coordinates: number[][][] }
  | { type: "MultiPolygon"; coordinates: number[][][][] };

export interface PropriedadesIVM {
  codigo_ibge: string;
  nome: string;
  ivm: number | null;
  semaforo: Semaforo | null;
  v_emprego: number | null;
  v_financas: number | null;
  v_saude: number | null;
  v_saude_estado: ExeEstado;
}

export interface FeatureIVM {
  type: "Feature";
  geometry: GeometriaGeoJSON | null;
  properties: PropriedadesIVM;
}

export interface FeatureCollectionIVM {
  type: "FeatureCollection";
  features: FeatureIVM[];
}

// Fontes do acervo (/v1/fontes) — proveniência consolidada: a confiança tornada verificável.
export interface FonteAcervo {
  codigo: string;
  nome: string;
  orgao: string;
  url_doc: string | null;
  licenca: string;
  atualizacao: string; // cadência: diaria..irregular
  lag_tipico_dias: number | null;
  permite_uso_comercial: boolean;
  permite_redistribuicao: boolean;
  base_legal_artigo: string;
  base_legal_hipotese: string;
  dominios: string[];
  n_indicadores: number;
}

export interface RespostaFontes {
  dados: FonteAcervo[];
  total: number;
}

// ----------------------------------------------------------------- Radar de Evasão (EDU-02)

export type NivelEvasao = "adequada" | "atencao" | "alerta" | "sem_dado";

export interface RadarEvasaoProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  periodo: string | null; // YYYY do Censo Escolar
  matriculas: number | null;
  matriculas_por_mil: number | null;
  populacao_escolar_estimada: number | null; // populacao × 0,14
  taxa_cobertura: number | null; // %
  nivel: NivelEvasao;
  nota: string;
  meta: MetaProveniencia | null;
}

// ----------------------------------------------------------------- ObraViva (TRANSP-05)

export type NivelContratos = "elevado" | "moderado" | "baixo" | "sem_dado";

export interface ObraVivaProduto {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  periodo: string | null; // YYYY
  valor_contratos: number | null; // R$ total dos contratos
  valor_por_hab: number | null; // R$/hab
  nivel: NivelContratos;
  nota: string;
  meta: MetaProveniencia | null;
}

// ----------------------------------------------------------------- AguaViva (SANE-01)

export type NivelAcesso = "adequado" | "atencao" | "alerta" | "sem_dado";

export interface AguaVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  periodo: string | null;
  agua_pct: number | null;
  esgoto_pct: number | null;
  nivel_agua: NivelAcesso;
  nivel_esgoto: NivelAcesso;
  nota: string;
  meta_agua: MetaProveniencia | null;
  meta_esgoto: MetaProveniencia | null;
}

// ----------------------------------------------------------------- EsgotoInvisível (SANE-03)

export type NivelGap = "adequado" | "atencao" | "critico" | "sem_dado";

export interface EsgotoInvisivelResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  periodo: string | null;
  agua_pct: number | null;
  esgoto_pct: number | null;
  gap_pct: number | null;
  nivel_gap: NivelGap;
  nota: string;
  meta_esgoto: MetaProveniencia | null;
  meta_agua: MetaProveniencia | null;
}

// ----------------------------------------------------------------- LuzNoMapa (SANE-04)

export type NivelEnergia = "confiavel" | "regular" | "fragil" | "sem_dado";

export interface LuzNoMapaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  periodo: string | null;
  dec: number | null;   // horas de interrupção por consumidor/ano
  fec: number | null;   // interrupções por consumidor/ano
  nivel_dec: NivelEnergia;
  nivel_fec: NivelEnergia;
  nota: string;
  meta_dec: MetaProveniencia | null;
  meta_fec: MetaProveniencia | null;
}

// ----------------------------------------------------------------- RioEmRisco (SANE-02)

export type NivelSeca = "normal" | "atencao" | "critico" | "sem_dado";

export interface RioEmRiscoResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  periodo: string | null;
  seca_indice: number | null;  // 0–5: Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5
  nivel: NivelSeca;
  nota: string;
  meta: MetaProveniencia | null;
}

// ----------------------------------------------------------------- PratoFrio (ALIM-01)

export type NivelProducao = "alta" | "moderada" | "baixa" | "sem_dado";

export interface PratoFrioResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  periodo: string | null;  // YYYY do exercício
  valor_total: number | null;  // BRL total (soma das lavouras)
  valor_por_hab: number | null;  // BRL/hab/ano
  nivel: NivelProducao;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------ SemeandoTransparencia (ALIM-05)

export type NivelInvestimento = "alto" | "moderado" | "baixo" | "sem_dado";

export interface SemeandoTransparenciaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;  // BRL — função 20 liquidado total
  valor_por_hab: number | null;    // BRL/hab/ano
  nivel: NivelInvestimento;
  nota: string;
  meta: MetaProveniencia | null;
}

export type NivelFomeOculta = "crítico" | "elevado" | "moderado" | "baixo" | "sem_dado";

export interface FomeOcultaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  n_acompanhadas: number | null;
  baixo_peso_pct: number | null;
  nivel: NivelFomeOculta;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------ SentinelaMaterna (SAUDE-03)

export type NivelMaterno = "crítico" | "elevado" | "moderado" | "baixo" | "sem_dado";

export interface SentinelaMaternаResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  n_gestantes: number | null;
  gestante_baixo_peso_pct: number | null;
  nivel: NivelMaterno;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- CaçadorArboviroses (SAUDE-02)

export type NivelArboviroses = "crítico" | "elevado" | "moderado" | "baixo" | "sem_dado";

export interface CacadorArboviroesResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  casos_confirmados: number | null;
  incidencia_100k: number | null;
  nivel: NivelArboviroses;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- PressaoSus (SAUDE-11)

export type NivelPressaoSus = "adequado" | "atenção" | "crítico" | "sem_dado";

export interface PressaoSusResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelPressaoSus;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- CasaViva (HAB-02)

export type NivelHabitacao = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface CasaVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelHabitacao;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- ViaViva (MOB-01)

export type NivelTransporte = "elevado" | "moderado" | "baixo" | "sem_dado";

export interface ViaVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelTransporte;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- EcoVivo (AMB-01)

export type NivelAmbiental = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface EcoVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelAmbiental;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- EscolaViva (EDU-03)

export type NivelEducacaoPublica = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface EscolaVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelEducacaoPublica;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- SaneFundo (SANE-05)

export type NivelSaneamento = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface SaneFundoResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelSaneamento;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- SegurançaViva (SEG-01)

export type NivelSeguranca = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface SegurancaVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelSeguranca;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- CidadeViva (URB-01)

export type NivelUrbanismo = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface CidadeVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelUrbanismo;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- AssisViva (SOCIAL-01)

export type NivelAssistencia = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface AssisVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelAssistencia;
  nota: string;
  meta: MetaProveniencia | null;
}

// ------------------------------------------------- CulturaViva (CULT-01)

export type NivelCultura = "expressivo" | "moderado" | "incipiente" | "sem_dado";

export interface CulturaVivaResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  nivel: NivelCultura;
  nota: string;
  meta: MetaProveniencia | null;
}

// ---------------------------------------- Analytics Inferencial (perfil orçamentário)

export interface FuncaoPerfilItem {
  funcao_cod: string;
  funcao_nome: string;
  valor_liquidado: number | null;
  valor_por_hab: number | null;
  percentil: number | null;  // 0–100; null quando município não tem dado na função
}

export interface PerfilOrcamentarioResponse {
  codigo_ibge: string;
  nome: string;
  uf: string | null;
  populacao: number | null;
  ano: number | null;
  funcoes: FuncaoPerfilItem[];
  nota: string;
}

export interface DistribuicaoFuncaoResponse {
  funcao_cod: string;
  funcao_nome: string;
  ano: number | null;
  n_municipios: number;
  media_brl_hab: number | null;
  mediana_brl_hab: number | null;
  desvio_padrao: number | null;
  p10: number | null;
  p25: number | null;
  p75: number | null;
  p90: number | null;
  minimo: number | null;
  maximo: number | null;
}
