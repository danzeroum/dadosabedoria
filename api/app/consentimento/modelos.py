"""Modelos do serviço de consentimento. A condição sensível nunca volta em claro na resposta."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class RespostaLogin(BaseModel):
    autenticado: bool
    sub: str  # contato_hash (pseudônimo); o e-mail bruto nunca é guardado


class AlertaIn(BaseModel):
    territorio: str = Field(description="codigo_ibge do território do alerta")
    finalidade: str = Field(min_length=2, max_length=80, examples=["alerta_qualidade_ar"])
    condicao_sensivel: str | None = Field(default=None, max_length=80, examples=["asma"])


class AlertaOut(BaseModel):
    id: int
    territorio: str
    finalidade: str
    consentido_em: str
    condicao_sensivel: bool  # apenas se há condição associada — nunca expõe o valor


class NotificacaoOut(BaseModel):
    """Notificação de alerta entregue ao cidadão (pull). Carrega proveniência (invariante 5)."""

    id: int
    territorio: str
    periodo: str
    ivm: float
    semaforo: str
    fonte: str
    metodologia: str
    criada_em: str
    lida: bool
