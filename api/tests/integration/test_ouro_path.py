"""Caminho ouro compartilhado: supressão aplicada ANTES de gravar + linhagem por lote.

Prova também (linhagem não-vazia) que o seed passou pelo caminho ouro — um INSERT cru deixaria a
tabela ``linhagem`` vazia (a restrição do produto: seeds pela MESMA regra da ingestão).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro
from app.ingestao.supressao import MetaIndicadorSupressao

pytestmark = pytest.mark.integration


async def test_seed_registrou_linhagem(db_pronto: None) -> None:
    async with connect(get_settings().database_url) as conn:
        n = (await conn.execute(text("SELECT count(*) FROM linhagem"))).scalar_one()
        assert n >= 3  # uma por lote semeado (CAGED, crédito, saúde)


async def test_seed_suprimiu_celula_sensivel(db_pronto: None) -> None:
    async with connect(get_settings().database_url) as conn:
        row = (
            (
                await conn.execute(
                    text(
                        """
                    SELECT v.valor, v.suprimido, v.motivo_supressao
                    FROM valor v
                    JOIN indicador i ON i.id = v.indicador_id
                    JOIN territorio t ON t.id = v.territorio_id
                    WHERE i.codigo = 'saude.resp.internacoes_j' AND t.codigo_ibge = '3509502'
                    """
                    )
                )
            )
            .mappings()
            .first()
        )
    assert row is not None
    assert row["suprimido"] is True
    assert row["valor"] is None
    assert "limiar" in row["motivo_supressao"]


async def test_escrever_ouro_suprime_e_grava(db_pronto: None) -> None:
    async with connect(get_settings().database_url) as conn:
        ind = (
            (
                await conn.execute(
                    text(
                        "SELECT id, fonte_id FROM indicador WHERE codigo='saude.resp.internacoes_j'"
                    )
                )
            )
            .mappings()
            .first()
        )
        ter = (
            await conn.execute(text("SELECT id FROM territorio WHERE codigo_ibge='3550308'"))
        ).scalar_one()

        grav = GravadorOuro(conn)
        cel = [
            CelulaOuro(
                ind["id"], ter, date(2031, 1, 1), "mensal", Decimal(2), 2, 4, ind["fonte_id"]
            )
        ]
        meta = {ind["id"]: MetaIndicadorSupressao(n_minimo=5, origem_sensivel=True)}
        resumo = await grav.escrever_ouro(
            cel, meta, ContextoLinhagem(ind["fonte_id"], ind["id"], "teste", "pytest")
        )
        assert resumo.suprimidos == 1

        row = (
            (
                await conn.execute(
                    text(
                        "SELECT valor, suprimido FROM valor WHERE indicador_id=:i "
                        "AND territorio_id=:t AND periodo='2031-01-01' AND versao=1"
                    ),
                    {"i": ind["id"], "t": ter},
                )
            )
            .mappings()
            .first()
        )
    assert row["suprimido"] is True
    assert row["valor"] is None
