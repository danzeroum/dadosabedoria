"""Seed inicial — governança/dimensões + fatos da Onda 1.

Regra do produto: os FATOS passam pelo MESMO caminho ouro da ingestão (``escrever_ouro``:
supressão + linhagem) — nada de INSERT cru em ``valor``. As dimensões (base_legal, fonte,
territorio, indicador) são upserts idempotentes — são metadados de governança, não fatos
sujeitos a k-anonimato.

Inclui de propósito uma célula sub-limiar de indicador de origem sensível (Campinas), para que a
supressão seja exercida ponta a ponta já no seed (ADR-0004).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import tables as t
from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro
from app.ingestao.supressao import MetaIndicadorSupressao

# --------------------------------------------------------------------------- dimensões

BASE_LEGAL: list[dict[str, str]] = [
    {
        "codigo": "obrigacao_legal",
        "artigo": "LGPD Art. 7, II",
        "hipotese": "Cumprimento de obrigação legal",
        "justificativa": (
            "Dados estatísticos públicos coletados por órgão governamental no exercício de "
            "política pública; reuso de dado já público e anonimizado."
        ),
    },
    {
        "codigo": "consentimento",
        "artigo": "LGPD Art. 7, I",
        "hipotese": "Consentimento do titular",
        "justificativa": (
            "Cidadão que opta por receber alertas fornece contato e localização para finalidade "
            "específica e informada."
        ),
    },
    {
        "codigo": "consentimento_sensivel",
        "artigo": "LGPD Art. 11, I",
        "hipotese": "Consentimento específico e destacado",
        "justificativa": (
            "Condição de saúde informada pelo cidadão (ex.: asmático) para personalizar alertas; "
            "dado sensível, consentimento explícito e em destaque."
        ),
    },
]

FONTES: list[dict[str, Any]] = [
    {
        "codigo": "ibge",
        "nome": "IBGE Agregados/Malhas",
        "orgao": "IBGE",
        "url_doc": "https://servicodados.ibge.gov.br/api/docs",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "irregular",
        "lag_tipico_dias": None,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "novo_caged",
        "nome": "Novo CAGED",
        "orgao": "MTE/PDET",
        "url_doc": "https://pdet.mte.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 40,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "bcb_sgs",
        "nome": "BCB SGS",
        "orgao": "Banco Central do Brasil",
        "url_doc": "https://api.bcb.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 30,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "bcb_estban",
        "nome": "BCB ESTBAN",
        "orgao": "Banco Central do Brasil",
        "url_doc": "https://api.bcb.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 60,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "datasus_sih",
        "nome": "SIH/SUS",
        "orgao": "Ministério da Saúde/DATASUS",
        "url_doc": "https://datasus.saude.gov.br",
        "licenca": "LAI/Dados Abertos (anonimizado)",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 90,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "siconfi",
        "nome": "SICONFI/STN",
        "orgao": "Tesouro Nacional (STN)",
        "url_doc": "https://apidatalake.tesouro.gov.br/ords/siconfi/docs",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "inep",
        "nome": "INEP — Censo Escolar",
        "orgao": "INEP/MEC",
        "url_doc": "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "pncp",
        "nome": "PNCP — Contratações Públicas",
        "orgao": "PNCP (MGI)",
        "url_doc": "https://pncp.gov.br/api/consulta/swagger-ui/index.html",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "diaria",
        "lag_tipico_dias": 30,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "snis",
        "nome": "SNIS — Série Histórica",
        "orgao": "MDR/SNSA",
        "url_doc": "http://app4.mdr.gov.br/serieHistorica/",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 548,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "aneel",
        "nome": "ANEEL — Indicadores de Qualidade DEC/FEC",
        "orgao": "ANEEL",
        "url_doc": "https://dadosabertos.aneel.gov.br/dataset/indicadores-qualidade-distribuicao-dec-fec",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "ana",
        "nome": "ANA — Monitor de Secas",
        "orgao": "ANA",
        "url_doc": "https://monitordesecas.ana.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 60,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "ibge_pam",
        "nome": "IBGE PAM — Pesquisa Agrícola Municipal",
        "orgao": "IBGE",
        "url_doc": "https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/9117-producao-agricola-municipal.html",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "sisvan",
        "nome": "SISVAN — Sistema de Vigilância Alimentar e Nutricional",
        "orgao": "Ministério da Saúde",
        "url_doc": "https://sisvan.saude.gov.br/",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "sinan",
        "nome": "SINAN — Sistema de Informação de Agravos de Notificação",
        "orgao": "Ministério da Saúde",
        "url_doc": "https://datasus.saude.gov.br/transferencia-de-arquivos/",
        "licenca": "LAI/Dados Abertos (anonimizado)",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
]

# (codigo_ibge, nome, nivel, uf, populacao, codigo_ibge_do_pai)
TERRITORIOS = [
    ("1", "Brasil", "pais", None, 203080756, None),
    ("3", "Região Sudeste", "regiao", None, None, "1"),
    ("33", "Rio de Janeiro", "uf", "RJ", None, "3"),
    ("35", "São Paulo", "uf", "SP", None, "3"),
    ("3304557", "Rio de Janeiro", "municipio", "RJ", 6211223, "33"),
    ("3509502", "Campinas", "municipio", "SP", 1213792, "35"),
    ("3550308", "São Paulo", "municipio", "SP", 11451245, "35"),
]

INDICADORES: list[dict[str, Any]] = [
    {
        "codigo": "trabalho.emprego.saldo_caged",
        "nome": "Saldo de empregos formais",
        "descricao": "Admissões menos desligamentos com carteira no mês.",
        "dominio": "trabalho",
        "subdominio": "emprego_formal",
        "unidade": "contagem",
        "polaridade": "maior_melhor",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "novo_caged",
        "codigo_externo": "CNAE",
        "metodologia": "Soma de admissões menos desligamentos do Novo CAGED por município/mês.",
    },
    {
        "codigo": "trabalho.emprego.salario_medio_admissao",
        "nome": "Salário médio de admissão",
        "descricao": (
            "Salário médio declarado nas admissões formais do mês (CAGEDMOV). "
            "Não inclui desligamentos."
        ),
        "dominio": "trabalho",
        "subdominio": "emprego_formal",
        "unidade": "reais",
        "polaridade": "maior_melhor",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "novo_caged",
        "codigo_externo": "salário",
        "metodologia": (
            "Média dos salários declarados nos registros de admissão (saldomovimentação=1) "
            "do Novo CAGED por município/mês."
        ),
    },
    {
        "codigo": "credito.operacoes.saldo_total",
        "nome": "Saldo de operações de crédito",
        "descricao": "Saldo total de operações de crédito do SFN por município/mês (ESTBAN).",
        "dominio": "credito",
        "subdominio": "operacoes",
        "unidade": "reais",
        "polaridade": "neutra",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "bcb_estban",
        "codigo_externo": None,
        "metodologia": "Soma dos saldos de operações de crédito do ESTBAN por município/mês.",
    },
    {
        "codigo": "saude.resp.internacoes_j",
        "nome": "Internações por doenças respiratórias",
        "descricao": "Internações no SUS com CID-10 do grupo J (respiratórias) por mês.",
        "dominio": "saude",
        "subdominio": "respiratorio",
        "unidade": "contagem",
        "polaridade": "menor_melhor",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 5,
        "classificacao": "nao_pessoal",
        "origem_sensivel": True,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "datasus_sih",
        "codigo_externo": "CID-10:J00-J99",
        "metodologia": (
            "Contagem de AIH com diagnóstico principal no grupo J do SIH/SUS por município/mês."
        ),
    },
    {
        "codigo": "financas.transferencias.correntes",
        "nome": "Transferências correntes recebidas",
        "descricao": "Transferências correntes recebidas pelo município no exercício (DCA).",
        "dominio": "financas",
        "subdominio": "transferencias",
        "unidade": "reais",
        "polaridade": "neutra",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "siconfi",
        "codigo_externo": "DCA",
        "metodologia": (
            "Soma das Transferências Correntes da DCA (SICONFI/STN) por município/exercício."
        ),
    },
    {
        "codigo": "educacao.matriculas.fundamental",
        "nome": "Matrículas no ensino fundamental",
        "descricao": "Matrículas no ensino fundamental por município (Censo Escolar/INEP).",
        "dominio": "educacao",
        "subdominio": "matriculas",
        "unidade": "contagem",
        "polaridade": "neutra",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "inep",
        "codigo_externo": "QT_MAT_FUND",
        "metodologia": (
            "Soma das matrículas no ensino fundamental (QT_MAT_FUND) do Censo Escolar por "
            "município/ano."
        ),
    },
    {
        "codigo": "compras.contratos.valor_total",
        "nome": "Valor total de contratos públicos",
        "descricao": "Soma do valor dos contratos públicos do município no ano (PNCP).",
        "dominio": "compras",
        "subdominio": "contratos",
        "unidade": "reais",
        "polaridade": "neutra",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "pncp",
        "codigo_externo": "valorGlobal",
        "metodologia": (
            "Soma do valorGlobal dos contratos do PNCP por município/ano (unidadeOrgao.codigoIbge)."
        ),
    },
    {
        "codigo": "saneamento.agua.atendimento_pct",
        "nome": "Índice de atendimento de água",
        "descricao": "Percentual da população atendida com abastecimento de água (IN023_AE, SNIS).",
        "dominio": "saneamento",
        "subdominio": "agua",
        "unidade": "pct",
        "polaridade": "maior_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "snis",
        "codigo_externo": "IN023_AE",
        "metodologia": (
            "IN023_AE do SNIS: (pop. urbana atendida com água / pop. urbana total) × 100, "
            "por prestador declarante ao SNIS por município/ano."
        ),
    },
    {
        "codigo": "saneamento.esgoto.coleta_pct",
        "nome": "Índice de coleta de esgoto",
        "descricao": "Percentual da população com coleta de esgoto (IN015_AE, SNIS).",
        "dominio": "saneamento",
        "subdominio": "esgoto",
        "unidade": "pct",
        "polaridade": "maior_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "snis",
        "codigo_externo": "IN015_AE",
        "metodologia": (
            "IN015_AE do SNIS: (pop. urbana com coleta de esgoto / pop. urbana total) × 100, "
            "por prestador declarante ao SNIS por município/ano."
        ),
    },
    {
        "codigo": "energia.qualidade.dec",
        "nome": "DEC — Duração Equivalente de Interrupção",
        "descricao": "Horas de interrupção equivalentes por consumidor/ano (ANEEL).",
        "dominio": "energia",
        "subdominio": "qualidade",
        "unidade": "horas",
        "polaridade": "menor_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "aneel",
        "codigo_externo": "DEC",
        "metodologia": (
            "Média do DEC (horas de interrupção por consumidor/ano) das distribuidoras "
            "reguladas pela ANEEL no município. Forma a confirmar na 1ª busca real."
        ),
    },
    {
        "codigo": "energia.qualidade.fec",
        "nome": "FEC — Frequência Equivalente de Interrupção",
        "descricao": "Número de interrupções equivalentes por consumidor/ano (ANEEL).",
        "dominio": "energia",
        "subdominio": "qualidade",
        "unidade": "contagem",
        "polaridade": "menor_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "aneel",
        "codigo_externo": "FEC",
        "metodologia": (
            "Média do FEC (interrupções por consumidor/ano) das distribuidoras "
            "reguladas pela ANEEL no município. Forma a confirmar na 1ª busca real."
        ),
    },
    {
        "codigo": "saneamento.agua.seca_indice",
        "nome": "Índice de Seca — Monitor de Secas ANA",
        "descricao": (
            "Índice numérico de seca (0–5) derivado da classificação do Monitor de Secas da ANA: "
            "Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5. Valor anual = pior mês do exercício."
        ),
        "dominio": "saneamento",
        "subdominio": "agua",
        "unidade": "indice",
        "polaridade": "menor_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "ana",
        "codigo_externo": "seca_indice",
        "metodologia": (
            "Classificação mensal de seca por município (Normal, D0–D4), metodologia USDM "
            "adaptada pela ANA. Convertida em índice 0–5; valor anual = máximo mensal. "
            "Forma a confirmar na 1ª busca real (monitordesecas.ana.gov.br)."
        ),
    },
    {
        "codigo": "alimentacao.producao.valor_total",
        "nome": "Valor da produção agrícola municipal",
        "descricao": (
            "Valor total da produção agrícola municipal (lavouras temporárias + permanentes)"
            " em BRL por município/ano. Fonte: IBGE PAM, tabelas 1612 e 1613, variável 762."
        ),
        "dominio": "alimentacao",
        "subdominio": "producao",
        "unidade": "BRL",
        "polaridade": "maior_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "ibge_pam",
        "codigo_externo": "PAM_762",
        "metodologia": (
            "Soma do Valor da Produção (variável 762, Mil Reais) das lavouras temporárias "
            "(tabela 1612) e permanentes (tabela 1613) do IBGE PAM por município/ano. "
            "Convertido de Mil BRL para BRL (× 1000). "
            "Forma a confirmar na 1ª busca real (servicodados.ibge.gov.br)."
        ),
    },
    {
        "codigo": "alimentacao.nutricao.baixo_peso_pct",
        "nome": "Prevalência de baixo peso em crianças < 5 anos",
        "descricao": (
            "% de crianças menores de 5 anos com magreza ou magreza acentuada "
            "(CO_ESTADO_NUTRI_CRIANCA in [1,2]) entre as acompanhadas pelo SISVAN/MS "
            "no município. Proxy de fome oculta (insegurança nutricional)."
        ),
        "dominio": "alimentacao",
        "subdominio": "nutricao",
        "unidade": "%",
        "polaridade": "menor_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 5,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "sisvan",
        "codigo_externo": "SISVAN_baixo_peso_pct",
        "metodologia": (
            "% de crianças < 5 anos com magreza acentuada (cód. 1) + magreza (cód. 2) "
            "no estado nutricional do SISVAN, por município/ano. "
            "Forma a confirmar na 1ª busca real (s3.sa-east-1.amazonaws.com/ckan.saude.gov.br)."
        ),
    },
    {
        "codigo": "saude.materno.gestante_baixo_peso_pct",
        "nome": "Gestantes com baixo peso (%)",
        "descricao": (
            "% de gestantes com baixo peso (CO_ESTADO_NUTRI_GESTANTE = 1) entre as "
            "acompanhadas pelo SISVAN/MS no município. Indicador de risco nutricional materno "
            "(SAUDE-03 Sentinela Materna). Origem sensível: supressão k-anon n≥5."
        ),
        "dominio": "saude",
        "subdominio": "materno",
        "unidade": "%",
        "polaridade": "menor_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 5,
        "classificacao": "nao_pessoal",
        "origem_sensivel": True,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "sisvan",
        "codigo_externo": "SISVAN_gestante_baixo_peso_pct",
        "metodologia": (
            "% de gestantes com baixo peso (cód. 1) no estado nutricional do SISVAN "
            "(CO_ESTADO_NUTRI_GESTANTE), por município/ano. Cobre apenas gestantes "
            "acompanhadas pelo SISVAN/CadÚnico — não é censo. "
            "Forma a confirmar na 1ª busca real (s3.sa-east-1.amazonaws.com/ckan.saude.gov.br)."
        ),
    },
    {
        "codigo": "saude.arboviroses.dengue_casos",
        "nome": "Casos confirmados de dengue",
        "descricao": (
            "Casos confirmados de dengue (CLASSI_FIN ∈ {1,2,3}) por município/ano. "
            "Inclui: dengue clássico (1), com sinais de alarme (2) e grave (3). "
            "Fonte: SINAN (Sistema de Informação de Agravos de Notificação/MS)."
        ),
        "dominio": "saude",
        "subdominio": "arboviroses",
        "unidade": "casos",
        "polaridade": "menor_melhor",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 5,
        "classificacao": "nao_pessoal",
        "origem_sensivel": True,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "sinan",
        "codigo_externo": "SINAN_DENGBR_CLASSI_FIN",
        "metodologia": (
            "Contagem de registros com CLASSI_FIN ∈ {1,2,3} no arquivo DENGBR{YY}.dbc "
            "do SINAN/DATASUS, por município de residência (ID_MUNICIP, IBGE 6 dígitos) e "
            "ano de notificação (NU_ANO). K-anonimato: n_minimo=5 (saúde sensível). "
            "Forma a confirmar na 1ª busca real (ftp.datasus.gov.br)."
        ),
    },
]


async def _upsert(conn: AsyncConnection, tabela: Table, conflito: list[str], valores: dict) -> int:
    ins = pg_insert(tabela).values(**valores)
    set_ = {k: getattr(ins.excluded, k) for k in valores if k not in conflito}
    stmt = ins.on_conflict_do_update(index_elements=conflito, set_=set_).returning(tabela.c.id)
    res = await conn.execute(stmt)
    return int(res.scalar_one())


async def executar_seed(conn: AsyncConnection) -> dict[str, int]:
    """Semeia dimensões (upsert) e fatos (via ``escrever_ouro``). Idempotente."""
    bl_ids = {r["codigo"]: await _upsert(conn, t.base_legal, ["codigo"], r) for r in BASE_LEGAL}

    fonte_ids: dict[str, int] = {}
    for f in FONTES:
        row = {k: v for k, v in f.items() if k != "base_legal"}
        row["base_legal_id"] = bl_ids[f["base_legal"]]
        fonte_ids[f["codigo"]] = await _upsert(conn, t.fonte, ["codigo"], row)

    terr_ids: dict[str, int] = {}
    for codigo_ibge, nome, nivel, uf, pop, pai in TERRITORIOS:
        row = {
            "codigo_ibge": codigo_ibge,
            "nome": nome,
            "nivel": nivel,
            "uf": uf,
            "populacao": pop,
            "pai_id": terr_ids[pai] if pai else None,
        }
        terr_ids[codigo_ibge] = await _upsert(conn, t.territorio, ["codigo_ibge"], row)

    ind_ids: dict[str, int] = {}
    meta: dict[int, MetaIndicadorSupressao] = {}
    for ind in INDICADORES:
        row = {k: v for k, v in ind.items() if k not in ("base_legal", "fonte")}
        row["base_legal_id"] = bl_ids[ind["base_legal"]]
        row["fonte_id"] = fonte_ids[ind["fonte"]]
        iid = await _upsert(conn, t.indicador, ["codigo"], row)
        ind_ids[ind["codigo"]] = iid
        meta[iid] = MetaIndicadorSupressao(
            n_minimo=int(ind["n_minimo"]), origem_sensivel=bool(ind["origem_sensivel"])
        )

    await _semear_fatos(conn, fonte_ids, terr_ids, ind_ids, meta)
    return {"indicadores": len(ind_ids), "territorios": len(terr_ids), "fontes": len(fonte_ids)}


async def _tem_dados_reais(conn: AsyncConnection, ind_id: int) -> bool:
    """Retorna True se o indicador já tem linhagem de ingestão real (responsavel != 'seed')."""
    from sqlalchemy import func, select

    stmt = (
        select(func.count())
        .select_from(t.linhagem)
        .where(t.linhagem.c.indicador_id == ind_id, t.linhagem.c.responsavel != "seed")
    )
    return int((await conn.execute(stmt)).scalar_one()) > 0


async def _semear_fatos(
    conn: AsyncConnection,
    fonte_ids: dict[str, int],
    terr_ids: dict[str, int],
    ind_ids: dict[str, int],
    meta: dict[int, MetaIndicadorSupressao],
) -> None:
    grav = GravadorOuro(conn)  # usa SupressaoKAnonimato por padrão

    sp = terr_ids["3550308"]
    cps = terr_ids["3509502"]

    # EMPREGO (saldo CAGED): n_amostra None, n_minimo 0 → nunca suprimido.
    caged = ind_ids["trabalho.emprego.saldo_caged"]
    f_caged = fonte_ids["novo_caged"]
    if not await _tem_dados_reais(conn, caged):
        caged_cels = [
            CelulaOuro(caged, sp, date(2026, 2, 1), "mensal", Decimal(8200), None, 5, f_caged),
            CelulaOuro(caged, sp, date(2026, 3, 1), "mensal", Decimal(-15400), None, 5, f_caged),
            CelulaOuro(caged, sp, date(2026, 4, 1), "mensal", Decimal(-9100), None, 5, f_caged),
            CelulaOuro(caged, cps, date(2026, 2, 1), "mensal", Decimal(1200), None, 5, f_caged),
            CelulaOuro(caged, cps, date(2026, 3, 1), "mensal", Decimal(-800), None, 5, f_caged),
            CelulaOuro(caged, cps, date(2026, 4, 1), "mensal", Decimal(-300), None, 5, f_caged),
        ]
        await grav.escrever_ouro(
            caged_cels,
            meta,
            ContextoLinhagem(f_caged, caged, "seed Onda 1: prata->ouro (saldo CAGED)", "seed"),
        )

    # SALÁRIO MÉDIO DE ADMISSÃO (Novo CAGED): reais; n_minimo 0.
    sal = ind_ids["trabalho.emprego.salario_medio_admissao"]
    if not await _tem_dados_reais(conn, sal):
        sal_cels = [
            CelulaOuro(sal, sp, date(2026, 2, 1), "mensal", Decimal("2380.00"), None, 5, f_caged),
            CelulaOuro(sal, sp, date(2026, 3, 1), "mensal", Decimal("2410.00"), None, 5, f_caged),
            CelulaOuro(sal, sp, date(2026, 4, 1), "mensal", Decimal("2450.00"), None, 5, f_caged),
            CelulaOuro(sal, cps, date(2026, 2, 1), "mensal", Decimal("2750.00"), None, 5, f_caged),
            CelulaOuro(sal, cps, date(2026, 3, 1), "mensal", Decimal("2800.00"), None, 5, f_caged),
            CelulaOuro(sal, cps, date(2026, 4, 1), "mensal", Decimal("2820.00"), None, 5, f_caged),
        ]
        await grav.escrever_ouro(
            sal_cels,
            meta,
            ContextoLinhagem(
                f_caged, sal, "seed Onda 3: prata->ouro (salário médio admissão CAGED)", "seed"
            ),
        )

    # CRÉDITO (ESTBAN): reais; n_minimo 0.
    cred = ind_ids["credito.operacoes.saldo_total"]
    f_estban = fonte_ids["bcb_estban"]
    if not await _tem_dados_reais(conn, cred):
        # SP e Campinas nos mesmos meses → o IVM tem ≥2 municípios (mapa com contraste).
        # Campinas com crédito maior (menos vulnerável em finanças) — dado ilustrativo de seed.
        cred_cels = [
            CelulaOuro(cred, sp, date(2026, 2, 1), "mensal", Decimal("1.00e11"), None, 4, f_estban),
            CelulaOuro(cred, sp, date(2026, 3, 1), "mensal", Decimal("1.01e11"), None, 4, f_estban),
            CelulaOuro(cred, sp, date(2026, 4, 1), "mensal", Decimal("0.99e11"), None, 4, f_estban),
            CelulaOuro(
                cred, cps, date(2026, 2, 1), "mensal", Decimal("2.00e11"), None, 4, f_estban
            ),
            CelulaOuro(
                cred, cps, date(2026, 3, 1), "mensal", Decimal("2.01e11"), None, 4, f_estban
            ),
            CelulaOuro(
                cred, cps, date(2026, 4, 1), "mensal", Decimal("1.99e11"), None, 4, f_estban
            ),
        ]
        await grav.escrever_ouro(
            cred_cels,
            meta,
            ContextoLinhagem(f_estban, cred, "seed Onda 1: prata->ouro (crédito ESTBAN)", "seed"),
        )

    # SAÚDE (origem sensível): SP acima do limiar; Campinas n_amostra=3 < 5 → SUPRIMIDO.
    sau = ind_ids["saude.resp.internacoes_j"]
    f_sih = fonte_ids["datasus_sih"]
    if not await _tem_dados_reais(conn, sau):
        sau_cels = [
            CelulaOuro(sau, sp, date(2026, 4, 1), "mensal", Decimal(310), 310, 4, f_sih),
            CelulaOuro(sau, sp, date(2026, 5, 1), "mensal", Decimal(420), 420, 4, f_sih),
            CelulaOuro(sau, sp, date(2026, 6, 1), "mensal", Decimal(660), 660, 4, f_sih),
            CelulaOuro(sau, cps, date(2026, 4, 1), "mensal", Decimal(3), 3, 3, f_sih),  # < limiar
        ]
        await grav.escrever_ouro(
            sau_cels,
            meta,
            ContextoLinhagem(f_sih, sau, "seed Onda 1: prata->ouro (internações resp.)", "seed"),
        )

    # FINANÇAS (SICONFI/DCA, anual): transferências correntes por município/exercício. n_minimo 0.
    fin = ind_ids["financas.transferencias.correntes"]
    f_siconfi = fonte_ids["siconfi"]
    if not await _tem_dados_reais(conn, fin):
        fin_cels = [
            CelulaOuro(fin, sp, date(2024, 1, 1), "anual", Decimal("1.50e9"), None, 4, f_siconfi),
            CelulaOuro(fin, cps, date(2024, 1, 1), "anual", Decimal("2.50e8"), None, 4, f_siconfi),
        ]
        await grav.escrever_ouro(
            fin_cels,
            meta,
            ContextoLinhagem(
                f_siconfi, fin, "seed Onda 2A: prata->ouro (SICONFI transferências)", "seed"
            ),
        )

    # EDUCAÇÃO (INEP/Censo Escolar, anual): matrículas no fundamental por município/ano.
    edu = ind_ids["educacao.matriculas.fundamental"]
    f_inep = fonte_ids["inep"]
    if not await _tem_dados_reais(conn, edu):
        edu_cels = [
            CelulaOuro(edu, sp, date(2024, 1, 1), "anual", Decimal(980000), None, 4, f_inep),
            CelulaOuro(edu, cps, date(2024, 1, 1), "anual", Decimal(150000), None, 4, f_inep),
        ]
        await grav.escrever_ouro(
            edu_cels,
            meta,
            ContextoLinhagem(f_inep, edu, "seed Onda 2A: prata->ouro (INEP matrículas)", "seed"),
        )

    # COMPRAS (PNCP/contratos, anual): valor de contratos públicos por município/ano. n_minimo 0.
    com = ind_ids["compras.contratos.valor_total"]
    f_pncp = fonte_ids["pncp"]
    if not await _tem_dados_reais(conn, com):
        com_cels = [
            CelulaOuro(com, sp, date(2024, 1, 1), "anual", Decimal("2.00e9"), None, 4, f_pncp),
            CelulaOuro(com, cps, date(2024, 1, 1), "anual", Decimal("3.00e8"), None, 4, f_pncp),
        ]
        await grav.escrever_ouro(
            com_cels,
            meta,
            ContextoLinhagem(f_pncp, com, "seed Onda 2A: prata->ouro (PNCP contratos)", "seed"),
        )

    # ENERGIA (ANEEL DEC/FEC, anual): qualidade do fornecimento elétrico por município/ano.
    dec = ind_ids["energia.qualidade.dec"]
    fec = ind_ids["energia.qualidade.fec"]
    f_aneel = fonte_ids["aneel"]
    if not await _tem_dados_reais(conn, dec):
        dec_cels = [
            CelulaOuro(dec, sp, date(2023, 1, 1), "anual", Decimal("3.52"), None, 4, f_aneel),
            CelulaOuro(dec, cps, date(2023, 1, 1), "anual", Decimal("5.75"), None, 4, f_aneel),
        ]
        await grav.escrever_ouro(
            dec_cels,
            meta,
            ContextoLinhagem(f_aneel, dec, "seed Onda 2C: prata->ouro (ANEEL DEC)", "seed"),
        )
    if not await _tem_dados_reais(conn, fec):
        fec_cels = [
            CelulaOuro(fec, sp, date(2023, 1, 1), "anual", Decimal("4.21"), None, 4, f_aneel),
            CelulaOuro(fec, cps, date(2023, 1, 1), "anual", Decimal("5.10"), None, 4, f_aneel),
        ]
        await grav.escrever_ouro(
            fec_cels,
            meta,
            ContextoLinhagem(f_aneel, fec, "seed Onda 2C: prata->ouro (ANEEL FEC)", "seed"),
        )

    # SANEAMENTO/SECA (ANA Monitor de Secas, anual): índice de seca por município/ano.
    seca = ind_ids["saneamento.agua.seca_indice"]
    f_ana = fonte_ids["ana"]
    if not await _tem_dados_reais(conn, seca):
        seca_cels = [
            # SP: Normal (0.0) — sem seca registrada
            CelulaOuro(seca, sp, date(2023, 1, 1), "anual", Decimal("0.0"), None, 3, f_ana),
            # Campinas: D0 (1.0) — Anormalmente Seco
            CelulaOuro(seca, cps, date(2023, 1, 1), "anual", Decimal("1.0"), None, 3, f_ana),
        ]
        await grav.escrever_ouro(
            seca_cels,
            meta,
            ContextoLinhagem(f_ana, seca, "seed Onda 2C: prata->ouro (ANA seca_indice)", "seed"),
        )

    # ALIMENTAÇÃO (IBGE PAM, anual): valor da produção agrícola por município/ano.
    producao = ind_ids["alimentacao.producao.valor_total"]
    f_pam = fonte_ids["ibge_pam"]
    if not await _tem_dados_reais(conn, producao):
        producao_cels = [
            # SP: 5000+1000 Mil BRL → 6.000.000 BRL (fixture: grau-demo)
            CelulaOuro(producao, sp, date(2023, 1, 1), "anual", Decimal("6000000"), None, 3, f_pam),
            # Campinas: 8000+2000 Mil BRL → 10.000.000 BRL (fixture: grau-demo)
            CelulaOuro(
                producao, cps, date(2023, 1, 1), "anual", Decimal("10000000"), None, 3, f_pam
            ),
        ]
        await grav.escrever_ouro(
            producao_cels,
            meta,
            ContextoLinhagem(
                f_pam, producao, "seed ALIM-01: prata->ouro (IBGE PAM valor_brl)", "seed"
            ),
        )

    # ALIMENTAÇÃO (SISVAN, anual): % de crianças < 5 com baixo peso por município/ano.
    baixo_peso = ind_ids["alimentacao.nutricao.baixo_peso_pct"]
    f_sisvan = fonte_ids["sisvan"]
    if not await _tem_dados_reais(conn, baixo_peso):
        bp_cels = [
            # SP: 2% → moderado (fixture: grau-demo)
            CelulaOuro(baixo_peso, sp, date(2023, 1, 1), "anual", Decimal("2.0"), 50, 3, f_sisvan),
            # Campinas: 5% → elevado (fixture: grau-demo)
            CelulaOuro(baixo_peso, cps, date(2023, 1, 1), "anual", Decimal("5.0"), 20, 3, f_sisvan),
        ]
        await grav.escrever_ouro(
            bp_cels,
            meta,
            ContextoLinhagem(
                f_sisvan, baixo_peso, "seed ALIM-02: prata->ouro (SISVAN baixo_peso_pct)", "seed"
            ),
        )

    # SAÚDE MATERNA (SISVAN gestante, anual): % de gestantes com baixo peso por município/ano.
    gestante_bp = ind_ids["saude.materno.gestante_baixo_peso_pct"]
    if not await _tem_dados_reais(conn, gestante_bp):
        gbp_cels = [
            # SP: 3.0% → baixo (fixture: grau-demo, 1 baixo peso em 30)
            CelulaOuro(gestante_bp, sp, date(2023, 1, 1), "anual", Decimal("3.0"), 30, 3, f_sisvan),
            # Rio: 25.0% → crítico (fixture: grau-demo, 10 baixo peso em 40)
            # Rio não está no seed de territórios (só SP e Campinas estão) — usamos Campinas
            # Campinas: 15.0% → elevado (fixture: grau-demo, 3 baixo peso em 20)
            CelulaOuro(
                gestante_bp, cps, date(2023, 1, 1), "anual", Decimal("15.0"), 20, 3, f_sisvan
            ),
        ]
        await grav.escrever_ouro(
            gbp_cels,
            meta,
            ContextoLinhagem(
                f_sisvan,
                gestante_bp,
                "seed SAUDE-03: prata->ouro (SISVAN gestante_baixo_peso_pct)",
                "seed",
            ),
        )

    # SAÚDE/ARBOVIROSES (SINAN, anual): casos confirmados de dengue por município/ano.
    dengue = ind_ids["saude.arboviroses.dengue_casos"]
    f_sinan = fonte_ids["sinan"]
    if not await _tem_dados_reais(conn, dengue):
        # SP: 8000 casos → incidência ~70/100k (elevado); fixture: grau-demo.
        # Campinas: None (suprimido, n_amostra=3 < 5).
        # Rio não está no seed de territórios, então só SP.
        dengue_cels = [
            CelulaOuro(dengue, sp, date(2023, 1, 1), "anual", Decimal(8000), 8000, 3, f_sinan),
            # Campinas com n_amostra=3 → abaixo de n_minimo=5 → suprimido pelo k-anon
            CelulaOuro(dengue, cps, date(2023, 1, 1), "anual", Decimal(3), 3, 3, f_sinan),
        ]
        await grav.escrever_ouro(
            dengue_cels,
            meta,
            ContextoLinhagem(
                f_sinan, dengue, "seed SAUDE-02: prata->ouro (SINAN dengue_casos)", "seed"
            ),
        )


async def main() -> None:
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    async with connect(settings.database_url) as conn:
        resumo = await executar_seed(conn)
    await refrescar_ivm()  # popula a MV do IVM após o seed (fora da transação)
    print(f"seed concluído: {resumo}")  # noqa: T201 (saída de CLI)
