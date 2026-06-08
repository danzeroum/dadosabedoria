"""Integração da rota de proveniência consolidada (``/v1/fontes``) — as fontes do acervo.

Afirma **invariantes estáveis** sobre as fontes semeadas (dimensões, não fatos): cobertura por
domínio, licença/base legal presentes, ordenação por nome e o caso honesto de cobertura vazia
(uma fonte sem indicador público aparece com ``dominios=[]``).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_fontes_lista_com_licenca_e_base_legal(client) -> None:
    r = await client.get("/v1/fontes")
    assert r.status_code == 200
    b = r.json()
    por_codigo = {f["codigo"]: f for f in b["dados"]}
    # as 8 fontes da Onda 1/2A estão semeadas
    assert {
        "ibge",
        "novo_caged",
        "bcb_sgs",
        "bcb_estban",
        "datasus_sih",
        "siconfi",
        "inep",
        "pncp",
    } <= set(por_codigo)
    assert b["total"] == len(b["dados"])
    # invariante 5 (proveniência): toda fonte traz licença e base legal — não-vazios.
    for f in b["dados"]:
        assert f["nome"] and f["orgao"] and f["licenca"]
        assert f["base_legal_artigo"] and f["base_legal_hipotese"]
        assert isinstance(f["permite_uso_comercial"], bool)
        assert isinstance(f["dominios"], list)


async def test_fontes_cobertura_por_dominio(client) -> None:
    b = (await client.get("/v1/fontes")).json()
    por_codigo = {f["codigo"]: f for f in b["dados"]}
    # SICONFI alimenta finanças (1 indicador público); CAGED alimenta trabalho.
    assert por_codigo["siconfi"]["dominios"] == ["financas"]
    assert por_codigo["siconfi"]["n_indicadores"] >= 1
    assert por_codigo["siconfi"]["atualizacao"] == "anual"
    assert "trabalho" in por_codigo["novo_caged"]["dominios"]


async def test_fontes_cobertura_vazia_e_honesta(client) -> None:
    # BCB SGS está no acervo como fonte, mas nenhum indicador público a usa → cobertura vazia,
    # mostrada (não escondida). Valida o outer join + ``array_remove(.., NULL)``.
    b = (await client.get("/v1/fontes")).json()
    sgs = next(f for f in b["dados"] if f["codigo"] == "bcb_sgs")
    assert sgs["dominios"] == []
    assert sgs["n_indicadores"] == 0


async def test_fontes_ordenadas_por_nome(client) -> None:
    b = (await client.get("/v1/fontes")).json()
    nomes = [f["nome"] for f in b["dados"]]
    assert nomes == sorted(nomes)
