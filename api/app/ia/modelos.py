"""Modelos da IA ancorada (§9): resposta com citações e ressalvas; sem dado, abstém-se."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PerguntaIA(BaseModel):
    pergunta: str = Field(min_length=1, max_length=1000)
    indicador: str | None = Field(default=None, description="código do indicador (opcional)")
    territorio: str | None = Field(default=None, description="codigo_ibge (opcional)")
    de: str | None = Field(default=None, description="período inicial YYYY-MM")
    ate: str | None = Field(default=None, description="período final YYYY-MM")


class Citacao(BaseModel):
    indicador: str
    nome: str
    fonte: str
    metodologia: str
    periodo_de: str | None = None
    periodo_ate: str | None = None
    lag_tipico_dias: int | None = None


class RespostaIA(BaseModel):
    resposta: str
    abstencao: bool
    citacoes: list[Citacao]
    ressalvas: list[str]
    revisao_humana: bool
    narrador: str  # model card: identifica o narrador usado
