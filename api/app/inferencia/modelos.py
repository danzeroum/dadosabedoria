"""Modelos Pydantic para analytics inferencial."""

from __future__ import annotations

from pydantic import BaseModel


class DistribuicaoFuncaoOut(BaseModel):
    """Distribuição nacional de investimento per capita em uma função SICONFI."""

    funcao_cod: str
    funcao_nome: str
    ano: int | None
    n_municipios: int
    media_brl_hab: float | None
    mediana_brl_hab: float | None
    desvio_padrao: float | None
    p10: float | None
    p25: float | None
    p75: float | None
    p90: float | None
    minimo: float | None
    maximo: float | None


class FuncaoPerfilItem(BaseModel):
    """Gasto de uma função orçamentária com percentil nacional."""

    funcao_cod: str
    funcao_nome: str
    valor_liquidado: float | None
    valor_por_hab: float | None
    percentil: float | None  # 0–100; None quando município não tem dado na função


class PerfilOrcamentarioOut(BaseModel):
    """Perfil orçamentário completo de um município (todas as funções SICONFI)."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None
    ano: int | None
    funcoes: list[FuncaoPerfilItem]
    nota: str
