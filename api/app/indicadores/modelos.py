"""Modelos Pydantic v2 da API de leitura — com o envelope ``meta`` de proveniência (§7)."""

from __future__ import annotations

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
