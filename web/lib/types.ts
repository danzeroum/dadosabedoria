// Espelha os modelos de resposta da API (/v1/ivm).

export type Semaforo = "verde" | "amarelo" | "vermelho";

export interface IVMItem {
  codigo_ibge: string;
  nome: string;
  periodo: string; // YYYY-MM
  ivm: number; // 0..100, maior = mais vulnerável
  semaforo: Semaforo;
  v_emprego: number;
  v_financas: number;
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
