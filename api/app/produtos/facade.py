"""Facade dos produtos que leem o acervo real (cache + ``meta`` de proveniência do banco).

**Pulso Produtivo** lê o saldo CAGED **já no ar** via o mesmo Repository de ``/v1/valores`` —
reusa, não duplica a consulta. **Giro Local** reusa o mesmo repositório para CAGED + ESTBAN.
OndeFoi usa o seu próprio ``RepositorioOndeFoi``. **LuzNoMapa** lê DEC/FEC da ANEEL.
"""

from __future__ import annotations

from sqlalchemy import RowMapping, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura
from app.core.erros import NaoEncontradoError
from app.core.tables import execucao_funcao as t_ef
from app.core.tables import territorio as t_terr
from app.indicadores.modelos import MetaProveniencia
from app.indicadores.repositorio import RepositorioIndicadores
from app.produtos.agua_viva import NOTA_HONESTA as NOTA_AGUA_VIVA
from app.produtos.agua_viva import calcular as calcular_agua_viva
from app.produtos.bussola_edu_trabalho import NOTA_HONESTA as NOTA_BUSSOLA
from app.produtos.bussola_edu_trabalho import calcular as calcular_bussola
from app.produtos.esgoto_invisivel import NOTA_HONESTA as NOTA_ESGOTO_INVISIVEL
from app.produtos.esgoto_invisivel import calcular as calcular_esgoto_invisivel
from app.produtos.fome_oculta import NOTA_HONESTA as NOTA_FOME_OCULTA
from app.produtos.fome_oculta import calcular as calcular_fome_oculta
from app.produtos.giro_local import (
    NOTA_HONESTA as NOTA_GIRO,
)
from app.produtos.giro_local import (
    calcular as calcular_giro,
)
from app.produtos.luz_no_mapa import NOTA_HONESTA as NOTA_LUZ_NO_MAPA
from app.produtos.luz_no_mapa import calcular as calcular_luz_no_mapa
from app.produtos.modelos import (
    AguaVivaOut,
    BussolaEduTrabOut,
    EsgotoInvisivelOut,
    FomeOcultaOut,
    GiroLocalOut,
    LuzNoMapaOut,
    MesInternacoesOut,
    MesSaldoOut,
    MunicipioEmpregoOut,
    ObraVivaOut,
    PratoFrioOut,
    PulsoProdutivoOut,
    RadarEvasaoOut,
    RegiaoEmpregaOut,
    RioEmRiscoOut,
    SalarioRadarOut,
    SemeandoTransparenciaOut,
    SentinelaRespOut,
)
from app.produtos.obra_viva import NOTA_HONESTA as NOTA_OBRA_VIVA
from app.produtos.obra_viva import calcular as calcular_obra_viva
from app.produtos.prato_frio import NOTA_HONESTA as NOTA_PRATO_FRIO
from app.produtos.prato_frio import calcular as calcular_prato_frio
from app.produtos.pulso_produtivo import NOTA_HONESTA, MesSaldo, calcular
from app.produtos.radar_evasao import NOTA_HONESTA as NOTA_RADAR
from app.produtos.radar_evasao import calcular as calcular_radar
from app.produtos.regiao_emprega import NOTA_HONESTA as NOTA_REGIAO
from app.produtos.regiao_emprega import calcular as calcular_regiao
from app.produtos.rio_em_risco import NOTA_HONESTA as NOTA_RIO_EM_RISCO
from app.produtos.rio_em_risco import calcular as calcular_rio_em_risco
from app.produtos.salario_radar import NOTA_HONESTA as NOTA_SALARIO
from app.produtos.salario_radar import calcular as calcular_salario
from app.produtos.semeando_transparencia import NOTA_HONESTA as NOTA_SEMEANDO
from app.produtos.semeando_transparencia import calcular as calcular_semeando
from app.produtos.sentinela_resp import NOTA_HONESTA as NOTA_SENTINELA
from app.produtos.sentinela_resp import MesInternacoes
from app.produtos.sentinela_resp import calcular as calcular_sentinela

