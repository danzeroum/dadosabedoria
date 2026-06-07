"""Modelos Pydantic do contrato do OndeFoi (ADR-0026) — resposta de ``/v1/onde-foi/{ibge}``."""

from __future__ import annotations

from pydantic import BaseModel

from app.produtos.onde_foi import Banda, ExeEstado


class FuncaoOut(BaseModel):
    funcao: str
    recebido: int
    exe: int | None  # None onde exe_estado != "valor"
    exe_estado: ExeEstado
    pct: int | None


class FonteOut(BaseModel):
    sigla: str
    orgao: str
    ate: str


class MetaOndeFoi(BaseModel):
    metodologia: str  # "execução orçamentária, NÃO serviço entregue" (ADR-0026)
    versao_metodologia: str
    periodo: str
    periodo_rotulo: str  # "exercício X" — selo de frescor derivado daqui (não hardcoded)
    atraso_dias: int
    fontes: list[FonteOut]


class OndeFoiOut(BaseModel):
    """Recebido × execução por função. % sobre a base divulgada; parcela fora explícita."""

    codigo_ibge: str
    nome: str
    uf: str
    recebido_total: int  # contexto — nunca o denominador
    recebido_base: int  # denominador do %
    recebido_fora_base: int  # explícito: total − base
    executado: int
    pct: int
    banda: Banda
    funcoes: list[FuncaoOut]
    meta: MetaOndeFoi
