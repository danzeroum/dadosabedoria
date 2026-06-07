"""Modelos Pydantic v2 da API de leitura — com o envelope ``meta`` de proveniência (§7)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MetaProveniencia(BaseModel):
    """Proveniência exigida em toda resposta (invariante 5)."""

    indicador: str
    nome: str
    fonte: str
    metodologia: str
    lag_tipico_dias: int | None = None
    licenca: str


class Paginacao(BaseModel):
    pagina: int
    por_pagina: int
    total: int


class ValorOut(BaseModel):
    periodo: str = Field(examples=["2026-04"])  # YYYY-MM
    valor: float | None  # None quando suprimido
    confiabilidade: int | None = None
    suprimido: bool = False
    motivo_supressao: str | None = None


class RespostaValores(BaseModel):
    dados: list[ValorOut]
    meta: MetaProveniencia
    paginacao: Paginacao


class IndicadorOut(BaseModel):
    codigo: str
    nome: str
    descricao: str
    dominio: str
    subdominio: str
    unidade: str
    polaridade: str
    atualizacao: str
    nivel_minimo_agregacao: str
    metodologia: str
    versao_metodologia: str
    meta: MetaProveniencia


class RespostaIndicadores(BaseModel):
    dados: list[IndicadorOut]
    paginacao: Paginacao


class TerritorioRef(BaseModel):
    codigo_ibge: str
    nome: str
    nivel: str


class TerritorioOut(BaseModel):
    codigo_ibge: str
    nome: str
    nivel: str
    uf: str | None = None
    populacao: int | None = None
    pai: TerritorioRef | None = None


class ErroOut(BaseModel):
    """Envelope de erro padronizado (§7)."""

    erro: str = Field(examples=["validacao", "nao_encontrado", "rate_limit", "interno"])
    mensagem: str
    doc_url: str
    trace_id: str


# ----------------------------------------------------------------------- IVM (índice composto)


class MetaIVM(BaseModel):
    """Proveniência do IVM — índice composto, não vem de uma fonte única."""

    indicador: str
    nome: str
    metodologia: str
    versao_metodologia: str
    componentes: list[str]
    semaforo: dict[str, str]
    periodo: str | None = None


class IVMItem(BaseModel):
    codigo_ibge: str
    nome: str
    periodo: str  # YYYY-MM
    ivm: float  # 0..100, maior = mais vulnerável
    semaforo: str  # verde | amarelo | vermelho
    v_emprego: float
    v_financas: float
    v_saude: float | None = None  # subíndice de saúde (None onde não há dado não suprimido)
    # padrão *_estado (ADR-0026): distingue null-por-supressão (k-anon) de null-por-cobertura.
    v_saude_estado: Literal["valor", "suprimido", "sem_cobertura"] = "sem_cobertura"


class RespostaIVM(BaseModel):
    dados: list[IVMItem]
    meta: MetaIVM
    paginacao: Paginacao


class RespostaIVMSerie(BaseModel):
    dados: list[IVMItem]
    meta: MetaIVM