CODIGO_CAGED = "trabalho.emprego.saldo_caged"
CODIGO_ESTBAN = "credito.operacoes.saldo_total"
CODIGO_SALARIO = "trabalho.emprego.salario_medio_admissao"
CODIGO_EDUCACAO = "educacao.matriculas.fundamental"
CODIGO_DATASUS = "saude.resp.internacoes_j"
CODIGO_PNCP = "compras.contratos.valor_total"
CODIGO_AGUA_SNIS = "saneamento.agua.atendimento_pct"
CODIGO_ESGOTO_SNIS = "saneamento.esgoto.coleta_pct"
CODIGO_DEC = "energia.qualidade.dec"
CODIGO_FEC = "energia.qualidade.fec"
CODIGO_SECA = "saneamento.agua.seca_indice"
CODIGO_PAM = "alimentacao.producao.valor_total"
CODIGO_SISVAN = "alimentacao.nutricao.baixo_peso_pct"
_POR_PAGINA = 1000  # série mensal de um município cabe folgada numa página.


def _meta(row: RowMapping) -> MetaProveniencia:
    return MetaProveniencia(
        indicador=row["codigo"],
        nome=row["nome"],
        fonte=row["fonte_nome"],
        metodologia=row["metodologia"],
        lag_tipico_dias=row["fonte_lag"],
        licenca=row["fonte_licenca"],
    )


class PulsoProdutivoFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:pulso")
    async def pulso_produtivo(self, *, codigo_ibge: str) -> PulsoProdutivoOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_CAGED)
        if meta_row is None:  # pragma: no cover - indicador sempre semeado
            raise NaoEncontradoError(f"indicador '{CODIGO_CAGED}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_CAGED,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        # Só meses divulgados (valor não suprimido); o saldo CAGED nunca suprime (n_minimo=0).
        meses = [
            MesSaldo(periodo=r["periodo"].strftime("%Y-%m"), saldo=int(r["valor"]))
            for r in linhas
            if r["valor"] is not None
        ]
        if not meses:
            raise NaoEncontradoError(f"Pulso Produtivo para município '{codigo_ibge}'")

        p = calcular(terr["codigo_ibge"], terr["nome"], terr["uf"], meses)
        return PulsoProdutivoOut(
            codigo_ibge=p.codigo_ibge,
            nome=p.nome,
            uf=p.uf,
            periodo=p.periodo,
            saldo_mes=p.saldo_mes,
            saldo_acumulado=p.saldo_acumulado,
            pulso=p.pulso,
            tendencia=p.tendencia,
            meses_positivos=p.meses_positivos,
            meses_negativos=p.meses_negativos,
            meses=[MesSaldoOut(periodo=m.periodo, saldo=m.saldo) for m in p.meses],
            nota=NOTA_HONESTA,
            meta=_meta(meta_row),
        )


class GiroLocalFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:giro")
    async def giro_local(self, *, codigo_ibge: str) -> GiroLocalOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        meta_caged = await self._repo.meta_indicador(self._s, CODIGO_CAGED)
        meta_estban = await self._repo.meta_indicador(self._s, CODIGO_ESTBAN)

        # CAGED: último mês disponível (saldo do mês mais recente)
        linhas_caged, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_CAGED,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        caged_rows = [r for r in linhas_caged if r["valor"] is not None]
        saldo_emprego: int | None = None
        periodo_emprego: str | None = None
        if caged_rows:
            ultimo_caged = caged_rows[-1]
            saldo_emprego = int(ultimo_caged["valor"])
            periodo_emprego = ultimo_caged["periodo"].strftime("%Y-%m")

        # ESTBAN: último mês disponível
        linhas_estban, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_ESTBAN,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        estban_rows = [r for r in linhas_estban if r["valor"] is not None]
        saldo_credito: int | None = None
        periodo_credito: str | None = None
        if estban_rows:
            ultimo_estban = estban_rows[-1]
            saldo_credito = int(ultimo_estban["valor"])
            periodo_credito = ultimo_estban["periodo"].strftime("%Y-%m")

        if saldo_emprego is None and saldo_credito is None:
            raise NaoEncontradoError(f"Giro Local para município '{codigo_ibge}'")

        g = calcular_giro(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            periodo_emprego=periodo_emprego,
            saldo_emprego=saldo_emprego,
            periodo_credito=periodo_credito,
            saldo_credito=saldo_credito,
        )
        return GiroLocalOut(
            codigo_ibge=g.codigo_ibge,
            nome=g.nome,
            uf=g.uf,
            populacao=g.populacao,
            periodo_emprego=g.periodo_emprego,
            saldo_emprego=g.saldo_emprego,
            saldo_emprego_per_1000=g.saldo_emprego_per_1000,
            nivel_emprego=g.nivel_emprego,
            periodo_credito=g.periodo_credito,
            saldo_credito=g.saldo_credito,
            saldo_credito_per_hab=g.saldo_credito_per_hab,
            nivel_credito=g.nivel_credito,
            nota=NOTA_GIRO,
            meta_emprego=_meta(meta_caged) if meta_caged else None,
            meta_credito=_meta(meta_estban) if meta_estban else None,
        )


class SalarioRadarFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:salario")
    async def salario_radar(self, *, codigo_ibge: str) -> SalarioRadarOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_SALARIO)
        if meta_row is None:  # pragma: no cover - indicador sempre semeado
            raise NaoEncontradoError(f"indicador '{CODIGO_SALARIO}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_SALARIO,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        rows = [r for r in linhas if r["valor"] is not None]
        if not rows:
            raise NaoEncontradoError(f"Salário Radar para município '{codigo_ibge}'")

        ultimo = rows[-1]
        s = calcular_salario(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            periodo=ultimo["periodo"].strftime("%Y-%m"),
            salario_medio=float(ultimo["valor"]),
        )
        return SalarioRadarOut(
            codigo_ibge=s.codigo_ibge,
            nome=s.nome,
            uf=s.uf,
            periodo=s.periodo,
            salario_medio=s.salario_medio,
            nivel=s.nivel,
            nota=NOTA_SALARIO,
            meta=_meta(meta_row),
        )


class RegiaoEmpregaFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:regiao")
    async def regiao_emprega(self, *, codigo_ibge: str) -> RegiaoEmpregaOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        # Resolve UF: o código pode ser uma UF (nivel='uf') ou um município (nivel='municipio')
        if terr["nivel"] == "uf":
            uf_codigo = terr["codigo_ibge"]
            uf_nome = terr["nome"]
            uf_sigla = terr["uf"] or ""
        elif terr["nivel"] == "municipio" and terr["pai_codigo_ibge"]:
            uf_codigo = terr["pai_codigo_ibge"]
            uf_row = await self._repo.obter_territorio(self._s, uf_codigo)
            if uf_row is None:
                raise NaoEncontradoError(f"UF para município '{codigo_ibge}'")
            uf_nome = uf_row["nome"]
            uf_sigla = uf_row["uf"] or terr["uf"] or ""
        else:
            raise NaoEncontradoError(f"território '{codigo_ibge}' não é UF nem município")

        # Saldos de todos os municípios da UF (uma consulta, sem N+1)
        linhas = await self._repo.saldos_por_uf(
            self._s,
            uf_codigo_ibge=uf_codigo,
            indicador_codigo=CODIGO_CAGED,
        )
        if not linhas:
            raise NaoEncontradoError(f"Região Emprega para UF '{uf_codigo}'")

        municipios_raw: list[tuple[str, str, int | None, int | None]] = []
        periodo: str | None = None
        for r in linhas:
            saldo = int(r["valor"]) if r["valor"] is not None else None
            if r["periodo"] is not None and periodo is None:
                periodo = r["periodo"].strftime("%Y-%m")
            municipios_raw.append((r["codigo_ibge"], r["nome"], r["populacao"], saldo))

        reg = calcular_regiao(
            uf_codigo,
            uf_nome,
            uf_sigla,
            periodo=periodo,
            municipios_raw=municipios_raw,
        )

        meta_row = await self._repo.meta_indicador(self._s, CODIGO_CAGED)
        if meta_row is None:  # pragma: no cover - indicador sempre semeado
            raise NaoEncontradoError(f"indicador '{CODIGO_CAGED}'")

        return RegiaoEmpregaOut(
            codigo_ibge=reg.codigo_ibge,
            nome=reg.nome,
            uf=reg.uf,
            periodo=reg.periodo,
            saldo_total=reg.saldo_total,
            municipios_criando=reg.municipios_criando,
            municipios_estaveis=reg.municipios_estaveis,
            municipios_reduzindo=reg.municipios_reduzindo,
            municipios_sem_dado=reg.municipios_sem_dado,
            municipios_total=reg.municipios_total,
            nivel=reg.nivel,
            municipios=[
                MunicipioEmpregoOut(
                    codigo_ibge=m.codigo_ibge,
                    nome=m.nome,
                    populacao=m.populacao,
                    saldo=m.saldo,
                    per_1000=m.per_1000,
                    nivel=m.nivel,
                )
                for m in reg.municipios
            ],
            nota=NOTA_REGIAO,
            meta=_meta(meta_row),
        )


class BussolaEduTrabFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:bussola-edu")
    async def bussola_edu_trabalho(self, *, codigo_ibge: str) -> BussolaEduTrabOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        # Educação: último valor anual disponível
        linhas_edu, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_EDUCACAO,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        edu_rows = [r for r in linhas_edu if r["valor"] is not None]
        matriculas: int | None = None
        periodo_educacao: str | None = None
        if edu_rows:
            ultimo_edu = edu_rows[-1]
            matriculas = int(ultimo_edu["valor"])
            periodo_educacao = ultimo_edu["periodo"].strftime("%Y")

        # Emprego formal: último mês disponível
        linhas_caged, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_CAGED,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        caged_rows = [r for r in linhas_caged if r["valor"] is not None]
        saldo_emprego: int | None = None
        periodo_emprego: str | None = None
        if caged_rows:
            ultimo_caged = caged_rows[-1]
            saldo_emprego = int(ultimo_caged["valor"])
            periodo_emprego = ultimo_caged["periodo"].strftime("%Y-%m")

        # Salário médio das admissões: último mês disponível
        linhas_sal, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_SALARIO,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        sal_rows = [r for r in linhas_sal if r["valor"] is not None]
        salario_medio: float | None = None
        if sal_rows:
            salario_medio = float(sal_rows[-1]["valor"])

        if matriculas is None and saldo_emprego is None:
            raise NaoEncontradoError(f"Bússola Educação-Trabalho para município '{codigo_ibge}'")

        b = calcular_bussola(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            periodo_educacao=periodo_educacao,
            matriculas=matriculas,
            periodo_emprego=periodo_emprego,
            saldo_emprego=saldo_emprego,
            salario_medio=salario_medio,
        )

        meta_edu = await self._repo.meta_indicador(self._s, CODIGO_EDUCACAO)
        meta_caged = await self._repo.meta_indicador(self._s, CODIGO_CAGED)
        meta_sal = await self._repo.meta_indicador(self._s, CODIGO_SALARIO)

        return BussolaEduTrabOut(
            codigo_ibge=b.codigo_ibge,
            nome=b.nome,
            uf=b.uf,
            populacao=b.populacao,
            periodo_educacao=b.periodo_educacao,
            matriculas=b.matriculas,
            matriculas_por_mil=b.matriculas_por_mil,
            nivel_educacao=b.nivel_educacao,
            periodo_emprego=b.periodo_emprego,
            saldo_emprego=b.saldo_emprego,
            nivel_emprego=b.nivel_emprego,
            salario_medio=b.salario_medio,
            nivel_salario=b.nivel_salario,
            nota=NOTA_BUSSOLA,
            meta_educacao=_meta(meta_edu) if meta_edu else None,
            meta_emprego=_meta(meta_caged) if meta_caged else None,
            meta_salario=_meta(meta_sal) if meta_sal else None,
        )


class SentinelaRespFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:sentinela-resp")
    async def sentinela_resp(self, *, codigo_ibge: str) -> SentinelaRespOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        # Lê TODOS os meses (incluindo suprimidos) ordenados por período.
        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_DATASUS,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        if not linhas:
            raise NaoEncontradoError(f"Sentinela Respiratória para município '{codigo_ibge}'")

        meses = [
            MesInternacoes(
                periodo=r["periodo"].strftime("%Y-%m"),
                internacoes=int(r["valor"]) if r["valor"] is not None else None,
                suprimido=bool(r["suprimido"]),
            )
            for r in linhas
        ]

        s = calcular_sentinela(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            meses,
        )
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_DATASUS)

        return SentinelaRespOut(
            codigo_ibge=s.codigo_ibge,
            nome=s.nome,
            uf=s.uf,
            populacao=s.populacao,
            periodo=s.periodo,
            internacoes=s.internacoes,
            internacoes_por_100k=s.internacoes_por_100k,
            suprimido=s.suprimido,
            nivel=s.nivel,
            tendencia=s.tendencia,
            meses=[
                MesInternacoesOut(
                    periodo=m.periodo,
                    internacoes=m.internacoes,
                    suprimido=m.suprimido,
                )
                for m in s.meses
            ],
            nota=NOTA_SENTINELA,
            meta=_meta(meta_row) if meta_row else None,
        )


