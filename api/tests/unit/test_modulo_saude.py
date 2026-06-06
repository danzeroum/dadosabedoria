"""Unidade do plugin de domínio `saude` (DATASUS/SIH) — prova o contrato ModuloDominio (§6)."""

from __future__ import annotations

import pytest

from app.core.registro import RegistroModulos
from app.domains.saude import ModuloSaude
from app.ingestao.adaptadores.datasus import CODIGO_INDICADOR, AdaptadorDatasus
from tests.fixtures.datasus import AMOSTRA, FetcherFake


def _modulo() -> ModuloSaude:
    return ModuloSaude(FetcherFake(AMOSTRA))


def test_registro_ativa_e_lista() -> None:
    reg = RegistroModulos()
    reg.registrar(_modulo())
    assert reg.codigos == ["saude"]


def test_registra_adaptador_e_indicador() -> None:
    m = _modulo()
    adaptadores = m.registrar_adaptadores_fonte()
    assert len(adaptadores) == 1
    assert isinstance(adaptadores[0], AdaptadorDatasus)
    codigos = [i["codigo"] for i in m.registrar_indicadores()]  # type: ignore[index]
    assert CODIGO_INDICADOR in codigos


def test_modulo_duplicado_erra() -> None:
    reg = RegistroModulos()
    reg.registrar(_modulo())
    with pytest.raises(ValueError, match="duplicado"):
        reg.registrar(_modulo())
