"""Exporta o OpenAPI do app para ``docs/openapi.yaml`` de forma DETERMINÍSTICA.

Fonte única da verdade do contrato (§7). O CI roda este script e falha se o arquivo commitado
divergir de uma exportação fresca (gate de contrato/regressão). Chaves ordenadas + versão fixa →
sem drift falso.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Permite rodar de qualquer cwd: garante que ``app`` é importável.
_API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_API_ROOT))

from app.main import create_app  # noqa: E402

_DESTINO = _API_ROOT.parent / "docs" / "openapi.yaml"


def gerar() -> str:
    schema = create_app().openapi()
    return yaml.safe_dump(schema, sort_keys=True, allow_unicode=True, default_flow_style=False)


def main() -> None:
    conteudo = gerar()
    _DESTINO.parent.mkdir(parents=True, exist_ok=True)
    _DESTINO.write_text(conteudo, encoding="utf-8")
    print(f"OpenAPI exportado para {_DESTINO}")  # noqa: T201


if __name__ == "__main__":
    main()
