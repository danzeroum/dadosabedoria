"""Unidade do plugin de domínio `compras` (PNCP) — prova o contrato ModuloDominio (§6)."""

from __future__ import annotations

import pytest

from app.core.registro import RegistroModulos
from app.domains.compras import ModuloCompras
from app.ingestao.adaptadores.pncp import CODIGO_INDICADOR, AdaptadorPncp
from tests.fixtures.pncp import AMOSTRA, FetcherFake


def _modulo() -> ModuloCompras:
    return ModuloCompras(FetcherFake(AMOSTRA))


def test_registro_ativa_e_lista() -> None:
    reg = RegistroModulos()
    reg.registrar(_modulo())
    assert reg.codigos == ["compras"]


def test_registra_adaptador_e_indicador() -> None:
    m = _modulo()
    adaptadores = m.registrar_adaptadores_fonte()
    assert len(adaptadores) == 1
    assert isinstance(adaptadores[0], AdaptadorPncp)
    codigos = [i["codigo"] for i in m.registrar_indicadores()]  # type: ignore[index]
    assert CODIGO_INDICADOR in codigos


def test_modulo_duplicado_erra() -> None:
    reg = RegistroModulos()
    reg.registrar(_modulo())
    with pytest.raises(ValueError, match="duplicado"):
        reg.registrar(_modulo())
