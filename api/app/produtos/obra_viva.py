"""ObraViva (TRANSP-05) — contratações públicas municipais via PNCP.

Pergunta do produto: **quanto o município está contratando publicamente e em que intensidade
relativa à sua população?**

Usa o indicador ``compras.contratos.valor_total`` (soma do ``valorGlobal`` dos contratos
publicados no PNCP pelo órgão cuja unidade tem código IBGE do município). Lógica **pura**
— sem rede/DB.

HONESTIDADE:
- O PNCP reúne contratos federais, estaduais e municipais **publicados no portal** — municípios
  que ainda não aderiram ao PNCP ou publicam em portais próprios ficam subcontados. Ausência de
  dado ≠ ausência de contratação.
- O valor agregado inclui todos os tipos de contrato (obras, serviços, bens) — não distingue
  obra pública de compra de material de escritório.
- Cobre os contratos pela unidade **publicadora** (órgão com o IBGE do município), não
  necessariamente onde o serviço é prestado.
- Lag: dados do PNCP chegam com dias a semanas de atraso; o acervo reflete o exercício ingerido.
- Dupla face (§17): agregado por município — nunca identifica fornecedores (TRANSP-02/03 = outro
  produto); use como contexto de intensidade de contratação, não como ranking de eficiência.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Nível de intensidade de contratação pública per capita.
NivelContratos = Literal["elevado", "moderado", "baixo", "sem_dado"]

# Limiares provisórios (R$/hab/ano). Calibrar com distribuição real nacional.
# Referência: gasto municipal médio ≈ R$ 3.000–6.000/hab/ano; contratos ≈ 30–50 % disso.
_LIMIAR_ELEVADO = 3_000.0  # ≥ R$ 3.000/hab → alta intensidade
_LIMIAR_MODERADO = 500.0  # R$ 500–2.999/hab → intensidade moderada

NOTA_HONESTA = (
    "Soma do valor global de contratos publicados no PNCP pelo município no exercício. "
    "PNCP é o portal unificado de contratações do governo federal, estados e municípios, "
    "mas a adesão ainda não é universal — ausência de dado não significa ausência de "
    "contratação. O valor agrega todos os tipos (obras, serviços, bens) e cobre contratos "
    "onde a unidade publicadora tem o código IBGE do município. "
    "Limiares provisórios — a calibrar com a distribuição nacional. "
    "Agregado por município, sem identificação de fornecedores (dupla face §17, TRANSP-05)."
)


@dataclass(frozen=True)
class ObraViva:
    """Contrato: contratações públicas municipais via PNCP por município."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY do exercício mais recente com dado
    valor_contratos: int | None  # R$ total dos contratos do exercício
    valor_por_hab: float | None  # R$/hab = valor_contratos / populacao
    nivel: NivelContratos


def classificar_nivel_contratos(valor_por_hab: float | None) -> NivelContratos:
    """Classifica a intensidade de contratação per capita."""
    if valor_por_hab is None:
        return "sem_dado"
    if valor_por_hab >= _LIMIAR_ELEVADO:
        return "elevado"
    if valor_por_hab >= _LIMIAR_MODERADO:
        return "moderado"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    periodo: str | None,
    valor_contratos: int | None,
) -> ObraViva:
    """Monta o ObraViva a partir dos dados disponíveis; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_contratos is not None and populacao and populacao > 0:
        por_hab = round(valor_contratos / populacao, 2)

    return ObraViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        periodo=periodo,
        valor_contratos=valor_contratos,
        valor_por_hab=por_hab,
        nivel=classificar_nivel_contratos(por_hab),
    )
