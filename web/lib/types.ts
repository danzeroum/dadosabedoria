// Espelha os modelos de resposta da API (/v1/ivm).

export type Semaforo = "verde" | "amarelo" | "vermelho";

export type ExeEstado = "valor" | "suprimido" | "sem_cobertura";

export interface IVMItem {
  codigo_ibge: string;
  nome: string;
  periodo: string; // YYYY-MM
  ivm: number; // 0..100, maior = mais vulnerável
  semaforo: Semaforo;
  v_emprego: number;
  v_financas: number;
  v_saude: number | null; // subíndice de saúde (null onde não há dado não suprimido)
  v_saude_estado: ExeEstado; // valor | suprimido (privacidade) | sem_cobertura
}

export interface MetaIVM {
  indicador: string;
  nome: string;
  metodologia: string;
  versao_metodologia: string;
  componentes: string[];
  semaforo: Record<string, string>;
  periodo: string | null;
}

export interface Paginacao {
  pagina: number;
  por_pagina: number;
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

// ----------------------------------------------------------------- OndeFoi (TRANSP-06)

export type Banda = "alta" | "parcial" | "baixa" | "indef";

export interface FuncaoOut {
  funcao: string;
  recebido: number;
  exe: number | null; // null onde exe_estado != "valor"
  exe_estado: ExeEstado; // no OndeFoi: "valor" | "sem_cobertura" (orçamento público, sem cadeado)
  pct: number | null;
}

export interface FonteOut {
  sigla: string;
  orgao: string;
  ate: string;
}

export interface MetaOndeFoi {
  metodologia: string; // "execução orçamentária, NÃO serviço entregue"
  versao_metodologia: string;
  periodo: string;
  periodo_rotulo: string; // "exercício 2025" — selo de frescor
  atraso_dias: number;
  fontes: FonteOut[];
}

export interface OndeFoiProduto {
  codigo_ibge: string;
  nome: string;
  uf: string;
  recebido_total: number; // contexto — nunca o denominador
  recebido_base: number; // denominador do %
  recebido_fora_base: number; // explícito: total − base
  executado: number;
  pct: number;
  banda: Banda;
  funcoes: FuncaoOut[];
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
