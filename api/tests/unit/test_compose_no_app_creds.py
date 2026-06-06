"""Checagem estática do docker-compose: serviços analíticos (api/worker/ai) NÃO recebem
credenciais do schema ``app`` (§8.1 ponto 3). Torna mecânica a promessa de isolamento.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_NEGADAS = {"CONSENT_DATABASE_URL", "APP_FIELD_KEY", "APP_FIELD_KEYS_ANTIGAS", "CONSENT_PWD"}
_SERVICOS_ANALITICOS = {"api", "worker", "ai", "orchestrator"}


def _achar_compose() -> Path:
    p = Path(__file__).resolve()
    for pai in p.parents:
        candidato = pai / "docker-compose.yml"
        if candidato.exists():
            return candidato
    pytest.skip("docker-compose.yml não encontrado")


def _nomes_env(environment: object) -> set[str]:
    if environment is None:
        return set()
    if isinstance(environment, dict):
        return set(environment.keys())
    nomes = set()
    for item in environment:  # lista "NOME" ou "NOME=valor"
        nomes.add(str(item).split("=", 1)[0])
    return nomes


def test_servicos_analiticos_sem_credencial_app() -> None:
    compose = yaml.safe_load(_achar_compose().read_text(encoding="utf-8"))
    servicos = compose.get("services", {})
    for nome in _SERVICOS_ANALITICOS:
        svc = servicos.get(nome)
        if not svc:
            continue
        vazou = _nomes_env(svc.get("environment")) & _NEGADAS
        assert not vazou, f"serviço '{nome}' recebe credencial do app: {vazou}"
