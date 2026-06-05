"""Unidade da camada bronze (armazenamento + hash)."""

from __future__ import annotations

from app.ingestao.bronze import (
    ArmazenamentoMemoria,
    construir_store_padrao,
    gravar_bronze,
    sha256_hex,
)


def test_memoria_salva_e_le() -> None:
    store = ArmazenamentoMemoria()
    h = gravar_bronze(store, "caged/202607.txt", b"abc")
    assert store.ler("caged/202607.txt") == b"abc"
    assert h == sha256_hex(b"abc")


def test_store_padrao_cai_para_memoria_sem_s3() -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    assert isinstance(construir_store_padrao(), ArmazenamentoMemoria)
