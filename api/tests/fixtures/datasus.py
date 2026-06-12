"""Fixture do DATASUS/SIH-RD — colunas mínimas do produto, forma fiel ao bruto real.

Forma confirmada no ADR-0024 contra RDRO2604 (9670 linhas, 114 colunas, 2026-06-11) e
confirmada contra RDRO2603 em produção (2026-06-12):
  - MUNIC_RES: município de RESIDÊNCIA do paciente (IBGE 6 dígitos; 355030=SP, 350950=Campinas).
  - MUNIC_MOV: município onde ocorreu a internação (pode diferir de MUNIC_RES).
  - DIAG_PRINC: diagnóstico principal (CID-10). Grupo J = respiratório (J00–J99).
  - DT_INTER: data de internação em formato **YYYYMMDD** (ex.: "20260903") — SEM traços.
    ATENÇÃO: formato é YYYYMMDD, não YYYY-MM-DD. Fixture anterior usava traços e
    mascarava o bug de parsing em produção — corrigida em 2026-06-12.
  - ANO_CMPT / MES_CMPT: competência de faturamento (mistura meses; NOT usado para o mês).

Linha I10 (hipertensão) exercita o filtro DIAG_PRINC LIKE 'J%'.
Linha 3 (SP residente em internação fora) demonstra que MUNIC_RES ≠ MUNIC_MOV é possível.
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

# Colunas mínimas: produto + forma real (sem quasi-identificadores de pessoa).
# DT_INTER em YYYYMMDD (formato real do DBF DATASUS — confirmado 2026-06-12).
_CABECALHO = "MUNIC_RES,MUNIC_MOV,DIAG_PRINC,DT_INTER,ANO_CMPT,MES_CMPT"
_LINHAS = [
    "355030,355030,J189,20260903,2026,9",  # SP — pneumonia
    "355030,355030,J450,20260907,2026,9",  # SP — asma
    "355030,350140,J22,20260911,2026,9",  # SP residente, internação fora (MUNIC_MOV ≠ RES)
    "355030,355030,I10,20260915,2026,9",  # SP — hipertensão (fora do grupo J → filtrado)
    "350950,350950,J189,20260904,2026,9",  # Campinas — pneumonia
    "350950,350950,J450,20260918,2026,9",  # Campinas — asma
]
AMOSTRA = ("\n".join([_CABECALHO, *_LINHAS]) + "\n").encode("utf-8")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://datasus_sih"
