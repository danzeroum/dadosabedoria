"""Narrador — adaptador de geração. Troca o provedor sem mexer no serviço (§2/§9).

``NarradorTemplate`` (padrão): determinístico, templa SÓ o dado recuperado e cita a fonte — não
inventa número e não afirma causalidade, por construção (satisfaz o invariante 3).
``NarradorLLM``: provedor real via API **OpenAI-compatível** (DeepSeek hospedado ou Ollama local),
escolhido por config. Mantém o invariante 3 com três travas: (1) o LLM só recebe os fatos
recuperados (sem DB, sem PII); (2) as citações continuam determinísticas (montadas no serviço);
(3) **ancoragem numérica** — se a resposta trouxer um número que não veio dos fatos, cai para o
template. Falha/timeout do provedor também cai para o template (degradação graciosa).
"""

from __future__ import annotations

from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.observabilidade import get_logger
from app.ia.guardrails import numeros, sanitizar, validar_numeros_ancorados
from app.ia.recuperacao import ContextoIA

_log = get_logger("ia.narrador")

_SISTEMA = (
    "Você é um narrador de dados públicos brasileiros. Responda em português do Brasil, "
    "em 1 a 3 frases curtas. REGRAS INEGOCIÁVEIS: use SOMENTE os dados do bloco DADOS (sem "
    "conhecimento externo); NUNCA invente nem calcule números — só cite números que aparecem "
    "nos DADOS; NÃO afirme causa/efeito nem faça projeções, apenas descreva; cite a fonte ao "
    "final; se os DADOS estiverem vazios, diga que não há dado para responder."
)


def _pontos(contexto: ContextoIA) -> list[str]:
    pontos: list[str] = []
    for r in contexto.valores:
        periodo = r["periodo"].strftime("%Y-%m")
        if r["suprimido"]:
            pontos.append(f"{periodo}: dado protegido ({r['motivo_supressao']})")
        else:
            conf = r["confiabilidade"]
            sufixo = f" (confiabilidade {conf}/5)" if conf is not None else ""
            pontos.append(f"{periodo}: {r['valor']}{sufixo}")
    return pontos


class Narrador(Protocol):
    id: str

    async def narrar(self, contexto: ContextoIA) -> str: ...


class NarradorTemplate:
    id = "template-v1"

    async def narrar(self, contexto: ContextoIA) -> str:
        nome_ind = contexto.indicador["nome"]
        fonte = contexto.indicador["fonte_nome"]
        # Usa o nome do território (resolvido na recuperação) ou o código como fallback.
        nome_local = contexto.territorio_nome or contexto.territorio
        local = f" em {nome_local}" if nome_local else ""
        pontos = _pontos(contexto)
        # Limita a 12 pontos para não inundar a resposta
        if len(pontos) > 12:
            pontos = pontos[-12:]
            prefixo = f"(mostrando os {len(pontos)} períodos mais recentes) "
        else:
            prefixo = ""
        corpo = "; ".join(pontos)
        return f"{nome_ind}{local} — {prefixo}{corpo}. Fonte: {fonte}."


class NarradorLLM:
    """Narrador via API OpenAI-compatível (DeepSeek/Ollama). ``transport`` injetável p/ testes."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
        fallback: Narrador | None = None,
    ) -> None:
        self.id = f"llm:{model}"
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout
        self._transport = transport
        self._fallback: Narrador = fallback or NarradorTemplate()

    def _dados(self, contexto: ContextoIA) -> str:
        cab = (
            f"indicador: {contexto.indicador['nome']}; "
            f"território: {contexto.territorio or 'todos'}; "
            f"fonte: {contexto.indicador['fonte_nome']}"
        )
        return f"DADOS ({cab}):\n" + "\n".join(f"- {p}" for p in _pontos(contexto))

    async def _chamar(self, dados: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": _SISTEMA},
                {"role": "user", "content": dados + "\n\nDescreva esses dados, citando a fonte."},
            ],
            "temperature": 0,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as c:
            resp = await c.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return str(data["choices"][0]["message"]["content"])

    async def narrar(self, contexto: ContextoIA) -> str:
        dados = self._dados(contexto)
        permitidos = numeros(dados)
        try:
            texto = sanitizar(await self._chamar(dados))
        except Exception as exc:  # rede/timeout/resposta malformada → degrada para o template
            _log.warning("llm_indisponivel_fallback", erro=str(exc), narrador=self.id)
            return await self._fallback.narrar(contexto)
        if not texto or not validar_numeros_ancorados(texto, permitidos):
            _log.warning("llm_resposta_nao_ancorada_fallback", narrador=self.id)
            return await self._fallback.narrar(contexto)
        return texto


def narrador_padrao() -> Narrador:
    """Devolve o NarradorLLM se houver provedor configurado; senão o template determinístico."""
    s = get_settings()
    if s.llm_base_url and s.llm_model:
        return NarradorLLM(
            base_url=s.llm_base_url,
            model=s.llm_model,
            api_key=s.llm_api_key,
            timeout=s.llm_timeout_segundos,
        )
    return NarradorTemplate()