class RadarEvasaoFacade:
    """Fachada do Radar de Evasão Escolar (EDU-02): cobertura do ensino fundamental."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:radar-evasao")
    async def radar_evasao(self, *, codigo_ibge: str) -> RadarEvasaoOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_EDUCACAO,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=10,
        )
        if not linhas:
            raise NaoEncontradoError(f"Radar de Evasão para município '{codigo_ibge}'")

        ultimo = [r for r in linhas if r["valor"] is not None]
        if not ultimo:
            raise NaoEncontradoError(f"Radar de Evasão para município '{codigo_ibge}'")

        row = ultimo[-1]
        r = calcular_radar(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            periodo=row["periodo"].strftime("%Y"),
            matriculas=int(row["valor"]),
        )
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_EDUCACAO)

        return RadarEvasaoOut(
            codigo_ibge=r.codigo_ibge,
            nome=r.nome,
            uf=r.uf,
            populacao=r.populacao,
            periodo=r.periodo,
            matriculas=r.matriculas,
            matriculas_por_mil=r.matriculas_por_mil,
            populacao_escolar_estimada=r.populacao_escolar_estimada,
            taxa_cobertura=r.taxa_cobertura,
            nivel=r.nivel,
            nota=NOTA_RADAR,
            meta=_meta(meta_row) if meta_row else None,
        )


class ObraVivaFacade:
    """Fachada das contratações públicas municipais via PNCP (TRANSP-05)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:obra-viva")
    async def obra_viva(self, *, codigo_ibge: str) -> ObraVivaOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_PNCP,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=10,
        )
        if not linhas:
            raise NaoEncontradoError(f"ObraViva para município '{codigo_ibge}'")

        ultimo = linhas[-1]
        valor_contratos = int(ultimo["valor"]) if ultimo["valor"] is not None else None
        periodo = ultimo["periodo"].strftime("%Y") if ultimo["periodo"] is not None else None

        o = calcular_obra_viva(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            periodo=periodo,
            valor_contratos=valor_contratos,
        )
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_PNCP)

        return ObraVivaOut(
            codigo_ibge=o.codigo_ibge,
            nome=o.nome,
            uf=o.uf,
            populacao=o.populacao,
            periodo=o.periodo,
            valor_contratos=o.valor_contratos,
            valor_por_hab=o.valor_por_hab,
            nivel=o.nivel,
            nota=NOTA_OBRA_VIVA,
            meta=_meta(meta_row) if meta_row else None,
        )


