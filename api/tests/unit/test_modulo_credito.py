"""Unidade do plugin de domínio `credito` (BCB/ESTBAN)."""

from __future__ import annotations

from app.core.registro import RegistroModulos
from app.domains.credito import ModuloCredito
from app.ingestao.adaptadores.estban import CODIGO_INDICADOR, AdaptadorEstban
from tests.fixtures.caged import FetcherFake
from tests.fixtures.estban import AMOSTRA_ESTBAN


def _modulo() -> ModuloCredito:
    return ModuloCredito(FetcherFake(AMOSTRA_ESTBAN))


def test_registro_ativa_e_lista() -> None:
    reg = RegistroModulos()
    reg.registrar(_modulo())
    assert reg.codigos == ["credito"]


def test_registra_adaptador_e_indicador() -> None:
    m = _modulo()
    adaptadores = m.registrar_adaptadores_fonte()
    assert len(adaptadores) == 1
    assert isinstance(adaptadores[0], AdaptadorEstban)
    codigos = [i["codigo"] for i in m.registrar_indicadores()]  # type: ignore[index]
    assert CODIGO_INDICADOR in codigos


def test_dois_modulos_convivem() -> None:
    from app.domains.trabalho import ModuloTrabalho
    from tests.fixtures.caged import AMOSTRA_UNIT

    reg = RegistroModulos()
    reg.registrar(ModuloTrabalho(FetcherFake(AMOSTRA_UNIT)))
    reg.registrar(_modulo())
    assert reg.codigos == ["credito", "trabalho"]
