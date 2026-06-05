"""Agenda da ingestão — qual competência buscar, dada a defasagem da fonte."""

from __future__ import annotations

from datetime import date


def competencia_alvo(hoje: date, defasagem_meses: int = 2) -> str:
    """Competência (YYYYMM) a ingerir hoje. CAGED tem lag ~40 dias → padrão: 2 meses atrás."""
    indice = (hoje.year * 12 + (hoje.month - 1)) - defasagem_meses
    ano, mes0 = divmod(indice, 12)
    return f"{ano:04d}{mes0 + 1:02d}"
