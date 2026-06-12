"""AguaViva (SANE-01) — acesso a água tratada e coleta de esgoto por município (SNIS/MDR).

Pergunta do produto: **como está o acesso a água e esgoto no município?**

Usa os indicadores ``saneamento.agua.atendimento_pct`` (IN023_AE) e
``saneamento.esgoto.coleta_pct`` (IN015_AE) do SNIS. Lógica **pura** — sem rede/DB.

HONESTIDADE:
- IN023_AE = índice de atendimento total de água (pop. urbana atendida / pop. total declarada).
  Cobre apenas o prestador declarante ao SNIS — sistemas alternativos e poços individuais
  não estão incluídos. Pode subestimar zonas rurais e municípios com baixa adesão ao SNIS.
- IN015_AE = índice de coleta de esgoto. Tratamento pode ser bem inferior à coleta.
- Municípios sem prestador declarante ao SNIS aparecem sem dado.
- Dado anual: lag típico de 12–18 meses em relação ao exercício de referência.
- Dupla face (§17): indicador agregado por município — estrutural, não culpa dos moradores;
  uso como contexto de vulnerabilidade, não ranking de eficiência. (SANE-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelAcesso = Literal["adequado", "atencao", "alerta", "sem_dado"]

# Limiares (%) baseados nos ODSs e no padrão nacional brasileiro.
# ODS 6 meta: 100% acesso água potável até 2030.
_LIMIAR_ADEQUADO = 90.0  # ≥ 90%: acesso amplo (maioria das capitais e grandes cidades)
_LIMIAR_ATENCAO = 70.0  # 70–89%: atenção (déficit expressivo)
# < 70%: alerta (déficit grave)

NOTA_HONESTA = (
    "Índice de atendimento de água (IN023_AE) e coleta de esgoto (IN015_AE) do SNIS "
    "(Sistema Nacional de Informações sobre Saneamento, MDR). Cobre o prestador principal "
    "declarante ao SNIS — sistemas alternativos e poços individuais não entram. "
    "Municípios sem prestador declarante aparecem sem dado. "
    "Dado anual com lag típico de 12–18 meses. "
    "Indicador estrutural de vulnerabilidade — não reflete culpa dos moradores. "
    "Limiares: adequado ≥ 90 %, atenção 70–89 %, alerta < 70 % (SANE-01, dupla face §17)."
)


@dataclass(frozen=True)
class AguaViva:
    """Contrato: acesso a saneamento básico por município."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None  # YYYY do exercício mais recente com dado
    agua_pct: float | None  # 0–100 %, IN023_AE
    esgoto_pct: float | None  # 0–100 %, IN015_AE (pode ser None)
    nivel_agua: NivelAcesso
    nivel_esgoto: NivelAcesso


def classificar_nivel(pct: float | None) -> NivelAcesso:
    """Classifica o nível de acesso (água ou esgoto)."""
    if pct is None:
        return "sem_dado"
    if pct >= _LIMIAR_ADEQUADO:
        return "adequado"
    if pct >= _LIMIAR_ATENCAO:
        return "atencao"
    return "alerta"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    *,
    periodo: str | None,
    agua_pct: float | None,
    esgoto_pct: float | None,
) -> AguaViva:
    """Monta o AguaViva a partir dos dados disponíveis; degrada graciosamente."""
    return AguaViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=periodo,
        agua_pct=agua_pct,
        esgoto_pct=esgoto_pct,
        nivel_agua=classificar_nivel(agua_pct),
        nivel_esgoto=classificar_nivel(esgoto_pct),
    )
