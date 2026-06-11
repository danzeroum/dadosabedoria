"""Serviço de IA ancorada — orquestra guardrails → recuperação → (abster | narrar) + citações.

Garantias (invariante 3): narra só sobre o recuperado; cada resposta carrega citação e ressalvas;
sem dado suficiente, abstém-se; nunca afirma causalidade. Sem acesso ao schema ``app``.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.ia.guardrails import candidatos_lugar, identificar_indicador, sanitizar
from app.ia.modelos import Citacao, PerguntaIA, RespostaIA
from app.ia.narrador import Narrador, narrador_padrao
from app.ia.recuperacao import ContextoIA, catalogo, recuperar
from app.indicadores.repositorio import RepositorioIndicadores


def _parse_mes(valor: str | None) -> date | None:
    if valor is None:
        return None
    ano, mes = valor.split("-")
    return date(int(ano), int(mes), 1)


class ServicoIA:
    def __init__(self, session: AsyncSession, narrador: Narrador | None = None) -> None:
        self._s = session
        self._narrador = narrador or narrador_padrao()
        self._repo = RepositorioIndicadores()

    async def _resolver_territorio(self, pergunta: str) -> str | None:
        """Tenta encontrar um município único na pergunta por nome.

        Extrai candidatos de lugar (após preposições) e busca na tabela territorio.
        Retorna o codigo_ibge se exatamente 1 resultado exato; None se ambíguo ou não encontrado.
        """
        for cand in candidatos_lugar(pergunta):
            rows = await self._repo.buscar_territorios(self._s, q=cand, nivel="municipio", limit=5)
            exatos = [r for r in rows if r["nome"].lower() == cand.lower()]
            if len(exatos) == 1:
                return str(exatos[0]["codigo_ibge"])
        return None

    async def perguntar(self, p: PerguntaIA) -> RespostaIA:
        pergunta = sanitizar(p.pergunta)

        indicador = p.indicador or identificar_indicador(pergunta, await catalogo(self._s))
        if not indicador:
            return self._abster(
                "não identifiquei a qual indicador a pergunta se refere; informe o código "
                "(ex.: 'trabalho.emprego.saldo_caged')."
            )

        try:
            de, ate = _parse_mes(p.de), _parse_mes(p.ate)
        except (ValueError, TypeError):
            return self._abster("período inválido; use o formato YYYY-MM.")

        # Resolve território pelo nome na pergunta se não foi fornecido explicitamente.
        territorio = p.territorio or await self._resolver_territorio(pergunta)

        contexto = await recuperar(
            self._s, indicador=indicador, territorio=territorio, de=de, ate=ate
        )
        if contexto is None:
            return self._abster(f"não há o indicador '{indicador}' no repositório.")
        if not contexto.valores:
            return self._abster(
                f"não há dado público para '{indicador}' no recorte pedido (território/período)."
            )

        # Se sem território e resultado com muitos territórios distintos → pede precisão.
        if territorio is None and len(contexto.valores) > 20:
            return self._abster(
                "a pergunta retornou dados de muitos municípios ao mesmo tempo. "
                "Informe o nome do município no campo 'Município' ou adicione o código IBGE "
                "(ex.: '3304557' para Rio de Janeiro-RJ)."
            )

        return RespostaIA(
            resposta=await self._narrador.narrar(contexto),
            abstencao=False,
            citacoes=[self._citacao(contexto)],
            ressalvas=self._ressalvas(contexto),
            revisao_humana=bool(contexto.indicador["origem_sensivel"]),
            narrador=self._narrador.id,
        )

    def _abster(self, motivo: str) -> RespostaIA:
        return RespostaIA(
            resposta=f"Não posso responder com segurança: {motivo}",
            abstencao=True,
            citacoes=[],
            ressalvas=["A IA só afirma o que recupera do repositório; sem dado, abstém-se."],
            revisao_humana=False,
            narrador=self._narrador.id,
        )

    def _citacao(self, contexto: ContextoIA) -> Citacao:
        vals = contexto.valores
        return Citacao(
            indicador=contexto.indicador["codigo"],
            nome=contexto.indicador["nome"],
            fonte=contexto.indicador["fonte_nome"],
            metodologia=contexto.indicador["metodologia"],
            periodo_de=vals[0]["periodo"].strftime("%Y-%m"),
            periodo_ate=vals[-1]["periodo"].strftime("%Y-%m"),
            lag_tipico_dias=contexto.indicador["fonte_lag"],
        )

    def _ressalvas(self, contexto: ContextoIA) -> list[str]:
        ressalvas = ["Descrição do dado recuperado — sem inferência de causalidade."]
        lag = contexto.indicador["fonte_lag"]
        if lag:
            ressalvas.append(f"Considere a defasagem típica de ~{lag} dias da fonte.")
        if len(contexto.valores) > 1:
            ressalvas.append("Comparações entre períodos pedem cautela (sazonalidade, séries).")
        if contexto.indicador["origem_sensivel"]:
            ressalvas.append("Origem sensível — recomenda-se revisão humana antes de uso crítico.")
        return ressalvas
