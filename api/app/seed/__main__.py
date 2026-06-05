"""Entrypoint: ``python -m app.seed`` — semeia via o caminho ouro compartilhado."""

from __future__ import annotations

import asyncio

from app.seed import main

if __name__ == "__main__":
    asyncio.run(main())
