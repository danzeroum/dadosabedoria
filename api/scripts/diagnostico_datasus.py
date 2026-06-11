#!/usr/bin/env python3
"""Diagnóstico de conectividade e forma do DATASUS/SIH — SOMENTE LEITURA.

Roda dentro do worker da VPS e faz, numa execução:

  1. CONECTIVIDADE: testa FTP em ftp.datasus.gov.br (passivo, anônimo).
  2. NAVEGA a árvore FTP /dissemin/publicos/SIHSUS/ e descobre o diretório
     e arquivo mais recente — sem hardcode de caminho.
  3. BAIXA um arquivo .dbc de uma UF pequena (RO — menor volume).
  4. DECODIFICA DBC→DataFrame (datasus_dbc + dbfread + polars) e IMPRIME A FORMA:
     colunas, shape, encoding (SIH = sempre latin-1), primeiras linhas.
     Verifica presença de MUNIC_RES e DIAG_PRINC (CONTRATO do adaptador).
     Imprime distribuição de CID-10 para confirmar grupo J.
  5. SALVA amostra (~2.000 linhas) em
     api/tests/fixtures/datasus_amostra_real.csv para commitar.
  6. NÃO grava no banco (diagnóstico é read-only e seguro em produção).

NOTA DE PRIVACIDADE (ADR-0004):
  A contagem de AIH respiratórias é o n_amostra do k-anonimato. O pipeline
  ouro suprime municípios com contagem < n_minimo (default 5). Este script
  não agrega nem escreve — apenas inspeciona o bruto. Nenhum dado pessoal
  é persistido fora da fixture de teste (já agregada por município).

Uso:
  docker compose --profile ingestion run --rm worker \\
    python scripts/diagnostico_datasus.py
"""

from __future__ import annotations

import ftplib
import io
import os
import socket
import sys
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
FTP_HOST = "ftp.datasus.gov.br"
FTP_BASE = "/dissemin/publicos/SIHSUS"
FTP_TIMEOUT = 30  # segundos — DATASUS pode ser mais lento

# UF pequena para minimizar o download (~1–5 MB vs ~50 MB de SP).
# AC (Acre), RO (Rondônia) são as menores. Ajuste se necessário.
UF_AMOSTRA = "RO"

# Dentro do container: __file__ = /app/scripts/diagnostico_datasus.py
# /app/ já É a pasta api/ — não há sub-nível api/ dentro do container.
REPO_ROOT = Path(__file__).resolve().parent.parent  # /app/
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"
AMOSTRA_PATH = FIXTURE_DIR / "datasus_amostra_real.csv"
AMOSTRA_LINHAS = 2_000

SEP = "=" * 70


def _sep(titulo: str) -> None:
    print(f"\n{SEP}")
    print(f"  {titulo}")
    print(SEP)


# ---------------------------------------------------------------------------
# 1. CONECTIVIDADE FTP
# ---------------------------------------------------------------------------


def _testar_porta_ftp() -> bool:
    try:
        s = socket.create_connection((FTP_HOST, 21), timeout=FTP_TIMEOUT)
        s.close()
        return True
    except (TimeoutError, OSError):
        return False


def _conectar_ftp() -> ftplib.FTP | None:
    ftp = ftplib.FTP(encoding="latin-1")  # noqa: S321 — DATASUS usa Windows-1252/latin-1
    try:
        ftp.connect(FTP_HOST, 21, timeout=FTP_TIMEOUT)
        ftp.login()  # anônimo
        ftp.set_pasv(True)  # modo passivo (obrigatório em containers com NAT)
        return ftp
    except Exception as exc:
        print(f"  ERRO ao conectar: {exc}")
        try:
            ftp.close()
        except Exception as close_exc:  # noqa: BLE001
            print(f"  (ignorando erro ao fechar: {close_exc})")
        return None


