"""Sentinela Respiratória (SAUDE-01) — internações SUS por doenças respiratórias por município.

Pergunta do produto: **quantas internações por doenças respiratórias ocorreram no município?**
Usa as internações com diagnóstico principal no grupo J do CID-10 (J00–J99) registradas no
SIH/SUS (DATASUS). Dado de **origem sensível**: células abaixo do piso de k-anonimato (n<5)
são suprimidas — aparecem como **protegido**, nunca como zero (ADR-0004).

HONESTIDADE:
- Cobre apenas internações **no SUS** (público): hospitais privados não estão incluídos.
- Fluxo mensal: variações podem refletir **sazonalidade** (inverno → mais casos respiratórios),
  capacidade hospitalar ou subregistro de AIH — não apenas incidência real.
- Células suprimidas (k-anon) revelam que houve internações, mas em número pequeno demais para
  divulgar sem risco de reidentificação. **Não significa ausência de casos.**
- Lag típico: ~90 dias após a competência (SIH/SUS é publicado com atraso).
- Indicador de **contagem** (não normalizado): cidades maiores têm mais internações absolutas.
  Use per 100k para comparação entre municípios de portes diferentes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Nível de internações respiratórias (por 100k hab/mês). ``suprimido`` = k-anon protegido.
NivelSentinela = Literal["elevado", "moderado", "baixo", "suprimido", "sem_dado"]
#: Tendência mensal das internações (mês atual vs. anterior).
TendenciaSentinela = Literal["subindo", "estavel", "caindo"]

# Limiares provisórios (internações / 100k hab / mês). Calibrar com distribuição nacional.
_POR_100K_ELEVADO = 10.0  # ≥10/100k → carga elevada
_POR_100K_MODERADO = 3.0  # 3–9/100k → carga moderada

NOTA_HONESTA = (
    "Internações com diagnóstico principal no grupo J do CID-10 (doenças do aparelho respiratório, "
    "J00–J99) no SIH/SUS por município/mês. Cobre apenas internações no SUS (público); hospitais "
    "privados não estão incluídos (~30% das internações nacionais). Fluxo mensal sujeito a "
    "sazonalidade (inverno → mais casos), capacidade hospitalar e subregistro de AIH — não é "
    "apenas incidência real. Células com menos de 5 internações são protegidas (k-anonimato, "
    "ADR-0004): aparecem como 'protegido', nunca como zero. 'Protegido' indica que houve "
    "internações — em número pequeno demais para divulgar com segurança. Lag típico: ~90 dias."
)


@dataclass(frozen=True)
class MesInternacoes:
    """Uma batida mensal: contagem ou supressão."""

    periodo: str  # YYYY-MM
    internacoes: int | None  # None = suprimido (k-anon)
    suprimido: bool


@dataclass(frozen=True)
class SentinelaResp:
    """Contrato: internações respiratórias SUS com supressão honesta."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY-MM do dado mais recente
    internacoes: int | None  # None se suprimido ou sem dado
    internacoes_por_100k: float | None  # normalizado; None se suprimido ou sem populacao
    suprimido: bool  # True = dado mais recente protegido pelo k-anonimato
    nivel: NivelSentinela
    tendencia: TendenciaSentinela | None  # None sem mês anterior comparável
    meses: tuple[MesInternacoes, ...]  # série histórica (inclui meses suprimidos)


def classificar_nivel(por_100k: float | None, suprimido: bool) -> NivelSentinela:
    """Nível do dado mais recente (suprimido tem prioridade sobre o per-capita)."""
    if suprimido:
        return "suprimido"
    if por_100k is None:
        return "sem_dado"
    if por_100k >= _POR_100K_ELEVADO:
        return "elevado"
    if por_100k >= _POR_100K_MODERADO:
        return "moderado"
    return "baixo"


def classificar_tendencia(atual: int, anterior: int) -> TendenciaSentinela:
    """Tendência: mês atual vs. mês anterior (ambos não suprimidos)."""
    if atual > anterior:
        return "subindo"
    if atual < anterior:
        return "caindo"
    return "estavel"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    meses: list[MesInternacoes],
) -> SentinelaResp:
    """Monta a Sentinela a partir da série de meses (não-vazia, ordenada por período).

    A rota garante ≥1 mês (senão 404). Meses suprimidos aparecem na série e influenciam a
    apresentação; o nível sempre reflete o dado mais recente.
    """
    if not meses:
        raise ValueError("sentinela requer ao menos um mês")

    ultimo = meses[-1]
    por_100k: float | None = None
    if not ultimo.suprimido and ultimo.internacoes is not None:
        if populacao and populacao > 0:
            por_100k = ultimo.internacoes / populacao * 100_000

    # Tendência: último par de meses não-suprimidos consecutivos
    tendencia: TendenciaSentinela | None = None
    reais = [m for m in meses if not m.suprimido and m.internacoes is not None]
    if len(reais) >= 2:
        tendencia = classificar_tendencia(reais[-1].internacoes, reais[-2].internacoes)  # type: ignore[arg-type]

    return SentinelaResp(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        periodo=ultimo.periodo,
        internacoes=ultimo.internacoes,
        internacoes_por_100k=round(por_100k, 1) if por_100k is not None else None,
        suprimido=ultimo.suprimido,
        nivel=classificar_nivel(por_100k, ultimo.suprimido),
        tendencia=tendencia,
        meses=tuple(meses),
    )