class AguaVivaFacade:
    """Fachada do saneamento básico municipal — AguaViva (SANE-01)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:agua-viva")
    async def agua_viva(self, *, codigo_ibge: str) -> AguaVivaOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas_agua, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_AGUA_SNIS,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )
        if not linhas_agua:
            raise NaoEncontradoError(f"AguaViva para município '{codigo_ibge}'")

        linhas_esgoto, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_ESGOTO_SNIS,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )

        ultimo_agua = linhas_agua[-1]
        agua_pct = float(ultimo_agua["valor"]) if ultimo_agua["valor"] is not None else None
        periodo = (
            ultimo_agua["periodo"].strftime("%Y") if ultimo_agua["periodo"] is not None else None
        )

        esgoto_pct: float | None = None
        if linhas_esgoto:
            v = linhas_esgoto[-1]["valor"]
            esgoto_pct = float(v) if v is not None else None

        av = calcular_agua_viva(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            periodo=periodo,
            agua_pct=agua_pct,
            esgoto_pct=esgoto_pct,
        )
        meta_agua = await self._repo.meta_indicador(self._s, CODIGO_AGUA_SNIS)
        meta_esgoto = await self._repo.meta_indicador(self._s, CODIGO_ESGOTO_SNIS)

        return AguaVivaOut(
            codigo_ibge=av.codigo_ibge,
            nome=av.nome,
            uf=av.uf,
            periodo=av.periodo,
            agua_pct=av.agua_pct,
            esgoto_pct=av.esgoto_pct,
            nivel_agua=av.nivel_agua,
            nivel_esgoto=av.nivel_esgoto,
            nota=NOTA_AGUA_VIVA,
            meta_agua=_meta(meta_agua) if meta_agua else None,
            meta_esgoto=_meta(meta_esgoto) if meta_esgoto else None,
        )


class LuzNoMapaFacade:
    """Fachada da qualidade do fornecimento elétrico por município — LuzNoMapa (SANE-04)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:luz-no-mapa")
    async def luz_no_mapa(self, *, codigo_ibge: str) -> LuzNoMapaOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas_dec, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_DEC,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )
        if not linhas_dec:
            raise NaoEncontradoError(f"LuzNoMapa para município '{codigo_ibge}'")

        linhas_fec, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_FEC,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )

        ultimo_dec = linhas_dec[-1]
        dec = float(ultimo_dec["valor"]) if ultimo_dec["valor"] is not None else None
        periodo = (
            ultimo_dec["periodo"].strftime("%Y") if ultimo_dec["periodo"] is not None else None
        )

        fec: float | None = None
        if linhas_fec:
            v = linhas_fec[-1]["valor"]
            fec = float(v) if v is not None else None

        lnm = calcular_luz_no_mapa(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            periodo=periodo,
            dec=dec,
            fec=fec,
        )
        meta_dec = await self._repo.meta_indicador(self._s, CODIGO_DEC)
        meta_fec = await self._repo.meta_indicador(self._s, CODIGO_FEC)

        return LuzNoMapaOut(
            codigo_ibge=lnm.codigo_ibge,
            nome=lnm.nome,
            uf=lnm.uf,
            periodo=lnm.periodo,
            dec=lnm.dec,
            fec=lnm.fec,
            nivel_dec=lnm.nivel_dec,
            nivel_fec=lnm.nivel_fec,
            nota=NOTA_LUZ_NO_MAPA,
            meta_dec=_meta(meta_dec) if meta_dec else None,
            meta_fec=_meta(meta_fec) if meta_fec else None,
        )