def verificar_conectividade_ftp() -> bool:
    _sep("1. CONECTIVIDADE FTP")
    print(f"  Host:    {FTP_HOST}:21")
    print(f"  Timeout: {FTP_TIMEOUT}s\n")

    if not _testar_porta_ftp():
        print("  RESULTADO: BLOQUEADO — porta 21 inacessível (socket timeout/refused)")
        print("  → Solicite ao administrador: liberar ftp.datasus.gov.br porta 21")
        return False

    print("  Porta 21: ALCANÇÁVEL")
    ftp = _conectar_ftp()
    if ftp is None:
        print("  RESULTADO: BLOQUEADO — porta aberta mas login FTP falhou")
        return False

    print(f"  Login anônimo: OK — banner: {ftp.getwelcome()!r:.80}")
    ftp.quit()
    print("  RESULTADO: ACESSÍVEL ✅")
    return True


# ---------------------------------------------------------------------------
# 2. NAVEGAR ÁRVORE FTP E LOCALIZAR ARQUIVO .DBC
# ---------------------------------------------------------------------------


def _listar_dir(ftp: ftplib.FTP, path: str) -> list[str]:
    try:
        ftp.cwd(path)
        entries: list[str] = []
        ftp.retrlines("NLST", entries.append)
        return sorted(entries)
    except ftplib.all_errors as exc:
        print(f"  AVISO: não consegui listar '{path}': {exc}")
        return []


def localizar_arquivo(ftp: ftplib.FTP) -> tuple[str, str, str] | None:
    """Navega a árvore FTP e retorna (caminho_completo, competencia, uf) do arquivo mais recente.

    Estrutura típica:
      /dissemin/publicos/SIHSUS/
        200801_/Dados/  ← formato YYYYMM_
        ...
      → /dissemin/publicos/SIHSUS/200801_/Dados/RDRO2604.dbc
    """
    _sep("2. NAVEGAÇÃO E LOCALIZAÇÃO DO ARQUIVO")
    print(f"  Base: {FTP_BASE}\n")

    base_entries = _listar_dir(ftp, FTP_BASE)
    print(f"  Entradas em {FTP_BASE}: {base_entries}")

    # Diretórios no formato YYYYMM_ (e.g. "200801_")
    dirs_periodo = sorted(
        [e for e in base_entries if e.endswith("_") and e[:-1].isdigit()],
        reverse=True,
    )
    if not dirs_periodo:
        print(f"  ERRO: nenhum diretório YYYYMM_ encontrado em {FTP_BASE}")
        return None

    dir_mais_recente = dirs_periodo[0]
    print(f"  Diretório mais recente: {dir_mais_recente}")

    caminho_dados = f"{FTP_BASE}/{dir_mais_recente}/Dados"
    arquivos = _listar_dir(ftp, caminho_dados)
    print(f"  Arquivos em {caminho_dados} (primeiros 30): {arquivos[:30]}")

    # Procura RD{UF_AMOSTRA}*.dbc mais recente
    prefixo_uf = f"RD{UF_AMOSTRA.upper()}"
    candidatos_uf = sorted(
        [a for a in arquivos if a.upper().startswith(prefixo_uf) and a.lower().endswith(".dbc")],
        reverse=True,
    )
    if not candidatos_uf:
        # Fallback: qualquer UF pequena
        for uf_fallback in ("RDAC", "RDAP", "RDRO", "RDTO", "RDAL"):
            candidatos_uf = sorted(
                [
                    a
                    for a in arquivos
                    if a.upper().startswith(uf_fallback) and a.lower().endswith(".dbc")
                ],
                reverse=True,
            )
            if candidatos_uf:
                print(f"  AVISO: {UF_AMOSTRA} não encontrado, usando fallback {uf_fallback[2:]}")
                break

    if not candidatos_uf:
        print(f"  ERRO: nenhum RD*.dbc encontrado para UF {UF_AMOSTRA}")
        print(f"  Arquivos disponíveis: {arquivos[:50]}")
        return None

    arquivo = candidatos_uf[0]
    # Extrai competência do nome (RDRO2604.dbc → aamm="2604", ano=20+26=2026, mes=04)
    nome_base = arquivo.upper().replace(".DBC", "")
    competencia_raw = nome_base[4:]  # e.g. "2604"
    caminho_completo = f"{caminho_dados}/{arquivo}"
    uf_detectada = nome_base[2:4]
    print(f"\n  ARQUIVO ENCONTRADO: {caminho_completo}")
    print(f"  UF: {uf_detectada}  Competência (AAMM): {competencia_raw}")
    return caminho_completo, competencia_raw, uf_detectada


