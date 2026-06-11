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
