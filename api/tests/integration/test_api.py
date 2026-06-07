"""API de leitura: proveniência no ``meta``, paginação, supressão visível, erros padronizados."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_health(client) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["db"] is True


async def test_lista_indicadores_carrega_meta(client) -> None:
    r = await client.get("/v1/indicadores")
    assert r.status_code == 200
    body = r.json()
    assert body["paginacao"]["total"] >= 3
    item = body["dados"][0]
    assert item["meta"]["fonte"]
    assert item["meta"]["licenca"]


async def test_filtra_por_dominio(client) -> None:
    r = await client.get("/v1/indicadores", params={"dominio": "trabalho"})
    body = r.json()
    assert body["dados"]
    assert all(i["dominio"] == "trabalho" for i in body["dados"])


async def test_obter_indicador_inexistente_404(client) -> None:
    r = await client.get("/v1/indicadores/nao.existe")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_valores_serie_com_proveniencia(client) -> None:
    r = await client.get(
        "/v1/valores",
        params={"indicador": "trabalho.emprego.saldo_caged", "territorio": "3550308"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["indicador"] == "trabalho.emprego.saldo_caged"
    assert body["meta"]["fonte"] == "Novo CAGED"
    assert body["meta"]["lag_tipico_dias"] == 40  # proveniência: lag (invariante 5)
    valores = [d["valor"] for d in body["dados"]]
    assert valores == [8200.0, -15400.0, -9100.0]  # bate com a referência §4.3


async def test_valores_indicador_obrigatorio(client) -> None:
    r = await client.get("/v1/valores")
    assert r.status_code == 400
    assert r.json()["erro"] == "validacao"


async def test_valores_mes_invalido(client) -> None:
    r = await client.get(
        "/v1/valores", params={"indicador": "trabalho.emprego.saldo_caged", "de": "2026/01"}
    )
    assert r.status_code == 400
    assert r.json()["erro"] == "validacao"


async def test_celula_suprimida_visivel_sem_valor(client) -> None:
    # Recorta o período da semente (2026-04): a esteira DATASUS/SIH pode gravar outras competências
    # de saúde de Campinas (também suprimidas) no banco compartilhado — afirma o invariante, não a
    # contagem total.
    r = await client.get(
        "/v1/valores",
        params={
            "indicador": "saude.resp.internacoes_j",
            "territorio": "3509502",
            "de": "2026-04",
            "ate": "2026-04",
        },
    )
    body = r.json()
    assert len(body["dados"]) == 1
    cel = body["dados"][0]
    assert cel["suprimido"] is True
    assert cel["valor"] is None  # nunca expõe o valor suprimido
    assert "limiar" in cel["motivo_supressao"]


async def test_paginacao_limite(client) -> None:
    r = await client.get("/v1/indicadores", params={"por_pagina": 1})
    body = r.json()
    assert len(body["dados"]) == 1
    assert body["paginacao"]["por_pagina"] == 1


async def test_territorio_com_hierarquia(client) -> None:
    r = await client.get("/v1/territorios/3550308")
    assert r.status_code == 200
    body = r.json()
    assert body["nome"] == "São Paulo"
    assert body["nivel"] == "municipio"
    assert body["pai"]["codigo_ibge"] == "35"


async def test_territorio_inexistente_404(client) -> None:
    r = await client.get("/v1/territorios/0000000")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_territorio_raiz_sem_pai(client) -> None:
    r = await client.get("/v1/territorios/1")
    assert r.status_code == 200
    body = r.json()
    assert body["nome"] == "Brasil"
    assert body["pai"] is None


async def test_valores_filtro_periodo(client) -> None:
    r = await client.get(
        "/v1/valores",
        params={
            "indicador": "trabalho.emprego.saldo_caged",
            "territorio": "3550308",
            "de": "2026-03",
            "ate": "2026-04",
        },
    )
    body = r.json()
    assert [d["periodo"] for d in body["dados"]] == ["2026-03", "2026-04"]


async def test_cache_hit_repete_resultado(client) -> None:
    # Segunda chamada idêntica deve vir do cache (read-through Redis) com o mesmo payload.
    p = {"indicador": "trabalho.emprego.saldo_caged", "territorio": "3550308"}
    r1 = await client.get("/v1/valores", params=p)
    r2 = await client.get("/v1/valores", params=p)
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()


async def test_metrics_interno_exposto(client) -> None:
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "# HELP" in r.text
