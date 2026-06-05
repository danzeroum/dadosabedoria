"""Checagem estática do runbook de backup (scripts/backup.sh): a SEPARAÇÃO de PII é mecânica,
não uma promessa humana (invariante 2; §8.1.5 / LGPD Art. 18).

Garante, lendo o próprio script, que:
- o dump do ACERVO ANALÍTICO exclui o schema ``app`` e roda como role_analitica (sem PII);
- o dump da PII usa só o schema ``app``, roda como role_consentimento e é CIFRADO antes do disco
  (nunca há artefato de PII em claro);
- a retenção da PII é MAIS CURTA que a do acervo (minimização).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


def _achar(nome: str) -> Path:
    p = Path(__file__).resolve()
    for pai in p.parents:
        candidato = pai / nome
        if candidato.exists():
            return candidato
    pytest.skip(f"{nome} não encontrado")


def _script() -> str:
    return _achar("scripts/backup.sh").read_text(encoding="utf-8")


def test_dump_analitico_exclui_app_e_vem_da_role_analitica() -> None:
    txt = _script()
    # URL do dump analítico vem de DATABASE_URL (analitica); a do app, de CONSENT_DATABASE_URL.
    assert 'analitico_url="$(para_libpq "$DATABASE_URL")"' in txt
    assert 'app_url="$(para_libpq "$CONSENT_DATABASE_URL")"' in txt
    # o comando de dump analítico usa essa URL e EXCLUI o schema app (sem PII, por construção).
    assert re.search(r'pg_dump "\$analitico_url"[^|]*?--exclude-schema=app', txt, re.S), (
        "o dump analítico deve usar \\$analitico_url e --exclude-schema=app"
    )


def test_dump_pii_usa_app_e_e_cifrado() -> None:
    txt = _script()
    # o dump de PII usa \$app_url (role_consentimento), só o schema app, e é cifrado (gpg) no pipe.
    assert re.search(
        r'pg_dump "\$app_url"[^\n]*--schema=app[^\n]*\n\s*\|\s*gpg[^\n]*--symmetric', txt
    ), "o dump de PII deve usar \\$app_url, --schema=app e ser canalizado p/ `gpg --symmetric`"
    assert "--cipher-algo AES256" in txt
    # o artefato de PII termina em .gpg (cifrado); não existe artefato de PII em claro.
    assert ".dump.gpg" in txt


def test_retencao_da_pii_e_mais_curta() -> None:
    txt = _script()
    anal = int(re.search(r"ANALYTIC_RETENTION_DAYS:-(\d+)", txt).group(1))
    app = int(re.search(r"APP_RETENTION_DAYS:-(\d+)", txt).group(1))
    assert app < anal, f"retenção de PII ({app}d) deve ser menor que a do acervo ({anal}d)"
