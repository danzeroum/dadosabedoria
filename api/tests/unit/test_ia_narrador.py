"""Unidade do narrador: factory por config + NarradorLLM com HTTP mockado (sem rede).

Garante o invariante 3 no provedor real: a resposta com número inventado e a falha do provedor
caem para o narrador template (determinístico, ancorado).
"""

from __future__ import annotations

from datetime import date

import httpx

from app.core.config import Settings
from app.ia import narrador as N
from app.ia.recuperacao import ContextoIA


def _contexto() -> ContextoIA:
    indicador = {"nome": "Saldo de empregos formais", "fonte_nome": "Novo CAGED"}
    valores = [
        {"periodo": date(2026, 2, 1), "valor": 8200, "suprimido": False, "confiabilidade": 4},
    ]
    return ContextoIA(indicador=indicador, valores=valores, territorio="3550308")  # type: ignore[arg-type]


def _transport_resposta(texto: str) -> httpx.MockTransport:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": texto}}]})

    return httpx.MockTransport(handler)


def _transport_erro() -> httpx.MockTransport:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    return httpx.MockTransport(handler)


def test_factory_template_sem_config(monkeypatch) -> None:
    monkeypatch.setattr(N, "get_settings", lambda: Settings(llm_base_url=None, llm_model=None))
    assert isinstance(N.narrador_padrao(), N.NarradorTemplate)


def test_factory_llm_quando_configurado(monkeypatch) -> None:
    monkeypatch.setattr(
        N, "get_settings", lambda: Settings(llm_base_url="http://x/v1", llm_model="deepseek-chat")
    )
    nar = N.narrador_padrao()
    assert isinstance(nar, N.NarradorLLM)
    assert nar.id == "llm:deepseek-chat"


async def test_llm_usa_resposta_ancorada() -> None:
    nar = N.NarradorLLM(
        base_url="http://x/v1",
        model="m",
        transport=_transport_resposta("O saldo foi 8.200 em 2026-02. Fonte: Novo CAGED."),
    )
    out = await nar.narrar(_contexto())
    assert "8.200" in out  # veio do LLM (o template escreveria 8200 sem ponto)


async def test_llm_numero_inventado_cai_para_template() -> None:
    nar = N.NarradorLLM(
        base_url="http://x/v1",
        model="m",
        transport=_transport_resposta("Na verdade o saldo foi 9999."),
    )
    out = await nar.narrar(_contexto())
    assert "9999" not in out  # rejeitado pela ancoragem
    assert "8200" in out and "Novo CAGED" in out  # fallback determinístico


async def test_llm_erro_cai_para_template() -> None:
    nar = N.NarradorLLM(base_url="http://x/v1", model="m", transport=_transport_erro())
    out = await nar.narrar(_contexto())
    assert "8200" in out and out.startswith("Saldo de empregos formais")  # template
