"""Registro de plugins — módulos de domínio (§6).

Acrescentar um domínio é implementar ``ModuloDominio`` e registrá-lo; o núcleo não muda
(Open/Closed). Nesta fatia nenhum módulo é entregue, mas o encaixe existe: ``domains/trabalho/``
entra depois sem tocar no core. A API genérica de leitura (``indicadores``) já serve qualquer
dado que os domínios alimentem.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from fastapi import APIRouter


@runtime_checkable
class ModuloDominio(Protocol):
    codigo: str  # 'trabalho' — identidade / ponto de entrada
    versao_core: str  # compatibilidade com o núcleo

    def registrar_indicadores(self) -> list[object]: ...
    def registrar_adaptadores_fonte(self) -> list[object]: ...
    def registrar_rotas_api(self, router: APIRouter) -> None: ...
    def registrar_paineis(self) -> list[object]: ...
    def ativar(self) -> None: ...
    def desativar(self) -> None: ...


class RegistroModulos:
    """Mantém os módulos ativos e agrega suas rotas no app."""

    def __init__(self) -> None:
        self._modulos: dict[str, ModuloDominio] = {}

    def registrar(self, modulo: ModuloDominio) -> None:
        if modulo.codigo in self._modulos:
            raise ValueError(f"Módulo de domínio duplicado: {modulo.codigo}")
        modulo.ativar()
        self._modulos[modulo.codigo] = modulo

    def montar_rotas(self, router: APIRouter) -> None:
        for modulo in self._modulos.values():
            modulo.registrar_rotas_api(router)

    @property
    def codigos(self) -> list[str]:
        return sorted(self._modulos)


registro = RegistroModulos()