class EsgotoInvisivelFacade:
    """Fachada do gap de saneamento por município — EsgotoInvisível (SANE-03)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:esgoto-invisivel")
    async def esgoto_invisivel(self, *, codigo_ibge: str) -> EsgotoInvisivelOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas_esgoto, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_ESGOTO_SNIS,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )
        if not linhas_esgoto:
            raise NaoEncontradoError(f"EsgotoInvisível para município '{codigo_ibge}'")

        linhas_agua, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_AGUA_SNIS,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )

        ultimo_esgoto = linhas_esgoto[-1]
        esgoto_pct = float(ultimo_esgoto["valor"]) if ultimo_esgoto["valor"] is not None else None
        periodo = (
            ultimo_esgoto["periodo"].strftime("%Y")
            if ultimo_esgoto["periodo"] is not None
            else None
        )

        agua_pct: float | None = None
        if linhas_agua:
            v = linhas_agua[-1]["valor"]
            agua_pct = float(v) if v is not None else None

        ei = calcular_esgoto_invisivel(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            periodo=periodo,
            agua_pct=agua_pct,
            esgoto_pct=esgoto_pct,
        )
        meta_esgoto = await self._repo.meta_indicador(self._s, CODIGO_ESGOTO_SNIS)
        meta_agua = await self._repo.meta_indicador(self._s, CODIGO_AGUA_SNIS)

        return EsgotoInvisivelOut(
            codigo_ibge=ei.codigo_ibge,
            nome=ei.nome,
            uf=ei.uf,
            periodo=ei.periodo,
            agua_pct=ei.agua_pct,
            esgoto_pct=ei.esgoto_pct,
            gap_pct=ei.gap_pct,
            nivel_gap=ei.nivel_gap,
            nota=NOTA_ESGOTO_INVISIVEL,
            meta_esgoto=_meta(meta_esgoto) if meta_esgoto else None,
            meta_agua=_meta(meta_agua) if meta_agua else None,
        )


class RioEmRiscoFacade:
    """Fachada do risco hídrico de seca por município — RioEmRisco (SANE-02)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:rio-em-risco")
    async def rio_em_risco(self, *, codigo_ibge: str) -> RioEmRiscoOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_SECA,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=5,
        )
        if not linhas:
            raise NaoEncontradoError(f"RioEmRisco para município '{codigo_ibge}'")

        ultimo = linhas[-1]
        seca_indice = float(ultimo["valor"]) if ultimo["valor"] is not None else None
        periodo = ultimo["periodo"].strftime("%Y") if ultimo["periodo"] is not None else None

        rer = calcular_rio_em_risco(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            periodo=periodo,
            seca_indice=seca_indice,
        )
        meta = await self._repo.meta_indicador(self._s, CODIGO_SECA)

        return RioEmRiscoOut(
            codigo_ibge=rer.codigo_ibge,
            nome=rer.nome,
            uf=rer.uf,
            periodo=rer.periodo,
            seca_indice=rer.seca_indice,
            nivel=rer.nivel,
            nota=NOTA_RIO_EM_RISCO,
            meta=_meta(meta) if meta else None,
        )


