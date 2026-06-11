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


class TerritorioSimples(BaseModel):
    codigo_ibge: str
    nome: str
    uf: str | None = None


class RespostaBuscaTerritorios(BaseModel):
    dados: list[TerritorioSimples]
    total: int


# ----------------------------------------- Panorama (todos os indicadores de um território)


class IndicadorValorOut(BaseModel):
    """Último valor de um indicador no território, com proveniência por indicador (multi-fonte)."""

    codigo: str
    nome: str
    dominio: str
    subdominio: str
    unidade: str
    polaridade: str
    periodo: str  # YYYY-MM do último dado
    valor: float | None  # None quando suprimido (a célula vira "protegido" na tela)
    suprimido: bool = False
    motivo_supressao: str | None = None
    fonte: str
    lag_tipico_dias: int | None = None
    metodologia: str


class PanoramaOut(BaseModel):
    """O que sabemos do município: o último valor de cada indicador público, com proveniência."""

    codigo_ibge: str
    nome: str
    nivel: str
    uf: str | None = None
    indicadores: list[IndicadorValorOut]


class ErroOut(BaseModel):
    """Envelope de erro padronizado (§7)."""

    erro: str = Field(examples=["validacao", "nao_encontrado", "rate_limit", "interno"])
    mensagem: str
    doc_url: str
    trace_id: str


# ----------------------------------------------------------------------- IVM (índice composto)


class FonteSelo(BaseModel):
    """Uma fonte no selo de confiança (primitivo compartilhado OndeFoi ↔ IVM)."""

    sigla: str
    nome: str
    orgao: str
    dominio: str
    ate: str
    atraso: str


class MetaIVM(BaseModel):
    """Proveniência do IVM — índice composto, não vem de uma fonte única."""

    indicador: str
    nome: str
    metodologia: str
    versao_metodologia: str
    componentes: list[str]
    semaforo: dict[str, str]
    periodo: str | None = None
    # Selo de confiança (compartilhado): proveniência rica por fonte + frescor (reuso na tela).
    fontes: list[FonteSelo] = Field(default_factory=list)
    periodo_rotulo: str | None = None
    atraso_dias: int = 60
    licenca: str = ""


class IVMItem(BaseModel):
    codigo_ibge: str
    nome: str
    uf: str | None = None
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


# ------------------------------------------------ Fontes (proveniência consolidada do acervo)


class FonteAcervoOut(BaseModel):
    """Uma fonte por trás dos números: órgão, licença, cadência, lag e base legal (LGPD).

    A transparência das fontes é o ativo "confiança" tornado verificável — não a promessa, o fato:
    estes campos vêm da tabela ``fonte``/``base_legal`` do acervo, não de texto fixo.
    """

    codigo: str
    nome: str
    orgao: str
    url_doc: str | None = None
    licenca: str
    atualizacao: str  # cadência (diaria..irregular)
    lag_tipico_dias: int | None = None
    permite_uso_comercial: bool
    permite_redistribuicao: bool
    base_legal_artigo: str
    base_legal_hipotese: str
    dominios: list[str]  # domínios públicos cobertos por esta fonte no acervo
    n_indicadores: int  # quantos indicadores públicos vêm dela


class RespostaFontes(BaseModel):
    dados: list[FonteAcervoOut]
    total: int


# ------------------------------------------------ Cobertura / modo demonstração


class CoberturaCAGED(BaseModel):
    """Cobertura atual do CAGED no acervo — detecta modo demonstração automaticamente.

    ``demo=true`` quando há menos de 50 municípios (seed de teste vs. ~5.500 nacional).
    O rótulo cai sozinho após a ingestão nacional; não é hardcode.
    """

    n_municipios: int
    demo: bool
    aviso: str | None = None
