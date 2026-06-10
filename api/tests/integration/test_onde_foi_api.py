"""Integração da rota do OndeFoi (``/v1/onde-foi``) — leitura da fato ``execucao_funcao``.

Comportamento pós go-live (ADR-0029/0032): sem grau-demo, dado real da pipeline de ingestão.
- Município desconhecido: 404 (nunca 200 com demo).
- Com dado semeado: pct/banda corretos, contrato ADR-0026 mantido.

Nota: ``role_analitica`` (DATABASE_URL) tem INSERT/UPDATE em ``execucao_funcao`` mas NÃO DELETE;
a limpeza usa o ADMIN_DATABASE_URL (role postgres). Os testes que precisam de estado limpo
semeiam explicitamente; os que precisam de vazio usam a coleção admin para limpar.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.siconfi import AdaptadorSiconfi
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_siconfi_funcoes
from tests.fixtures.siconfi import AMOSTRA_FUNCOES, FetcherFake

pytestmark = pytest.mark.integration

_DELETE = text("DELETE FROM execucao_funcao")


async def _seed(conn_url: str) -> None:
    """Insere o AMOSTRA_FUNCOES na fato via pipeline real."""
    adaptador = AdaptadorSiconfi(FetcherFake(AMOSTRA_FUNCOES))
    async with connect(conn_url) as conn:
        await executar_siconfi_funcoes(
            Janela(2024, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
        )


async def _limpar() -> None:
    """Limpa execucao_funcao via ADMIN_DATABASE_URL (role_analitica não tem DELETE)."""
    admin_url = os.environ.get("ADMIN_DATABASE_URL", get_settings().database_url)
    async with connect(admin_url) as conn:
        await conn.execute(_DELETE)


async def test_onde_foi_404_sem_dado(client, db_pronto: None) -> None:
    await _limpar()
    r = await client.get("/v1/onde-foi/3550308")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_onde_foi_lista_vazia_sem_dado(client, db_pronto: None) -> None:
    await _limpar()
    r = await client.get("/v1/onde-foi")
    assert r.status_code == 200
    b = r.json()
    assert b["dados"] == []
    # Tabela vazia: meta NÃO deve mostrar o ano corrente (default=date.today() era o bug).
    assert str(r.headers.get("date", "")[:4]) not in b["meta"]["periodo_rotulo"]
    assert "sem dados" in b["meta"]["periodo_rotulo"]


async def test_onde_foi_contrato_sp(client, db_pronto: None) -> None:
    await _limpar()
    await _seed(get_settings().database_url)
    r = await client.get("/v1/onde-foi/3550308")
    assert r.status_code == 200
    b = r.json()
    assert b["nome"] == "São Paulo"
    # 4 funções com liquidado → empenhado_base == empenhado_total, fora_base == 0
    assert b["empenhado_fora_base"] == b["empenhado_total"] - b["empenhado_base"]
    assert b["empenhado_base"] > 0
    assert b["liquidado"] > 0
    # base-única (ADR-0026/0029): % sobre as funções divulgadas
    assert b["pct"] == round(b["liquidado"] / b["empenhado_base"] * 100)
    # honestidade: execução orçamentária, não serviço entregue
    assert "serviço entregue" in b["meta"]["metodologia"]
    assert "2024" in b["meta"]["periodo_rotulo"]
    # selo de confiança: proveniência rica
    assert "Licença aberta" in b["meta"]["licenca"]
    fonte = b["meta"]["fontes"][0]
    assert fonte["sigla"] == "SICONFI"
    assert {"nome", "orgao", "dominio", "ate", "atraso"} <= set(fonte)
    # sem cadeado de privacidade em orçamento público
    assert {f["exe_estado"] for f in b["funcoes"]} <= {"valor", "sem_cobertura"}


async def test_onde_foi_lista_com_dado(client, db_pronto: None) -> None:
    await _limpar()
    await _seed(get_settings().database_url)
    r = await client.get("/v1/onde-foi")
    assert r.status_code == 200
    b = r.json()
    nomes = [d["nome"] for d in b["dados"]]
    # Fixture tem só SP → lista tem 1 município
    assert "São Paulo" in nomes
    assert nomes == sorted(nomes)  # por nome, não leaderboard (dupla-face §17)
    # cada resumo tem o contrato mínimo; nada de detalhe por função
    for d in b["dados"]:
        assert {"codigo_ibge", "nome", "uf", "pct", "banda"} == set(d)
    # SP deve ter pct calculado
    sp = next(d for d in b["dados"] if d["codigo_ibge"] == "3550308")
    assert sp["pct"] > 0
    assert sp["banda"] in {"alta", "parcial", "baixa"}
    # selo de confiança
    assert b["meta"]["fontes"][0]["sigla"] == "SICONFI"


async def test_onde_foi_municipio_sem_cadastro_404(client, db_pronto: None) -> None:
    r = await client.get("/v1/onde-foi/0000000")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"
