"""Métricas de domínio (Prometheus) — leves, sem acoplar à fiação OTel de ``observabilidade``.

§13 pede explicitamente *taxa de supressão* e *frescor vs lag por fonte*.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge

#: Total de células suprimidas pela regra de k-anonimato (incrementado em ``escrever_ouro``).
supressao_total = Counter(
    "dadosabedoria_supressao_total",
    "Células suprimidas pela regra de privacidade (k-anonimato).",
    ["indicador"],
)

#: Total de células gravadas (suprimidas ou não).
celulas_gravadas_total = Counter(
    "dadosabedoria_celulas_gravadas_total",
    "Células de valor gravadas na camada ouro.",
    ["indicador"],
)

#: Frescor observado (dias desde o período mais recente) por fonte — populado pela ingestão.
frescor_dias = Gauge(
    "dadosabedoria_frescor_dias",
    "Defasagem observada (dias) do dado mais recente por fonte.",
    ["fonte"],
)