# ---------------------------------------------------------------------------
# 3. DOWNLOAD DO .DBC
# ---------------------------------------------------------------------------


def baixar_dbc(ftp: ftplib.FTP, caminho: str) -> bytes | None:
    _sep("3. DOWNLOAD DO ARQUIVO .DBC")

    try:
        _tam = ftp.size(caminho)
        if _tam is not None:
            print(f"  Tamanho no FTP: {_tam / 1_048_576:.2f} MB ({_tam:,} bytes)")
    except ftplib.all_errors:
        print("  Tamanho: não disponível via FTP SIZE")

    print(f"  Baixando {caminho} ...")
    buf = io.BytesIO()
    t0 = time.time()
    try:
        ftp.retrbinary(f"RETR {caminho}", buf.write)
    except ftplib.all_errors as exc:
        print(f"  ERRO no download: {exc}")
        return None

    elapsed = time.time() - t0
    raw = buf.getvalue()
    print(f"  Download: {len(raw) / 1_048_576:.2f} MB em {elapsed:.1f}s  OK ✅")
    return raw


# ---------------------------------------------------------------------------
# 4. DECODIFICAR DBC E ANALISAR FORMA
# ---------------------------------------------------------------------------


def decodificar_e_analisar(dbc_bytes: bytes, nome_arquivo: str) -> bytes | None:
    """Decodifica DBC → CSV bytes via datasus_dbc + dbfread + polars (sem pysus/pandas)."""
    import polars as pl
    from datasus_dbc import decompress
    from dbfread import DBF

    _sep("4. DECODIFICAÇÃO DBC E FORMA")
    print(f"  Arquivo: {nome_arquivo}")
    print(f"  Tamanho DBC: {len(dbc_bytes) / 1_048_576:.2f} MB")
    print("  Decoder: datasus_dbc (Rust) + dbfread + polars")

    fd, tmp_dbc = tempfile.mkstemp(suffix=".dbc")
    os.close(fd)
    tmp_dbf = tmp_dbc[:-4] + ".dbf"
    try:
        with open(tmp_dbc, "wb") as f:
            f.write(dbc_bytes)
        print("  Decodificando DBC → DBF (datasus_dbc) ...")
        decompress(tmp_dbc, tmp_dbf)
        print("  Lendo DBF (dbfread) → polars DataFrame ...")
        table = DBF(tmp_dbf, encoding="latin-1")
        df = pl.DataFrame(list(table))
    except Exception as exc:
        print(f"  ERRO na decodificação DBC: {exc}")
        return None
    finally:
        for p in (tmp_dbc, tmp_dbf):
            try:
                os.unlink(p)
            except OSError:
                pass

    n_linhas, n_colunas = df.shape
    print(f"\n  Shape: {n_linhas:,} linhas × {n_colunas} colunas")
    print(f"\n  Colunas ({n_colunas}):")
    for col in df.columns:
        dtype = df[col].dtype
        n_nulos = df[col].null_count()
        vals = df[col].drop_nulls()
        ex = str(vals[0]) if len(vals) > 0 else "—"
        print(f"    {col!r:<45} {str(dtype):<15} nulos={n_nulos:<6} ex={ex!r:.30}")

    # Verificação do CONTRATO (MUNIC_RES + DIAG_PRINC obrigatórios)
    print("\n  Verificação do CONTRATO (app.ingestao.adaptadores.datasus):")
    for col_req in ("MUNIC_RES", "DIAG_PRINC"):
        presente = col_req in df.columns
        status = "✅ PRESENTE" if presente else "❌ AUSENTE — CONTRATO QUEBRADO"
        print(f"    {col_req}: {status}")

    # Distribuição CID-10 (DIAG_PRINC)
    if "DIAG_PRINC" in df.columns:
        print("\n  Distribuição CID-10 (DIAG_PRINC) — grupo J = respiratório:")
        dist = (
            df.select(pl.col("DIAG_PRINC").cast(pl.Utf8).str.slice(0, 1).alias("g"))
            .group_by("g")
            .agg(pl.len().alias("n"))
            .sort("n", descending=True)
            .head(10)
        )
        for row in dist.iter_rows(named=True):
            letra, contagem = row["g"], row["n"]
            marcador = " ← grupo respiratório" if letra == "J" else ""
            print(f"    {letra}: {contagem:>6} ({100 * contagem / n_linhas:.1f}%){marcador}")

    print("\n  Primeiras 5 linhas:")
    print(df.head(5))

    return df.write_csv().encode("utf-8")


