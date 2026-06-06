"""Emissão/revogação de chaves do tier profundo (admin).

  python -m app.profundo.run_chaves emitir "<nome do cliente>"
  python -m app.profundo.run_chaves revogar <id>

Roda como ADMIN (a role analítica não escreve em ``chave_api`` — migração 0014). A chave bruta é
exibida UMA vez na emissão; guarde-a (só o hash fica no banco). Ver ADR-0020.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.profundo.chaves import emitir_chave, revogar_chave


def _url_admin() -> str:
    url = get_settings().admin_database_url
    if not url:
        raise RuntimeError("ADMIN_DATABASE_URL é necessária (emissão/revogação são admin).")
    return url


async def _emitir(cliente: str) -> None:
    async with connect(_url_admin()) as conn:
        cid, bruta = await emitir_chave(conn, cliente)
    print(f"chave emitida (id={cid}, cliente={cliente!r}):")
    print(bruta)
    print("GUARDE AGORA — não é recuperável (só o hash fica no banco).")


async def _revogar(chave_id: int) -> None:
    async with connect(_url_admin()) as conn:
        ok = await revogar_chave(conn, chave_id)
    print("revogada" if ok else f"nada a revogar (id={chave_id} inexistente ou já revogada)")


def main() -> None:  # pragma: no cover - entrypoint CLI
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "emitir":
        asyncio.run(_emitir(args[1]))
    elif len(args) == 2 and args[0] == "revogar":
        asyncio.run(_revogar(int(args[1])))
    else:
        print('uso: run_chaves emitir "<cliente>" | revogar <id>')
        raise SystemExit(2)


if __name__ == "__main__":  # pragma: no cover
    main()
