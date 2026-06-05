"""O worker (stub nesta fatia) deve apenas configurar logs e logar — sem lançar."""

from __future__ import annotations

from app.worker import main


def test_worker_main_nao_lanca() -> None:
    main()
