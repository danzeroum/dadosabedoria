"""Prova VIVA do runbook de backup (scripts/backup.sh) contra o Postgres real (§8.1.5 / LGPD).

Insere uma linha-marcador de PII no schema ``app`` (como role_consentimento), roda o backup real e
verifica a SEPARAÇÃO: o marcador NÃO aparece no dump analítico (que também não referencia o schema
``app``) e APARECE no dump de ``app`` — que no disco está CIFRADO (só decifra com a passphrase).
Pula se ``pg_dump``/``pg_restore``/``gpg`` não estiverem disponíveis.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import asyncpg
import pytest

from tests.helpers import asyncpg_dsn

pytestmark = pytest.mark.integration

_MARCADOR = "PIIMARKER_backup_test_nao_deve_vazar_no_analitico"


def _raiz_repo() -> Path:
    p = Path(__file__).resolve()
    for pai in p.parents:
        if (pai / "scripts" / "backup.sh").exists():
            return pai
    pytest.skip("scripts/backup.sh não encontrado")


def _ferramentas_ok() -> bool:
    return all(shutil.which(b) for b in ("pg_dump", "pg_restore", "gpg"))


def _toc(dump: Path) -> str:
    return subprocess.run(
        ["pg_restore", "-l", str(dump)], capture_output=True, text=True, check=True
    ).stdout


def _sql(dump: Path) -> str:
    return subprocess.run(
        ["pg_restore", "--no-owner", "-f", "-", str(dump)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


async def test_backup_separa_pii_do_acervo(db_pronto: None, tmp_path: Path) -> None:
    if not _ferramentas_ok():
        pytest.skip("pg_dump/pg_restore/gpg ausentes")

    # 1) insere o marcador de PII como role_consentimento (satisfaz a RLS do app).
    cons = await asyncpg.connect(asyncpg_dsn(os.environ["CONSENT_DATABASE_URL"]))
    try:
        terr = await cons.fetchval("SELECT id FROM territorio LIMIT 1")
        base = await cons.fetchval("SELECT id FROM base_legal LIMIT 1")
        await cons.execute(
            "INSERT INTO app.assinante_alerta "
            "(contato_hash, territorio_id, finalidade, base_legal_id, consentido_em) "
            "VALUES ($1, $2, 'alerta_ivm', $3, now())",
            _MARCADOR,
            terr,
            base,
        )
    finally:
        await cons.close()

    try:
        # 2) roda o backup real.
        env = dict(os.environ)
        env["BACKUP_DIR"] = str(tmp_path)
        env["BACKUP_PASSPHRASE"] = "passphrase-de-teste-do-backup-ci-1234"
        r = subprocess.run(
            ["bash", "scripts/backup.sh"],
            cwd=_raiz_repo(),
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0, f"backup.sh falhou: {r.stderr}"

        analitico = next((tmp_path / "acervo-analitico").glob("*.dump"))
        pii_cifrado = next((tmp_path / "app-pii").glob("*.dump.gpg"))

        # 3) dump analítico: sem schema app, sem o marcador de PII.
        toc = _toc(analitico)
        assert "app " not in toc and "app." not in toc, "dump analítico referencia o schema app!"
        assert _MARCADOR not in _sql(analitico), "PII vazou para o dump analítico!"

        # 4) dump de PII: cifrado no disco (não é um dump válido sem decifrar)…
        assert subprocess.run(["pg_restore", "-l", str(pii_cifrado)]).returncode != 0
        # …decifra e contém o marcador.
        claro = tmp_path / "app.dump"
        dec = subprocess.run(
            [
                "gpg",
                "--batch",
                "--quiet",
                "--pinentry-mode",
                "loopback",
                "--decrypt",
                "--passphrase-fd",
                "0",
                "-o",
                str(claro),
                str(pii_cifrado),
            ],
            input=env["BACKUP_PASSPHRASE"],
            text=True,
        )
        assert dec.returncode == 0, "falha ao decifrar o dump de PII"
        assert _MARCADOR in _sql(claro), "marcador de PII ausente no dump do app"
    finally:
        # limpeza: remove o marcador para não poluir outros testes.
        cons = await asyncpg.connect(asyncpg_dsn(os.environ["CONSENT_DATABASE_URL"]))
        try:
            await cons.execute(
                "DELETE FROM app.assinante_alerta WHERE contato_hash = $1", _MARCADOR
            )
        finally:
            await cons.close()
