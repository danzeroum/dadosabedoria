#!/usr/bin/env python3
"""Diagnóstico de conectividade e forma do CAGED — SOMENTE LEITURA.

Roda dentro do worker da VPS e faz, numa execução:

  1. CONECTIVIDADE: testa FTP em ftp.mtps.gov.br (passivo, anônimo).
     Se bloqueado, testa caminhos HTTPS alternativos (dados.mte.gov.br,
     bi.mte.gov.br, ftp.mtps.gov.br/443).
  2. NAVEGA a árvore FTP /pdet/microdados/NOVO CAGED/ e descobre
     o arquivo mais recente — sem hardcode de caminho.
  3. BAIXA um arquivo .7z real, descompacta com py7zr.
  4. IMPRIME A FORMA: colunas, encoding, separador, 10 primeiras linhas,
     nº de linhas e tamanho do arquivo.
  5. SALVA amostra (~2.000 linhas) em
     api/tests/fixtures/caged_amostra_real.csv para commitar.
  6. NÃO grava no banco (diagnóstico é read-only e seguro em produção).

Uso:
  docker compose --profile ingestion run --rm worker \\
    python scripts/diagnostico_caged.py
"""

from __future__ import annotations

import ftplib
import io
import socket
import sys
import time
from pathlib import Path

import httpx
import polars as pl
import py7zr

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
FTP_HOST = "ftp.mtps.gov.br"
FTP_BASE = "/pdet/microdados/NOVO CAGED"
FTP_TIMEOUT = 20  # segundos

HTTPS_ALTERNATIVAS = [
    # candidatos a espelhos HTTPS — o script testa e reporta
    "https://ftp.mtps.gov.br/",
    "https://dados.mte.gov.br/",
    "https://bi.mte.gov.br/",
    "https://dadosabertos.mte.gov.br/",
]

# Dentro do container: __file__ = /app/scripts/diagnostico_caged.py
# /app/ já É a pasta api/ — não há sub-nível api/ dentro do container.
REPO_ROOT = Path(__file__).resolve().parent.parent  # /app/
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"  # /app/tests/fixtures/
AMOSTRA_PATH = FIXTURE_DIR / "caged_amostra_real.csv"
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
    """Testa porta 21 via socket antes de iniciar o FTP."""
    try:
        s = socket.create_connection((FTP_HOST, 21), timeout=FTP_TIMEOUT)
        s.close()
        return True
    except (TimeoutError, OSError):
        return False


def _conectar_ftp() -> ftplib.FTP | None:
    """Tenta conectar ao FTP; retorna FTP ou None se bloqueado."""
    ftp = ftplib.FTP(encoding="latin-1")  # noqa: S321 — servidor MTPS usa Windows-1252
    try:
        ftp.connect(FTP_HOST, 21, timeout=FTP_TIMEOUT)
        ftp.login()  # anônimo
        ftp.set_pasv(True)  # modo passivo (obrigatório em containers)
        return ftp
    except Exception as exc:
        print(f"  ERRO ao conectar: {exc}")
        ftp.close()
        return None


def verificar_conectividade_ftp() -> bool:
    _sep("1. CONECTIVIDADE FTP")
    print(f"  Host:    {FTP_HOST}:21")
    print(f"  Timeout: {FTP_TIMEOUT}s\n")

    if not _testar_porta_ftp():
        print("  RESULTADO: BLOQUEADO — porta 21 inacessível (socket timeout/refused)")
        print("  → O FTP puro não está disponível neste ambiente.")
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
# 2. NAVEGAR ÁRVORE FTP E LOCALIZAR ARQUIVO MAIS RECENTE
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


def localizar_arquivo(ftp: ftplib.FTP) -> tuple[str, str] | None:
    """Navega a árvore FTP e retorna (caminho_completo, competencia) do arquivo mais recente."""
    _sep("2. NAVEGAÇÃO E LOCALIZAÇÃO DO ARQUIVO")
    print(f"  Base: {FTP_BASE}\n")

    anos = _listar_dir(ftp, FTP_BASE)
    anos_numericos = [a for a in anos if a.isdigit() and len(a) == 4]
    if not anos_numericos:
        print(f"  ERRO: nenhum diretório de ano encontrado em {FTP_BASE}")
        print(f"  Entradas encontradas: {anos[:20]}")
        return None

    ano_recente = max(anos_numericos)
    print(f"  Anos disponíveis: {anos_numericos}")
    print(f"  Ano mais recente: {ano_recente}")

    competencias = _listar_dir(ftp, f"{FTP_BASE}/{ano_recente}")
    comp_validas = [c for c in competencias if c.isdigit() and len(c) == 6]
    if not comp_validas:
        print(f"  ERRO: nenhuma competência encontrada em {FTP_BASE}/{ano_recente}")
        print(f"  Entradas encontradas: {competencias[:20]}")
        return None

    comp_recente = max(comp_validas)
    print(f"  Competências em {ano_recente}: {comp_validas[-6:]}")  # últimas 6
    print(f"  Competência mais recente: {comp_recente}")

    path_comp = f"{FTP_BASE}/{ano_recente}/{comp_recente}"
    arquivos = _listar_dir(ftp, path_comp)
    print(f"  Arquivos em {path_comp}: {arquivos}")

    # Procura CAGEDMOV*.7z
    candidatos = [a for a in arquivos if a.upper().startswith("CAGEDMOV") and a.endswith(".7z")]
    if not candidatos:
        print("  AVISO: nenhum CAGEDMOV*.7z — tentando qualquer .7z")
        candidatos = [a for a in arquivos if a.endswith(".7z")]
    if not candidatos:
        print("  ERRO: nenhum arquivo .7z encontrado")
        return None

    arquivo = candidatos[0]
    caminho_completo = f"{path_comp}/{arquivo}"
    print(f"\n  ARQUIVO ENCONTRADO: {caminho_completo}")
    return caminho_completo, comp_recente


