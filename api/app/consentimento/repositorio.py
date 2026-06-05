"""Acesso ao schema ``app`` como ``role_consentimento`` — escrita de PII isolada + auditoria.

Toda operação registra ``app.auditoria_acesso`` (§8.1.5). A condição sensível é cifrada antes de
gravar (cifragem de campo). O contato já chega pseudonimizado (``contato_hash``).
"""

from __future__ import annotations

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.consentimento.cripto import cifrar
from app.core.erros import ValidacaoError


async def _territorio_id(session: AsyncSession, codigo_ibge: str) -> int:
    rid = (
        await session.execute(
            text("SELECT id FROM territorio WHERE codigo_ibge = :c"), {"c": codigo_ibge}
        )
    ).scalar_one_or_none()
    if rid is None:
        raise ValidacaoError(f"território '{codigo_ibge}' inexistente")
    return int(rid)


async def _base_legal_id(session: AsyncSession, codigo: str) -> int:
    rid = (
        await session.execute(text("SELECT id FROM base_legal WHERE codigo = :c"), {"c": codigo})
    ).scalar_one_or_none()
    if rid is None:
        raise RuntimeError(f"base legal '{codigo}' não cadastrada (rode o seed).")
    return int(rid)


async def auditar(
    session: AsyncSession, *, ator: str, acao: str, recurso: str, detalhe: str | None = None
) -> None:
    await session.execute(
        text(
            "INSERT INTO app.auditoria_acesso (ator, acao, recurso, detalhe) "
            "VALUES (:a, :ac, :r, :d)"
        ),
        {"a": ator, "ac": acao, "r": recurso, "d": detalhe},
    )


async def assinar(
    session: AsyncSession,
    *,
    contato_hash: str,
    territorio_codigo: str,
    finalidade: str,
    condicao_sensivel: str | None,
) -> int:
    territorio_id = await _territorio_id(session, territorio_codigo)
    base_legal = await _base_legal_id(session, "consentimento")
    aid = (
        await session.execute(
            text(
                "INSERT INTO app.assinante_alerta "
                "(contato_hash, territorio_id, finalidade, base_legal_id, consentido_em) "
                "VALUES (:h, :t, :f, :b, now()) RETURNING id"
            ),
            {"h": contato_hash, "t": territorio_id, "f": finalidade, "b": base_legal},
        )
    ).scalar_one()
    if condicao_sensivel:
        base_sensivel = await _base_legal_id(session, "consentimento_sensivel")
        await session.execute(
            text(
                "INSERT INTO app.condicao_sensivel "
                "(assinante_id, tipo, base_legal_id, consentido_em) VALUES (:a, :t, :b, now())"
            ),
            {"a": aid, "t": cifrar(condicao_sensivel), "b": base_sensivel},
        )
    await auditar(session, ator=contato_hash, acao="assinar", recurso=f"assinante_alerta:{aid}")
    return int(aid)


async def listar(session: AsyncSession, contato_hash: str) -> list[RowMapping]:
    linhas = (
        (
            await session.execute(
                text(
                    """
                SELECT a.id, t.codigo_ibge, a.finalidade, a.consentido_em,
                       EXISTS (SELECT 1 FROM app.condicao_sensivel c WHERE c.assinante_id = a.id)
                         AS tem_condicao
                FROM app.assinante_alerta a JOIN territorio t ON t.id = a.territorio_id
                WHERE a.contato_hash = :h AND a.revogado_em IS NULL
                ORDER BY a.id
                """
                ),
                {"h": contato_hash},
            )
        )
        .mappings()
        .all()
    )
    await auditar(session, ator=contato_hash, acao="listar", recurso="assinante_alerta")
    return list(linhas)


async def revogar(session: AsyncSession, contato_hash: str, alerta_id: int) -> bool:
    res = await session.execute(
        text(
            "UPDATE app.assinante_alerta SET revogado_em = now() "
            "WHERE id = :i AND contato_hash = :h AND revogado_em IS NULL"
        ),
        {"i": alerta_id, "h": contato_hash},
    )
    ok = (res.rowcount or 0) > 0  # type: ignore[attr-defined]  # CursorResult em runtime
    if ok:
        await auditar(
            session, ator=contato_hash, acao="revogar", recurso=f"assinante_alerta:{alerta_id}"
        )
    return ok


async def eliminar(session: AsyncSession, contato_hash: str) -> int:
    """LGPD Art. 18 — elimina todos os dados do cidadão (cascade na condição sensível)."""
    res = await session.execute(
        text("DELETE FROM app.assinante_alerta WHERE contato_hash = :h"), {"h": contato_hash}
    )
    n = res.rowcount or 0  # type: ignore[attr-defined]  # CursorResult em runtime
    await auditar(
        session, ator=contato_hash, acao="eliminar", recurso="assinante_alerta", detalhe=f"{n}"
    )
    return n