# ---------------------------------------------------------------------------
# 5. SALVAR AMOSTRA
# ---------------------------------------------------------------------------


def salvar_amostra(csv_bytes: bytes, competencia_raw: str, uf: str) -> None:
    _sep("5. SALVAR AMOSTRA")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    linhas = csv_bytes.decode("utf-8").splitlines(keepends=True)
    cabecalho = linhas[:1]
    dados = linhas[1 : AMOSTRA_LINHAS + 1]

    amostra = "".join(cabecalho + dados)
    AMOSTRA_PATH.write_text(amostra, encoding="utf-8")

    n = len(dados)
    print(f"  Salvo: {AMOSTRA_PATH}")
    print(f"  Linhas: {n} + 1 cabeçalho  (UF={uf}, comp={competencia_raw})")
    print()
    # Commit no host (container tem /app/ = api/; host usa api/tests/fixtures/)
    print("  Commit no host (após docker cp ou com volume montado):")
    print("    cd /opt/btv/dadosabedoria")
    print("    git add api/tests/fixtures/datasus_amostra_real.csv")
    aamm = competencia_raw  # e.g. "2604"
    print(f"    git commit -m 'fixture: amostra real DATASUS/SIH RD{uf}{aamm}'")
    print()
    print("  PRÓXIMO PASSO: commitar a amostra e colar a saída deste script no chat.")
    print("  O dev valida o parser, promove a fixture e fecha o ADR.")
    print()
    print("  LEMBRETE DE PRIVACIDADE: esta fixture contém linhas brutas de AIH (dado já")
    print("  público/anonimizado pelo DATASUS). Para a tela, apenas a contagem por município")
    print("  entra no banco — a supressão k-anon (n_minimo=5) ocorre no caminho ouro (ADR-0004).")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main() -> None:
    _sep("DIAGNÓSTICO DATASUS/SIH — SOMENTE LEITURA")
    print(f"  Host: {FTP_HOST}")
    print(f"  UF de amostra: {UF_AMOSTRA}")
    print(f"  Fixture destino: {AMOSTRA_PATH}")
    print("  Decoder: datasus_dbc (Rust wheel) + dbfread + polars — sem pysus/pandas")

    # 1. Conectividade
    if not verificar_conectividade_ftp():
        print("\nAbortando — FTP inacessível.")
        print("Solicite ao administrador da VPS: liberar ftp.datasus.gov.br porta 21.")
        sys.exit(1)

    # Abrir conexão para as etapas seguintes
    ftp = _conectar_ftp()
    if ftp is None:
        print("Erro ao abrir conexão FTP para navegação.")
        sys.exit(1)

    # 2. Localizar arquivo
    resultado = localizar_arquivo(ftp)
    if resultado is None:
        ftp.quit()
        sys.exit(1)
    caminho_completo, competencia_raw, uf_detectada = resultado

    # 3. Baixar DBC
    dbc_bytes = baixar_dbc(ftp, caminho_completo)
    ftp.quit()
    if dbc_bytes is None:
        sys.exit(1)

    # 4. Decodificar e analisar
    csv_bytes = decodificar_e_analisar(dbc_bytes, caminho_completo.split("/")[-1])
    if csv_bytes is None:
        sys.exit(1)

    # 5. Salvar amostra
    salvar_amostra(csv_bytes, competencia_raw, uf_detectada)

    _sep("CONCLUÍDO")
    print("  Forma do SIH-RD inspecionada. Próximos passos:")
    print("  1. Commitar api/tests/fixtures/datasus_amostra_real.csv (comando acima)")
    print("  2. Colar a saída deste script no chat → dev promove fixture + fecha ADR")
    print("  3. Liberar ftp.datasus.gov.br no allowlist do contêiner de ingestão")
    print("  4. Rodar ingestão: python -m app.ingestao.run_datasus <ano> <mes>")
    print()


if __name__ == "__main__":
    main()
