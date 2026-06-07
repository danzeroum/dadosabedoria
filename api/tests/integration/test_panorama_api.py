"""Integração da rota do panorama (``/v1/territorios/{ibge}/panorama``) — todos os indicadores.

Os testes afirmam **invariantes estáveis** (largura de domínios, uma linha por indicador,
proveniência por indicador, privacidade), não valores "mais recentes" — o banco de testes é
compartilhado na sessão e outros testes acrescentam células; o "último período" não é fixo.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_panorama_sp_atravessa_dominios_com_proveniencia(client) -> None:
    r = await client.get("/v1/territorios/3550308/panorama")
    assert r.status_code == 200
    b = r.json()
    assert b["nome"] == "São Paulo"
    assert b["nivel"] == "municipio"
    # atravessa os domínios semeados (não só os do IVM): trabalho/credito/saude/financas/edu/compras
    dominios = {i["dominio"] for i in b["indicadores"]}
    assert {"trabalho", "credito", "saude", "financas", "educacao", "compras"} <= dominios
    # proveniência por indicador (a fonte é do indicador, estável em qualquer período).
    assert all(i["fonte"] for i in b["indicadores"])
    por_codigo = {i["codigo"]: i for i in b["indicadores"]}
    assert por_codigo["trabalho.emprego.saldo_caged"]["fonte"] == "Novo CAGED"
    assert por_codigo["saude.resp.internacoes_j"]["fonte"] == "SIH/SUS"


async def test_panorama_uma_linha_por_indicador(client) -> None:
    # DISTINCT ON (indicador.codigo): no máximo uma linha por indicador (a célula mais recente).
    b = (await client.get("/v1/territorios/3550308/panorama")).json()
    codigos = [i["codigo"] for i in b["indicadores"]]
    assert len(codigos) == len(set(codigos))  # sem duplicata


async def test_panorama_suprimido_nunca_expoe_valor(client) -> None:
    # Privacidade estrutural: toda célula suprimida vem com valor nulo. Campinas tem a saúde
    # sub-limiar semeada (n=3<5) → o panorama a mostra protegida, jamais o número.
    b = (await client.get("/v1/territorios/3509502/panorama")).json()
    assert all(i["valor"] is None for i in b["indicadores"] if i["suprimido"])
    saude = next(i for i in b["indicadores"] if i["codigo"] == "saude.resp.internacoes_j")
    assert saude["suprimido"] is True
    assert saude["valor"] is None
    assert saude["motivo_supressao"] is not None


async def test_panorama_territorio_inexistente_404(client) -> None:
    r = await client.get("/v1/territorios/0000000/panorama")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_panorama_territorio_sem_dado_lista_vazia(client) -> None:
    # Brasil existe como território, mas não tem dado de grão municipal → lista vazia (200).
    r = await client.get("/v1/territorios/1/panorama")
    assert r.status_code == 200
    assert r.json()["indicadores"] == []
