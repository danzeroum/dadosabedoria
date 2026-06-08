"""IA ancorada: resposta só sobre o recuperado, com citação; abstenção honesta. Contra DB real."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_resposta_ancorada_com_citacao(client) -> None:
    r = await client.post(
        "/v1/ia/perguntar",
        json={
            "pergunta": "como está o saldo de empregos formais?",
            "indicador": "trabalho.emprego.saldo_caged",
            "territorio": "3550308",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["abstencao"] is False
    assert body["narrador"] == "template-v1"
    assert "8200" in body["resposta"]  # valor do seed (SP 2026-02)
    cit = body["citacoes"][0]
    assert cit["indicador"] == "trabalho.emprego.saldo_caged"
    assert cit["fonte"] == "Novo CAGED"
    assert cit["lag_tipico_dias"] == 40
    assert any("causalidade" in r for r in body["ressalvas"])


async def test_identifica_indicador_pela_pergunta(client) -> None:
    r = await client.post(
        "/v1/ia/perguntar",
        json={
            "pergunta": "qual o saldo de empregos formais em São Paulo?",
            "territorio": "3550308",
        },
    )
    body = r.json()
    assert body["abstencao"] is False
    assert body["citacoes"][0]["indicador"] == "trabalho.emprego.saldo_caged"


async def test_identifica_por_sinonimo_leigo(client) -> None:
    # "escola"/"aluno" não estão no léxico do dado (matrículas/ensino); o sinônimo do cidadão
    # aponta o domínio educação e a IA responde com citação, em vez de abster.
    r = await client.post(
        "/v1/ia/perguntar",
        json={"pergunta": "quantos alunos nas escolas?", "territorio": "3550308"},
    )
    body = r.json()
    assert body["abstencao"] is False
    assert body["citacoes"][0]["indicador"] == "educacao.matriculas.fundamental"


async def test_abstem_sem_indicador(client) -> None:
    r = await client.post("/v1/ia/perguntar", json={"pergunta": "qual a cor do céu hoje?"})
    body = r.json()
    assert body["abstencao"] is True
    assert body["citacoes"] == []


async def test_abstem_sem_dado(client) -> None:
    r = await client.post(
        "/v1/ia/perguntar",
        json={
            "pergunta": "saldo de emprego",
            "indicador": "trabalho.emprego.saldo_caged",
            "territorio": "0000000",
        },
    )
    body = r.json()
    assert body["abstencao"] is True


async def test_origem_sensivel_pede_revisao_humana(client) -> None:
    r = await client.post(
        "/v1/ia/perguntar",
        json={
            "pergunta": "internações respiratórias",
            "indicador": "saude.resp.internacoes_j",
            "territorio": "3550308",
        },
    )
    body = r.json()
    assert body["abstencao"] is False
    assert body["revisao_humana"] is True
