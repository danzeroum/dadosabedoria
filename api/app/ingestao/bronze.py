"""Camada BRONZE — guarda o dado bruto + hash (proveniência/auditoria, §5).

Abstração de armazenamento de objetos com duas implementações: ``ArmazenamentoMemoria`` (testes) e
``ArmazenamentoMinio`` (produção, S3-compatível). O hash do bruto vai para ``linhagem.hash_origem``.
"""

from __future__ import annotations

import hashlib
import io
from typing import Protocol


class ArmazenamentoBronze(Protocol):
    def salvar(self, chave: str, dados: bytes) -> None: ...
    def ler(self, chave: str) -> bytes: ...


class ArmazenamentoMemoria:
    """Armazenamento em memória — para testes."""

    def __init__(self) -> None:
        self._dados: dict[str, bytes] = {}

    def salvar(self, chave: str, dados: bytes) -> None:
        self._dados[chave] = dados

    def ler(self, chave: str) -> bytes:
        return self._dados[chave]


class ArmazenamentoMinio:  # pragma: no cover - requer MinIO/S3
    """Armazenamento S3-compatível (MinIO). Cria o bucket se necessário."""

    def __init__(
        self, endpoint: str, key: str, secret: str, bucket: str, *, secure: bool = False
    ) -> None:
        from minio import Minio

        self._cli = Minio(endpoint, access_key=key, secret_key=secret, secure=secure)
        self._bucket = bucket
        if not self._cli.bucket_exists(bucket):
            self._cli.make_bucket(bucket)

    def salvar(self, chave: str, dados: bytes) -> None:
        self._cli.put_object(self._bucket, chave, io.BytesIO(dados), length=len(dados))

    def ler(self, chave: str) -> bytes:
        resp = self._cli.get_object(self._bucket, chave)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()


def construir_store_padrao() -> ArmazenamentoBronze:
    """MinIO se S3 estiver configurado; senão, memória (dev/test sem object storage)."""
    from app.core.config import get_settings

    s = get_settings()
    if s.s3_endpoint and s.s3_key and s.s3_secret:  # pragma: no cover - requer MinIO/S3
        endpoint = s.s3_endpoint.split("://")[-1]
        return ArmazenamentoMinio(
            endpoint,
            s.s3_key,
            s.s3_secret,
            s.s3_bucket_bronze,
            secure=s.s3_endpoint.startswith("https"),
        )
    return ArmazenamentoMemoria()


def sha256_hex(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def gravar_bronze(store: ArmazenamentoBronze, chave: str, dados: bytes) -> str:
    """Persiste o bruto e devolve o sha256 (para a linhagem)."""
    store.salvar(chave, dados)
    return sha256_hex(dados)