class PratoFrioFacade:
    """Fachada da produção agrícola municipal per capita — PratoFrio (ALIM-01)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:prato-frio")
    async def prato_frio(self, *, codigo_ibge: str) -> PratoFrioOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_PAM,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=10,
        )
        if not linhas:
            raise NaoEncontradoError(f"PratoFrio para município '{codigo_ibge}'")

        ultimo = linhas[-1]
        valor_total = float(ultimo["valor"]) if ultimo["valor"] is not None else None
        periodo = ultimo["periodo"].strftime("%Y") if ultimo["periodo"] is not None else None

        pf = calcular_prato_frio(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            periodo=periodo,
            valor_total=valor_total,
        )
        meta = await self._repo.meta_indicador(self._s, CODIGO_PAM)

        return PratoFrioOut(
            codigo_ibge=pf.codigo_ibge,
            nome=pf.nome,
            uf=pf.uf,
            populacao=pf.populacao,
            periodo=pf.periodo,
            valor_total=pf.valor_total,
            valor_por_hab=pf.valor_por_hab,
            nivel=pf.nivel,
            nota=NOTA_PRATO_FRIO,
            meta=_meta(meta) if meta else None,
        )


# ------------------------------------------------- SemeandoTransparencia (ALIM-05)


class SemeandoTransparenciaFacade:
    """Fachada do investimento público municipal em agricultura — ALIM-05."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @cache_leitura("v1:semeando-transparencia")
    async def semeando_transparencia(self, *, codigo_ibge: str) -> SemeandoTransparenciaOut:
        # 1. território
        terr = (
            (
                await self._s.execute(
                    select(t_terr).where(
                        t_terr.c.codigo_ibge == codigo_ibge,
                        t_terr.c.nivel == "municipio",
                    )
                )
            )
            .mappings()
            .first()
        )
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        # 2. período mais recente em execucao_funcao para este território
        periodo = (
            await self._s.execute(
                select(func.max(t_ef.c.periodo)).where(t_ef.c.territorio_id == terr["id"])
            )
        ).scalar_one_or_none()
        if periodo is None:
            raise NaoEncontradoError(f"SemeandoTransparência para município '{codigo_ibge}'")

        # 3. função 20 no período mais recente
        row = (
            (
                await self._s.execute(
                    select(func.sum(t_ef.c.liquidado).label("liquidado")).where(
                        t_ef.c.territorio_id == terr["id"],
                        t_ef.c.periodo == periodo,
                        t_ef.c.funcao_cod == "20",
                    )
                )
            )
            .mappings()
            .first()
        )
        liquidado_raw = row["liquidado"] if row else None
        valor_liquidado = float(liquidado_raw) if liquidado_raw is not None else 0.0

        st = calcular_semeando(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            ano=periodo.year,
            valor_liquidado=valor_liquidado,
        )

        return SemeandoTransparenciaOut(
            codigo_ibge=st.codigo_ibge,
            nome=st.nome,
            uf=st.uf,
            populacao=st.populacao,
            ano=st.ano,
            valor_liquidado=st.valor_liquidado,
            valor_por_hab=st.valor_por_hab,
            nivel=st.nivel,
            nota=NOTA_SEMEANDO,
            meta=None,
        )