# ---------------------------------------------------------------------------
# 3. DOWNLOAD E DESCOMPRESSÃO
# ---------------------------------------------------------------------------


def baixar_e_descomprimir(ftp: ftplib.FTP, caminho: str) -> tuple[bytes, str] | None:
    _sep("3. DOWNLOAD E DESCOMPRESSÃO")

    # Tamanho do arquivo
    try:
        _tam = ftp.size(caminho)
        if _tam is not None:
            print(f"  Tamanho no FTP: {_tam / 1_048_576:.1f} MB ({_tam:,} bytes)")
    except ftplib.all_errors:
        _tam = None
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
    print(f"  Download: {len(raw) / 1_048_576:.1f} MB em {elapsed:.1f}s")

    print("  Descompactando com py7zr ...")
    try:
        with py7zr.SevenZipFile(io.BytesIO(raw), mode="r") as z:
            nomes = z.getnames()
            print(f"  Arquivos no .7z: {nomes}")
            z.reset()
            conteudo_dict = z.read()
            # Pega o primeiro arquivo CSV/TXT
            nome_csv = next(
                (n for n in nomes if n.upper().endswith((".CSV", ".TXT"))),
                nomes[0] if nomes else None,
            )
            if nome_csv is None:
                print("  ERRO: nenhum arquivo CSV/TXT no .7z")
                return None
            csv_bytes = conteudo_dict[nome_csv].read()
            print(f"  Arquivo extraído: {nome_csv} ({len(csv_bytes) / 1_048_576:.1f} MB)")
            return csv_bytes, nome_csv
    except Exception as exc:
        print(f"  ERRO na descompressão: {exc}")
        return None


# ---------------------------------------------------------------------------
# 4. FORMA DO ARQUIVO
# ---------------------------------------------------------------------------


