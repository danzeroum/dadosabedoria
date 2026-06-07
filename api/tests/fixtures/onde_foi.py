"""Demo do OndeFoi — fiel ao CONTRATO (ADR-0026), **não** à forma do DCA real.

Espelha o ``data.js`` do protótipo (valores = verdade-de-contrato), com ``"suprimido"`` →
``"sem_cobertura"`` (orçamento por função é público sem PII — ADR-0026 refino: válido =
``{valor, sem_cobertura}``). Nomes/classificação de função e ``codigo_ibge`` são **provisórios**
até a validação no #0 (forma-verdade vem da própria fonte, nunca do mock).
"""

from __future__ import annotations

from app.produtos.onde_foi import FuncaoBruta

# (codigo_ibge, nome, uf, recebido_total, funcoes). recebido_total > Σ funções → há recurso não
# detalhado por função; ele aparece em recebido_fora_base, nunca silenciosamente fora do %.
DEMO: list[tuple[str, str, str, int, list[FuncaoBruta]]] = [
    (
        "3304557",
        "Rio de Janeiro",
        "RJ",
        41200,
        [
            FuncaoBruta("Saúde", 9800, 8120),
            FuncaoBruta("Educação", 8600, 7310),
            FuncaoBruta("Assistência social", 2400, 1490),
            FuncaoBruta("Urbanismo", 5200, 2860),
            FuncaoBruta("Saneamento", 1800, "sem_cobertura"),
            FuncaoBruta("Cultura", 700, "sem_cobertura"),
        ],
    ),
    (
        "3550308",
        "São Paulo",
        "SP",
        78900,
        [
            FuncaoBruta("Saúde", 18200, 16930),
            FuncaoBruta("Educação", 17400, 16240),
            FuncaoBruta("Assistência social", 4100, 3360),
            FuncaoBruta("Urbanismo", 9800, 7250),
            FuncaoBruta("Saneamento", 3200, 2880),
            FuncaoBruta("Cultura", 1500, 1140),
        ],
    ),
    (
        "3106200",
        "Belo Horizonte",
        "MG",
        15600,
        [
            FuncaoBruta("Saúde", 4100, 3650),
            FuncaoBruta("Educação", 3800, 3420),
            FuncaoBruta("Assistência social", 980, 690),
            FuncaoBruta("Urbanismo", 2300, 1240),
            FuncaoBruta("Saneamento", 740, "sem_cobertura"),
            FuncaoBruta("Cultura", 320, 210),
        ],
    ),
    (
        "3303500",
        "Nova Iguaçu",
        "RJ",
        4900,
        [
            FuncaoBruta("Saúde", 1320, 760),
            FuncaoBruta("Educação", 1180, 880),
            FuncaoBruta("Assistência social", 360, 150),
            FuncaoBruta("Urbanismo", 540, 190),
            FuncaoBruta("Saneamento", 210, "sem_cobertura"),
            FuncaoBruta("Cultura", 90, "sem_cobertura"),
        ],
    ),
    (
        "3543402",
        "Ribeirão Preto",
        "SP",
        6300,
        [
            FuncaoBruta("Saúde", 1640, 1510),
            FuncaoBruta("Educação", 1490, 1360),
            FuncaoBruta("Assistência social", 410, 330),
            FuncaoBruta("Urbanismo", 760, 520),
            FuncaoBruta("Saneamento", 280, 240),
            FuncaoBruta("Cultura", 120, 80),
        ],
    ),
    (
        "3154606",
        "Ribeirão das Neves",
        "MG",
        2100,
        [
            FuncaoBruta("Saúde", 560, 240),
            FuncaoBruta("Educação", 520, 360),
            FuncaoBruta("Assistência social", 160, 60),
            FuncaoBruta("Urbanismo", 230, 70),
            FuncaoBruta("Saneamento", 90, "sem_cobertura"),
            FuncaoBruta("Cultura", 40, "sem_cobertura"),
        ],
    ),
]
