"""Definições SQLAlchemy Core (somente para CONSTRUÇÃO de consultas).

IMPORTANTE: isto **não** é a fonte da verdade do schema — as migrações Alembic são (ADR-0003).
Estas ``Table`` existem apenas para dar referências de coluna tipadas e ergonomia de ``select()``
ao Repository. Um teste de drift no quality gate confere que estas colunas batem com o banco vivo.

As colunas de ENUM usam os tipos nativos do Postgres (``create_type=False`` — as migrações já os
criaram), para que INSERT/SELECT liguem o valor como enum e não como ``varchar``.
"""

from __future__ import annotations

from sqlalchemy import BigInteger as BigInt
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    MetaData,
    Numeric,
    SmallInteger,
    Table,
    Text,
)
from sqlalchemy import DateTime as TS
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

metadata = MetaData()

# Tipos ENUM nativos (já criados pela migração 0001) — reutilizados entre tabelas.
periodicidade = PGEnum(
    "diaria",
    "semanal",
    "mensal",
    "trimestral",
    "anual",
    "irregular",
    name="periodicidade",
    create_type=False,
)
nivel_territorial = PGEnum(
    "pais",
    "regiao",
    "uf",
    "mesorregiao",
    "microrregiao",
    "municipio",
    "distrito",
    "bairro",
    "setor_censitario",
    "bacia",
    name="nivel_territorial",
    create_type=False,
)
classificacao_dado = PGEnum(
    "nao_pessoal", "pessoal", "sensivel", name="classificacao_dado", create_type=False
)
polaridade = PGEnum("maior_melhor", "menor_melhor", "neutra", name="polaridade", create_type=False)

base_legal = Table(
    "base_legal",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("codigo", Text, nullable=False),
    Column("artigo", Text, nullable=False),
    Column("hipotese", Text, nullable=False),
    Column("justificativa", Text, nullable=False),
)

fonte = Table(
    "fonte",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("codigo", Text, nullable=False),
    Column("nome", Text, nullable=False),
    Column("orgao", Text, nullable=False),
    Column("url_doc", Text),
    Column("licenca", Text, nullable=False),
    Column("permite_uso_comercial", Boolean, nullable=False),
    Column("permite_redistribuicao", Boolean, nullable=False),
    Column("atualizacao", periodicidade, nullable=False),
    Column("lag_tipico_dias", SmallInteger),
    Column("base_legal_id", BigInt, nullable=False),
    Column("observacoes", Text),
)

territorio = Table(
    "territorio",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("codigo_ibge", Text, nullable=False),
    Column("nome", Text, nullable=False),
    Column("nivel", nivel_territorial, nullable=False),
    Column("pai_id", BigInt),
    Column("uf", Text),
    Column("populacao", Integer),
    # geom existe no banco mas NUNCA é selecionado para payload de API.
)

indicador = Table(
    "indicador",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("codigo", Text, nullable=False),
    Column("nome", Text, nullable=False),
    Column("descricao", Text, nullable=False),
    Column("dominio", Text, nullable=False),
    Column("subdominio", Text, nullable=False),
    Column("unidade", Text, nullable=False),
    Column("polaridade", polaridade, nullable=False),
    Column("atualizacao", periodicidade, nullable=False),
    Column("nivel_minimo_agregacao", nivel_territorial, nullable=False),
    Column("n_minimo", Integer, nullable=False),
    Column("classificacao", classificacao_dado, nullable=False),
    Column("origem_sensivel", Boolean, nullable=False),
    Column("publico", Boolean, nullable=False),
    Column("base_legal_id", BigInt, nullable=False),
    Column("fonte_id", BigInt, nullable=False),
    Column("codigo_externo", Text),
    Column("metodologia", Text, nullable=False),
    Column("versao_metodologia", Text, nullable=False),
)

valor = Table(
    "valor",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("indicador_id", BigInt, nullable=False),
    Column("territorio_id", BigInt, nullable=False),
    Column("periodo", Date, nullable=False),
    Column("atualizacao", periodicidade, nullable=False),
    Column("valor", Numeric),
    Column("n_amostra", Integer),
    Column("suprimido", Boolean, nullable=False),
    Column("motivo_supressao", Text),
    Column("confiabilidade", SmallInteger),
    Column("ic_inferior", Numeric),
    Column("ic_superior", Numeric),
    Column("fonte_id", BigInt, nullable=False),
    Column("versao", SmallInteger, nullable=False),
    Column("carregado_em", TS(timezone=True), nullable=False),
)

# View canônica (Privacy by Default): só indicador público e não suprimido.
valor_publico = Table(
    "valor_publico",
    metadata,
    Column("indicador_id", BigInt),
    Column("territorio_id", BigInt),
    Column("periodo", Date),
    Column("valor", Numeric),
    Column("confiabilidade", SmallInteger),
    Column("suprimido", Boolean),
    Column("motivo_supressao", Text),
)

linhagem = Table(
    "linhagem",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("fonte_id", BigInt, nullable=False),
    Column("indicador_id", BigInt),
    Column("executado_em", TS(timezone=True), nullable=False),
    Column("url_extracao", Text),
    Column("hash_origem", Text),
    Column("transformacoes", Text),
    Column("registros_carregados", Integer),
    Column("responsavel", Text),
)

# Execução orçamentária por função (OndeFoi/TRANSP-06) — fato dedicado, função como dimensão.
# Agregado público sem PII (ADR-0028) → não é a fato `valor` nem passa pela supressão (ADR-0029).
execucao_funcao = Table(
    "execucao_funcao",
    metadata,
    Column("id", BigInt, primary_key=True),
    Column("territorio_id", BigInt, nullable=False),
    Column("periodo", Date, nullable=False),
    Column("funcao_cod", Text, nullable=False),
    Column("funcao_nome", Text, nullable=False),
    Column("empenhado", Numeric),
    Column("liquidado", Numeric),
    Column("fonte_id", BigInt, nullable=False),
    Column("carregado_em", TS(timezone=True), nullable=False),
)

# Tabelas analíticas (schema public) cujas colunas o drift test confere contra o banco.
TABELAS_ANALITICAS = [base_legal, fonte, territorio, indicador, valor, linhagem, execucao_funcao]
