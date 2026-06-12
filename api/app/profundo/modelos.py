"""Modelos do tier profundo — consulta em lote (reusa os tipos da leitura pública)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.indicadores.modelos import MetaProveniencia, Paginacao, ValorOut

LOTE_MAX = 50  # teto do lote (economia/abuso): clientes pagos paginam grandes volumes em chamadas


class ConsultaItem(BaseModel):
    indicador: str = Field(description="código namespaced do indicador (obrigatório)")
    territorio: str | None = Field(default=None, description="codigo_ibge do território")
    de: str | None = Field(default=None, description="período inicial YYYY-MM")
    ate: str | None = Field(default=None, description="período final YYYY-MM")
    por_pagina: int = Field(default=100, ge=1, le=1000)


class ConsultaLoteIn(BaseModel):
    consultas: list[ConsultaItem] = Field(min_length=1, max_length=LOTE_MAX)


class ResultadoLote(BaseModel):
    indicador: str
    territorio: str | None = None
    dados: list[ValorOut] | None = None
    meta: MetaProveniencia | None = None
    paginacao: Paginacao | None = None
    erro: str | None = None  # preenchido se ESTA consulta falhou — não derruba o lote inteiro


class RespostaLote(BaseModel):
    resultados: list[ResultadoLote]
    total: int


class RespostaQuota(BaseModel):
    """Uso atual da cota de API do cliente na janela em curso (sem incrementar o contador)."""

    limite: int
    usado: int
    restante: int
    reset: int = Field(description="Unix timestamp da próxima janela (hora cheia)")