class FomeOcultaFacade:
    """Fachada do produto Fome Oculta — ALIM-02."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:fome-oculta")
    async def fome_oculta(self, *, codigo_ibge: str) -> FomeOcultaOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_SISVAN)
        if meta_row is None:  # pragma: no cover - indicador sempre semeado
            raise NaoEncontradoError(f"indicador '{CODIGO_SISVAN}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_SISVAN,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=1,
        )
        if not linhas:
            raise NaoEncontradoError(f"Fome Oculta para município '{codigo_ibge}'")

        row = linhas[0]
        pct = float(row["valor"]) if row["valor"] is not None else None
        n_acomp = int(row["n_amostra"]) if row["n_amostra"] is not None else None
        ano = row["periodo"].year if row["periodo"] is not None else None

        fo = calcular_fome_oculta(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            ano=ano,
            n_acompanhadas=n_acomp,
            baixo_peso_pct=pct,
        )
        return FomeOcultaOut(
            codigo_ibge=fo.codigo_ibge,
            nome=fo.nome,
            uf=fo.uf,
            populacao=fo.populacao,
            ano=fo.ano,
            n_acompanhadas=fo.n_acompanhadas,
            baixo_peso_pct=fo.baixo_peso_pct,
            nivel=fo.nivel,
            nota=NOTA_FOME_OCULTA,
            meta=_meta(meta_row),
        )
