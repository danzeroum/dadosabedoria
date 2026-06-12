"""Rotas dos produtos nomeados: OndeFoi, Pulso Produtivo (TRAB-01), Giro Local (TRAB-03),
Salário Radar (TRAB-02), Região Emprega (TRAB-04), Bússola Educação-Trabalho (EDU-01),
Sentinela Respiratória (SAUDE-01), ObraViva (TRANSP-05), AguaViva (SANE-01),
EsgotoInvisível (SANE-03), LuzNoMapa (SANE-04), RioEmRisco (SANE-02), PratoFrio (ALIM-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.produtos.facade import (
    AguaVivaFacade,
    BussolaEduTrabFacade,
    EsgotoInvisivelFacade,
    GiroLocalFacade,
    LuzNoMapaFacade,
    ObraVivaFacade,
    PratoFrioFacade,
    PulsoProdutivoFacade,
    RadarEvasaoFacade,
    RegiaoEmpregaFacade,
    RioEmRiscoFacade,
    SalarioRadarFacade,
    SentinelaRespFacade,
)
from app.produtos.modelos import (
    AguaVivaOut,
    BussolaEduTrabOut,
    EsgotoInvisivelOut,
    GiroLocalOut,
    LuzNoMapaOut,
    ObraVivaOut,
    OndeFoiLista,
    OndeFoiOut,
    PratoFrioOut,
    PulsoProdutivoOut,
    RadarEvasaoOut,
    RegiaoEmpregaOut,
    RioEmRiscoOut,
    SalarioRadarOut,
    SentinelaRespOut,
)
from app.produtos.repositorio_onde_foi import RepositorioOndeFoi

router = APIRouter(prefix="/v1", tags=["produtos"])

_repo_onde_foi = RepositorioOndeFoi()


@router.get("/onde-foi", response_model=OndeFoiLista)
async def onde_foi_lista(session: AsyncSession = Depends(get_session)) -> OndeFoiLista:
    """Diretório dos municípios do OndeFoi — ordenado por nome (dupla-face §17, não ranking).

    Lista os municípios com dado real na fato ``execucao_funcao`` (SICONFI/Anexo I-E). Retorna
    lista vazia quando nenhum dado foi ingerido ainda.
    """
    return await _repo_onde_foi.listar(session)


@router.get("/onde-foi/{codigo_ibge}", response_model=OndeFoiOut)
async def onde_foi(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> OndeFoiOut:
    """Do que a prefeitura empenhou por função, quanto liquidou? (Liquidado÷Empenhado — ADR-0029).

    ``meta.metodologia`` enquadra: é execução **orçamentária** (empenhar≠liquidar≠serviço
    entregue). 404 quando não há dado para o município.
    """
    return await _repo_onde_foi.obter(session, codigo_ibge=codigo_ibge)


@router.get("/pulso-produtivo/{codigo_ibge}", response_model=PulsoProdutivoOut)
async def pulso_produtivo(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PulsoProdutivoOut:
    """Como está o pulso do emprego formal no município? Saldo CAGED (admissões − desligamentos).

    Dado **real** do acervo (mesmo Repository de ``/v1/valores``). ``nota``/``meta`` enquadram:
    emprego **formal**, fluxo volátil/sazonal — saldo negativo merece a pergunta, não é veredito.
    """
    return await PulsoProdutivoFacade(session).pulso_produtivo(codigo_ibge=codigo_ibge)


@router.get("/giro-local/{codigo_ibge}", response_model=GiroLocalOut)
async def giro_local(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> GiroLocalOut:
    """Dinamismo econômico local per capita: criação de emprego formal + crédito bancário.

    Combina CAGED (saldo/1000 hab) e ESTBAN (crédito/hab) para comparação entre municípios de
    portes diferentes. 404 quando não há nenhum dado disponível para o município.
    """
    return await GiroLocalFacade(session).giro_local(codigo_ibge=codigo_ibge)


@router.get("/salario-radar/{codigo_ibge}", response_model=SalarioRadarOut)
async def salario_radar(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SalarioRadarOut:
    """Nível salarial das novas contratações formais no município (Salário Radar — TRAB-02).

    Salário médio declarado nas admissões do Novo CAGED do último mês disponível. Revela o
    patamar salarial da demanda por trabalho formal local — não o salário médio da população.
    404 quando não há dado para o município.
    """
    return await SalarioRadarFacade(session).salario_radar(codigo_ibge=codigo_ibge)


@router.get("/regiao-emprega/{codigo_ibge}", response_model=RegiaoEmpregaOut)
async def regiao_emprega(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> RegiaoEmpregaOut:
    """Retrato do emprego formal de toda a UF no último mês disponível (Região Emprega — TRAB-04).

    Aceita o código IBGE de uma UF (ex.: ``35`` para SP) ou de um município (ex.: ``3550308``).
    Agrega o saldo CAGED de todos os municípios da UF no mesmo período, revelando se a criação ou
    destruição de empregos é local ou regional. 404 quando não há dado para a UF.
    """
    return await RegiaoEmpregaFacade(session).regiao_emprega(codigo_ibge=codigo_ibge)


@router.get("/bussola-edu-trabalho/{codigo_ibge}", response_model=BussolaEduTrabOut)
async def bussola_edu_trabalho(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> BussolaEduTrabOut:
    """Base educacional e mercado de trabalho formal do município (Bússola EDU-01).

    Combina matrículas do ensino fundamental (INEP/Censo Escolar, anual) com o saldo de emprego
    formal e o salário médio das admissões (CAGED, mensal). A relação é de CONTEXTO, não causal.
    404 quando não há nenhum dado disponível para o município.
    """
    return await BussolaEduTrabFacade(session).bussola_edu_trabalho(codigo_ibge=codigo_ibge)


@router.get("/sentinela-resp/{codigo_ibge}", response_model=SentinelaRespOut)
async def sentinela_resp(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SentinelaRespOut:
    """Internações respiratórias SUS do município por mês (Sentinela Respiratória — SAUDE-01).

    Contagem de AIH com diagnóstico no grupo J do CID-10 (J00–J99) no SIH/SUS. Dado de
    **origem sensível**: células abaixo de 5 internações são protegidas pelo k-anonimato
    (ADR-0004) — aparecem com ``suprimido=true`` e ``internacoes=null``, nunca como zero.
    404 quando não há nenhum dado disponível para o município.
    """
    return await SentinelaRespFacade(session).sentinela_resp(codigo_ibge=codigo_ibge)


@router.get("/radar-evasao/{codigo_ibge}", response_model=RadarEvasaoOut)
async def radar_evasao(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> RadarEvasaoOut:
    """Cobertura do ensino fundamental vs. estimativa de crianças em idade escolar (EDU-02).

    Matrículas do Censo Escolar/INEP divididas por 14 % da pop. municipal (proxy faixa 6–14 anos).
    Taxa > 100 % indica polo de atração escolar — classifica como "adequada", não erro.
    Só cobre o fundamental formal (não EJA, creche, pré-escola).
    404 quando não há dado de matrículas para o município.
    """
    return await RadarEvasaoFacade(session).radar_evasao(codigo_ibge=codigo_ibge)


@router.get("/obra-viva/{codigo_ibge}", response_model=ObraVivaOut)
async def obra_viva(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> ObraVivaOut:
    """Contratações públicas municipais via PNCP per capita (ObraViva — TRANSP-05).

    Soma do valor global de contratos publicados no PNCP pelo município no exercício. Cobre
    todos os tipos (obras, serviços, bens) — uso como contexto de intensidade de contratação.
    Nota: PNCP ainda não tem adesão universal — ausência ≠ ausência de contratação.
    404 quando não há dado de contratos para o município.
    """
    return await ObraVivaFacade(session).obra_viva(codigo_ibge=codigo_ibge)


@router.get("/agua-viva/{codigo_ibge}", response_model=AguaVivaOut)
async def agua_viva(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> AguaVivaOut:
    """Acesso a água tratada e coleta de esgoto por município (AguaViva — SANE-01).

    Indicadores IN023_AE (água) e IN015_AE (esgoto) do SNIS.
    404 quando não há dado SNIS para o município.
    """
    return await AguaVivaFacade(session).agua_viva(codigo_ibge=codigo_ibge)


@router.get("/esgoto-invisivel/{codigo_ibge}", response_model=EsgotoInvisivelOut)
async def esgoto_invisivel(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> EsgotoInvisivelOut:
    """Gap entre cobertura de água e esgoto por município (EsgotoInvisível — SANE-03).

    Onde a água chega mas o esgoto some — mede o efluente não coletado (IN015_AE do SNIS).
    Níveis: adequado (≥ 70 %), atenção (40–69 %), crítico (< 40 %).
    404 quando não há dado SNIS de esgoto para o município.
    """
    return await EsgotoInvisivelFacade(session).esgoto_invisivel(codigo_ibge=codigo_ibge)


@router.get("/luz-no-mapa/{codigo_ibge}", response_model=LuzNoMapaOut)
async def luz_no_mapa(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> LuzNoMapaOut:
    """Qualidade do fornecimento de energia elétrica no município (LuzNoMapa — SANE-04).

    Indicadores DEC (horas de interrupção por consumidor/ano) e FEC (interrupções/consumidor/ano)
    da ANEEL. Menor é melhor. 404 quando não há dado ANEEL para o município.
    """
    return await LuzNoMapaFacade(session).luz_no_mapa(codigo_ibge=codigo_ibge)


@router.get("/rio-em-risco/{codigo_ibge}", response_model=RioEmRiscoOut)
async def rio_em_risco(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> RioEmRiscoOut:
    """Risco hídrico de seca por município — ANA Monitor de Secas (RioEmRisco — SANE-02).

    Índice de seca (0–5: Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5), pior mês do exercício.
    Níveis: normal (< D0), atencao (D0–D1), critico (D2–D4).
    404 quando não há dado ANA para o município.
    """
    return await RioEmRiscoFacade(session).rio_em_risco(codigo_ibge=codigo_ibge)


@router.get("/prato-frio/{codigo_ibge}", response_model=PratoFrioOut)
async def prato_frio(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PratoFrioOut:
    """Produção agrícola municipal per capita — IBGE PAM (PratoFrio — ALIM-01).

    Valor total da produção (lavouras temporárias + permanentes, variável 762) em BRL por habitante.
    Níveis: alta (≥ R$ 5.000/hab/ano), moderada (≥ R$ 500/hab/ano), baixa (< R$ 500/hab/ano).
    Produção varia por bioma/clima — use como contexto, não ranking. Forma a confirmar na 1ª busca
    real (servicodados.ibge.gov.br). 404 quando não há dado PAM para o município.
    """
    return await PratoFrioFacade(session).prato_frio(codigo_ibge=codigo_ibge)