def analisar_forma(csv_bytes: bytes, nome_arquivo: str) -> pl.DataFrame | None:
    _sep("4. FORMA DO ARQUIVO")

    # Detectar encoding
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            amostra_txt = csv_bytes[:4096].decode(enc)
            encoding_detectado = enc
            break
        except UnicodeDecodeError:
            continue
    else:
        amostra_txt = csv_bytes[:4096].decode("latin-1", errors="replace")
        encoding_detectado = "latin-1 (fallback)"

    print(f"  Arquivo:  {nome_arquivo}")
    print(f"  Encoding: {encoding_detectado}")
    print(f"  Tamanho:  {len(csv_bytes) / 1_048_576:.2f} MB")

    # Detectar separador (primeira linha)
    primeira_linha = amostra_txt.split("\n")[0]
    print(f"  Cabeçalho bruto: {primeira_linha!r:.120}")

    sep = ";" if ";" in primeira_linha else ","
    print(f"  Separador: {sep!r}")

    # Contar linhas
    n_linhas = csv_bytes.count(b"\n")
    print(f"  Linhas (aprox.): {n_linhas:,}")

    # Ler com Polars
    try:
        df = pl.read_csv(
            io.BytesIO(csv_bytes),
            separator=sep,
            encoding="utf8-lossy",
            infer_schema_length=100,
            truncate_ragged_lines=True,
            ignore_errors=True,
        )
    except Exception as exc:
        print(f"  ERRO ao ler CSV com Polars: {exc}")
        return None

    print(f"\n  Shape: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    print(f"\n  Colunas ({df.shape[1]}):")
    for col in df.columns:
        dtype = df[col].dtype
        n_nulos = df[col].null_count()
        amostra_val = df[col].drop_nulls().head(1).to_list()
        amostra_val_str = str(amostra_val[0]) if amostra_val else "—"
        print(f"    {col!r:<45} {str(dtype):<15} nulos={n_nulos:<6} ex={amostra_val_str!r:.30}")

    print("\n  Primeiras 10 linhas:")
    with pl.Config(tbl_width_chars=140, tbl_rows=10):
        print(df.head(10))

    return df


# ---------------------------------------------------------------------------
# 5. SALVAR AMOSTRA
# ---------------------------------------------------------------------------


def salvar_amostra(csv_bytes: bytes, nome_arquivo: str, sep: str = ";") -> None:
    _sep("5. SALVAR AMOSTRA")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    linhas = csv_bytes.decode("utf-8-sig", errors="replace").splitlines(keepends=True)
    cabecalho = linhas[:1]
    dados = linhas[1 : AMOSTRA_LINHAS + 1]

    amostra = "".join(cabecalho + dados)
    AMOSTRA_PATH.write_text(amostra, encoding="utf-8")

    n = len(dados)
    print(f"  Salvo: {AMOSTRA_PATH}")
    print(f"  Linhas: {n} + 1 cabeçalho")
    print(f"  Commit sugerido: git add {AMOSTRA_PATH.relative_to(REPO_ROOT)}")
    print()
    # Caminho no HOST com volume montado:
    # -v /opt/btv/dadosabedoria/api/tests/fixtures:/app/tests/fixtures
    print("  Commit no host (após docker cp ou com volume montado):")
    print("    cd /opt/btv/dadosabedoria")
    print("    git add api/tests/fixtures/caged_amostra_real.csv")
    print("    git commit -m 'fixture: amostra real CAGEDMOV <competencia>'")
    print()
    print("  PRÓXIMO PASSO: commitar a amostra e colar a saída deste script no chat.")
    print("  O dev valida o parser, promove a fixture e fecha o ADR.")


# ---------------------------------------------------------------------------
# 6. HTTPS ALTERNATIVAS (se FTP bloqueado)
# ---------------------------------------------------------------------------


def testar_https_alternativas() -> None:
    _sep("6. HTTPS ALTERNATIVAS (FTP bloqueado — sondagem de espelhos)")
    for url in HTTPS_ALTERNATIVAS:
        try:
            r = httpx.get(
                url,
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "DadoSabedoria/1.0"},
            )
            print(f"  {url}")
            print(f"    → HTTP {r.status_code} ({len(r.content)} bytes)")
        except Exception as exc:
            print(f"  {url}")
            print(f"    → BLOQUEADO/ERRO: {exc}")
        print()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main() -> None:
    print(SEP)
    print("  DIAGNÓSTICO CAGED — DadoSabedoria")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(SEP)

    ftp_ok = verificar_conectividade_ftp()

    if not ftp_ok:
        testar_https_alternativas()
        _sep("RESULTADO FINAL")
        print("  FTP: BLOQUEADO")
        print("  Verifique as saídas do §6 para decidir o próximo passo:")
        print("  - Se alguma URL HTTPS retornou 200: avaliar se tem CAGEDMOV")
        print("  - Se tudo bloqueado: registrar na Lista de desbloqueio e aguardar")
        sys.exit(0)

    # FTP disponível — prosseguir
    ftp = _conectar_ftp()
    if ftp is None:
        print("ERRO: FTP acessível mas conexão falhou na segunda tentativa")
        sys.exit(1)

    resultado = localizar_arquivo(ftp)
    if resultado is None:
        ftp.quit()
        print("\nERRO: não foi possível localizar o arquivo na árvore FTP")
        sys.exit(1)

    caminho, competencia = resultado

    descomp = baixar_e_descomprimir(ftp, caminho)
    ftp.quit()

    if descomp is None:
        print("\nERRO: falha no download/descompressão")
        sys.exit(1)

    csv_bytes, nome_csv = descomp

    sep_csv = ";" if b";" in csv_bytes[:512] else ","
    df = analisar_forma(csv_bytes, nome_csv)

    if df is not None:
        salvar_amostra(csv_bytes, nome_csv, sep_csv)

    _sep("RESULTADO FINAL")
    print("  FTP:         ACESSÍVEL ✅")
    print(f"  Arquivo:     {caminho}")
    print(f"  Competência: {competencia}")
    if df is not None:
        print(f"  Shape:       {df.shape[0]:,} × {df.shape[1]}")
        colunas_necessarias = {"competênciamov", "município", "saldomovimentação"}
        encontradas = {c.lower().strip() for c in df.columns}
        faltam = colunas_necessarias - encontradas
        if faltam:
            print(f"  ⚠️  Colunas FALTANDO vs. fixture atual: {faltam}")
            print("     → Atualizar o parser/fixture antes de ingerir")
        else:
            print("  ✅ Colunas obrigatórias presentes (fixture compatível)")
    print(f"\n  Amostra salva em: {AMOSTRA_PATH}")


if __name__ == "__main__":
    main()
