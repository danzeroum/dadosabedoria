"""TDD da regra única de supressão (k-anonimato) — invariante 1. Pura, sem I/O."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.ingestao.supressao import (
    MOTIVO_PADRAO,
    MOTIVO_SEM_AMOSTRA,
    MetaIndicadorSupressao,
    SupressaoKAnonimato,
)

REGRA = SupressaoKAnonimato()


@pytest.mark.parametrize(
    ("valor", "n_amostra", "n_minimo", "sensivel", "esp_suprimido", "esp_motivo"),
    [
        # n_minimo=0 e sem amostra (saldo CAGED): supressão desligada.
        (Decimal(100), None, 0, False, False, None),
        # contagem abaixo do limiar → suprime.
        (Decimal(100), 3, 5, False, True, MOTIVO_PADRAO),
        # fronteira: n_amostra == limiar é MANTIDO (comparação estrita `<`).
        (Decimal(100), 5, 5, False, False, None),
        # origem sensível eleva o piso para 5 mesmo com n_minimo baixo.
        (Decimal(100), 4, 2, True, True, MOTIVO_PADRAO),
        # origem sensível acima do piso → mantém.
        (Decimal(100), 6, 5, True, False, None),
        # limiar > 0 sem amostra → fail-closed (suprime).
        (Decimal(100), None, 3, False, True, MOTIVO_SEM_AMOSTRA),
        # n_minimo=0 sempre mantém, qualquer amostra.
        (Decimal(100), 1, 0, False, False, None),
    ],
)
def test_aplicar(valor, n_amostra, n_minimo, sensivel, esp_suprimido, esp_motivo) -> None:
    r = REGRA.aplicar(
        valor=valor,
        n_amostra=n_amostra,
        meta=MetaIndicadorSupressao(n_minimo=n_minimo, origem_sensivel=sensivel),
    )
    assert r.suprimido is esp_suprimido
    assert r.motivo_supressao == esp_motivo
    if esp_suprimido:
        assert r.valor is None  # valor nulo ANTES de gravar (invariante 1)
    else:
        assert r.valor == valor


def test_limiar_efetivo_sensivel() -> None:
    rule = SupressaoKAnonimato()
    assert rule.limiar_efetivo(MetaIndicadorSupressao(2, True)) == 5
    assert rule.limiar_efetivo(MetaIndicadorSupressao(8, True)) == 8
    assert rule.limiar_efetivo(MetaIndicadorSupressao(2, False)) == 2
