"""Narrador — adaptador de geração. Troca o provedor sem mexer no serviço (§2/§9).

``NarradorTemplate`` (padrão): determinístico, templa SÓ o dado recuperado e cita a fonte — não
inventa número e não afirma causalidade, por construção (satisfaz o invariante 3).
``NarradorLLM``: ponto de plugue do provedor real (atrás de ``LLM_API_KEY`` + config) — chega quando
o provedor for escolhido; nos testes/CI usa-se o template.
"""

from __future__ import annotations

from typing import Protocol

from app.ia.recuperacao import ContextoIA


class Narrador(Protocol):
    id: str

    def narrar(self, contexto: ContextoIA) -> str: ...


class NarradorTemplate:
    id = "template-v1"

    def narrar(self, contexto: ContextoIA) -> str:
        nome = contexto.indicador["nome"]
        fonte = contexto.indicador["fonte_nome"]
        local = f" em {contexto.territorio}" if contexto.territorio else ""
        pontos: list[str] = []
        for r in contexto.valores:
            periodo = r["periodo"].strftime("%Y-%m")
            if r["suprimido"]:
                pontos.append(f"{periodo}: dado protegido ({r['motivo_supressao']})")
            else:
                conf = r["confiabilidade"]
                sufixo = f" (confiabilidade {conf}/5)" if conf is not None else ""
                pontos.append(f"{periodo}: {r['valor']}{sufixo}")
        corpo = "; ".join(pontos)
        return f"{nome}{local} — {corpo}. Fonte: {fonte}."


def narrador_padrao() -> Narrador:
    # Hoje sempre o template; quando houver provedor configurado, devolve o NarradorLLM.
    return NarradorTemplate()
