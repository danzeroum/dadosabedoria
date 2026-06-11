#!/usr/bin/env python3
"""Diagnóstico de conectividade e forma do ESTBAN — SOMENTE LEITURA.

Roda dentro do worker da VPS e faz, numa execução:

  1. SONDA múltiplos padrões de URL do BCB com headers de browser.
     O portal BCB migrou para SPA Angular — o arquivo ZIP não está mais
     em path estático; o script tenta os padrões conhecidos + heurísticas.
  2. Para cada URL que retornar um ZIP válido:
     - Extrai o CSV
     - Valida colunas (CODMUN + verbete 160)
     - Imprime a forma (linhas, colunas, amostra)
  3. SALVA amostra (~500 linhas) em tests/fixtures/estban_amostra_real.csv
     para commitar e promover a fixture a fiel-à-forma (ADR-0007).
  4. IMPRIME a URL que funcionou para atualizar FetcherEstbanHTTP.BASE.

Uso:
  docker compose --profile ingestion run --rm worker \\
    python scripts/diagnostico_estban.py [YYYYMM]

  Exemplo: python scripts/diagnostico_estban.py 202502
  (default: competência mais recente esperada = T-3 meses)
"""

from __future__ import annotations

import io
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

import httpx
import polars as pl

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Dentro do container: __file__ = /app/scripts/diagnostico_estban.py
# /app/ já É a pasta api/ — sem sub-nível api/ dentro do container.
REPO_ROOT = Path(__file__).resolve().parent.parent  # /app/
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"
AMOSTRA_PATH = FIXTURE_DIR / "estban_amostra_real.csv"
AMOSTRA_LINHAS = 500  # ESTBAN é menor que CAGED; 500 linhas representam bem

COL_CODMUN = "CODMUN"
PADRAO_VERBETE = "160"

SEP = "=" * 70

# Headers que imitam um browser para não ser bloqueado pela SPA Angular.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/octet-stream,application/zip,*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Referer": "https://www.bcb.gov.br/estabilidadefinanceira/estatisticabancariamunicipios",
}


def _sep(titulo: str) -> None:
    print(f"\n{SEP}")
    print(f"  {titulo}")
    print(SEP)


def _competencia_padrao() -> str:
    """Competência mais recente esperada: T-3 meses (ESTBAN publica com ~60 dias de lag)."""
    hoje = date.today()
    mes = hoje.month - 3
    ano = hoje.year
    if mes <= 0:
        mes += 12
        ano -= 1
    return f"{ano}{mes:02d}"


def _candidatos_url(comp: str) -> list[tuple[str, str]]:
    """Retorna lista de (descrição, URL) a testar para a competência YYYYMM."""
    return [
        (
            "BCB estabilidadefinanceira/docs (antigo)",
            f"https://www.bcb.gov.br/estabilidadefinanceira/docs/estban/ESTBAN_MUNICIPIO_{comp}.ZIP",
        ),
        (
            "BCB content/estabilidadefinanceira/docs",
            f"https://www.bcb.gov.br/content/estabilidadefinanceira/docs/estban/"
            f"ESTBAN_MUNICIPIO_{comp}.ZIP",
        ),
        (
            "BCB fis/cosif (www4)",
            f"https://www4.bcb.gov.br/fis/cosif/ESTBAN_MUNICIPIO_{comp}.ZIP",
        ),
        (
            "BCB API servico estban download",
            f"https://www.bcb.gov.br/api/servico/sitebcb/estban/download?dataBase={comp}",
        ),
        (
            "BCB API servico sitebcb redirect",
            f"https://www.bcb.gov.br/api/servico/sitebcb/redirect/arquivos/"
            f"estban/ESTBAN_MUNICIPIO_{comp}.ZIP",
        ),
        (
            "BCB downloads (caminho alternativo)",
            f"https://www.bcb.gov.br/fis/cosif/estban/ESTBAN_MUNICIPIO_{comp}.ZIP",
        ),
    ]


# ---------------------------------------------------------------------------
# 1. SONDA DE URLs
# ---------------------------------------------------------------------------


def _eh_zip(dados: bytes) -> bool:
    """Verifica assinatura de ZIP (PK magic bytes)."""
    return dados[:2] == b"PK"


def _eh_html(dados: bytes) -> bool:
    return dados[:5].lower() in (b"<!doc", b"<html", b"<?xml")


def sondar_urls(comp: str) -> tuple[str, str, bytes] | None:
    """Testa cada URL candidata e retorna (descricao, url, bytes_zip) ao encontrar ZIP válido."""
    _sep("1. SONDA DE URLs DO BCB")
    print(f"  Competência: {comp}")
    print("  Headers: User-Agent browser + Referer BCB\n")

    candidatos = _candidatos_url(comp)
    for desc, url in candidatos:
        print(f"  [{desc}]")
        print(f"  URL: {url}")
        try:
            r = httpx.get(url, headers=BROWSER_HEADERS, timeout=30, follow_redirects=True)
            print(f"  → HTTP {r.status_code}  {len(r.content):,} bytes")
            if r.status_code == 200:
                if _eh_zip(r.content):
                    print("  → ZIP válido (assinatura PK) — ENCONTRADO ✅")
                    return desc, url, r.content
                if _eh_html(r.content):
                    print("  → HTML (SPA Angular ou página de erro) — continua")
                else:
                    # JSON ou outro — tentar extrair URL de redirect
                    try:
                        j = r.json()
                        print(f"  → JSON: {str(j)[:200]}")
                        # Procura campo 'url', 'link', 'href', 'arquivo'
                        for k in ("url", "link", "href", "arquivo", "path", "download"):
                            v = j.get(k) if isinstance(j, dict) else None
                            if v and isinstance(v, str) and v.startswith("http"):
                                print(f"  → JSON contém URL em '{k}': {v}")
                    except Exception:
                        print(f"  → Conteúdo não-JSON, não-ZIP, não-HTML ({r.content[:80]!r})")
            elif r.status_code in (301, 302, 303, 307, 308):
                loc = r.headers.get("location", "")
                print(f"  → Redirect para: {loc}")
            else:
                print(f"  → Código {r.status_code} — próxima URL")
        except httpx.TimeoutException:
            print("  → TIMEOUT (30s)")
        except Exception as exc:
            print(f"  → ERRO: {exc}")
        print()

    return None


# ---------------------------------------------------------------------------
# 2. EXTRAIR E VALIDAR ZIP
# ---------------------------------------------------------------------------


def extrair_zip(dados_zip: bytes) -> tuple[bytes, str] | None:
    _sep("2. EXTRAÇÃO DO ZIP")
    try:
        with zipfile.ZipFile(io.BytesIO(dados_zip)) as z:
            nomes = z.namelist()
            print(f"  Arquivos no ZIP: {nomes}")
            csv_nome = next(
                (n for n in nomes if n.upper().endswith((".CSV", ".TXT"))),
                nomes[0] if nomes else None,
            )
            if csv_nome is None:
                print("  ERRO: nenhum CSV/TXT no ZIP")
                return None
            conteudo = z.read(csv_nome)
            print(f"  Arquivo extraído: {csv_nome} ({len(conteudo) / 1_048_576:.2f} MB)")
            return conteudo, csv_nome
    except zipfile.BadZipFile as exc:
        print(f"  ERRO: não é um ZIP válido — {exc}")
        return None


# ---------------------------------------------------------------------------
# 3. ANALISAR FORMA
# ---------------------------------------------------------------------------


def analisar_forma(csv_bytes: bytes, nome_arquivo: str) -> pl.DataFrame | None:
    _sep("3. FORMA DO ARQUIVO")

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

    # Detectar preâmbulo (ESTBAN real tem 2 linhas antes do cabeçalho)
    linhas = amostra_txt.splitlines()
    print("\n  Primeiras 4 linhas brutas (para detectar skip_rows):")
    for i, ln in enumerate(linhas[:4]):
        print(f"    [{i}] {ln!r:.120}")

    # Linha do cabeçalho (primeira com CODMUN ou separador ';')
    skip = 0
    for i, ln in enumerate(linhas[:5]):
        if COL_CODMUN in ln or (ln.count(";") >= 2):
            skip = i
            break
    print(f"\n  skip_rows detectado: {skip}")

    # Separador
    cab = linhas[skip] if skip < len(linhas) else linhas[0]
    sep = ";" if ";" in cab else ","
    print(f"  Separador: {sep!r}")
    print(f"  Cabeçalho: {cab!r:.120}")

    # Total de linhas
    n_linhas = csv_bytes.count(b"\n")
    print(f"  Linhas (aprox.): {n_linhas:,}")

    # Ler com Polars
    try:
        df = pl.read_csv(
            io.BytesIO(csv_bytes),
            separator=sep,
            encoding="utf8-lossy",
            infer_schema_length=0,
            skip_rows=skip,
            ignore_errors=True,
        )
    except Exception as exc:
        print(f"  ERRO ao ler com Polars: {exc}")
        return None

    print(f"\n  Shape: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    print(f"\n  Colunas ({df.shape[1]}):")
    for col in df.columns:
        tem_verbete = PADRAO_VERBETE in col
        amostra = df[col].drop_nulls().head(1).to_list()
        av = str(amostra[0]) if amostra else "—"
        marca = " ← VERBETE CRÉDITO" if tem_verbete else ""
        marca2 = " ← CODMUN" if col == COL_CODMUN else ""
        print(f"    {col!r:<55} ex={av!r:.25}{marca}{marca2}")

    # Validar colunas obrigatórias
    colunas = set(df.columns)
    tem_codmun = COL_CODMUN in colunas
    tem_verbete_col = any(PADRAO_VERBETE in c for c in colunas)
    print(f"\n  CODMUN presente:          {'✅' if tem_codmun else '❌ FALTANDO'}")
    print(f"  Verbete 160 presente:     {'✅' if tem_verbete_col else '❌ FALTANDO'}")

    print("\n  Primeiras 5 linhas:")
    with pl.Config(tbl_width_chars=140, tbl_rows=5):
        print(df.head(5))

    return df


# ---------------------------------------------------------------------------
# 4. SALVAR FIXTURE
# ---------------------------------------------------------------------------


def salvar_fixture(csv_bytes: bytes, skip: int, sep: str) -> None:
    _sep("4. SALVAR FIXTURE")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    linhas_raw = csv_bytes.decode("utf8-lossy", errors="replace").splitlines(keepends=True)
    # Inclui as linhas de preâmbulo (skip) + cabeçalho + dados
    cabecalho_e_preambulo = linhas_raw[: skip + 1]
    dados = linhas_raw[skip + 1 : skip + 1 + AMOSTRA_LINHAS]
    amostra = "".join(cabecalho_e_preambulo + dados)

    AMOSTRA_PATH.write_text(amostra, encoding="utf-8")
    n = len(dados)
    print(f"  Salvo: {AMOSTRA_PATH}")
    print(f"  Linhas de dados: {n} + {skip + 1} linhas de cabeçalho/preâmbulo")
    print("\n  PRÓXIMOS PASSOS:")
    print(f"  1. git add {AMOSTRA_PATH}")
    print("  2. Atualizar FetcherEstbanHTTP.BASE com a URL confirmada")
    print("  3. Marcar fixture como fiel-à-forma no ADR-0007")
    print("  4. Commitar e abrir PR")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main() -> None:
    comp = sys.argv[1] if len(sys.argv) > 1 else _competencia_padrao()
    if not (comp.isdigit() and len(comp) == 6):
        raise SystemExit(f"Competência inválida: {comp!r} — use formato YYYYMM")

    print(SEP)
    print("  DIAGNÓSTICO ESTBAN — DadoSabedoria")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"  Competência alvo: {comp}")
    print(SEP)

    resultado = sondar_urls(comp)
    if resultado is None:
        _sep("RESULTADO FINAL")
        print("  ❌ Nenhuma URL BCB retornou ZIP válido para ESTBAN.")
        print()
        print("  O que fazer:")
        print(
            "  a) Abra https://www.bcb.gov.br/estabilidadefinanceira/estatisticabancariamunicipios"
        )
        print("     no browser, clique em 'Download' e inspecione a aba Rede (DevTools).")
        print("     Copie a URL do ZIP e atualize FetcherEstbanHTTP.BASE no adaptador.")
        print()
        print("  b) Se o download exigir cookie/sessão Angular, considere Playwright headless:")
        print("     playwright install chromium && python scripts/diagnostico_estban_playwright.py")
        print()
        print("  c) Registrar na Lista de desbloqueio do roadmap e aguardar abertura da URL.")
        sys.exit(1)

    desc, url_ok, dados_zip = resultado

    extracao = extrair_zip(dados_zip)
    if extracao is None:
        sys.exit(1)

    csv_bytes, nome_csv = extracao
    df = analisar_forma(csv_bytes, nome_csv)

    # Detectar skip para salvar fixture corretamente
    amostra_txt = csv_bytes[:4096].decode("utf8-lossy", errors="replace")
    linhas = amostra_txt.splitlines()
    skip = 0
    for i, ln in enumerate(linhas[:5]):
        if COL_CODMUN in ln or (ln.count(";") >= 2):
            skip = i
            break
    sep = ";" if b";" in csv_bytes[:512] else ","

    if df is not None:
        salvar_fixture(csv_bytes, skip, sep)

    _sep("RESULTADO FINAL")
    print(f"  ✅ URL ENCONTRADA: {url_ok}")
    print(f"  Descrição: {desc}")
    print()
    print("  Atualize FetcherEstbanHTTP no adaptador:")
    print(f'    BASE = "{url_ok.rsplit("/ESTBAN_MUNICIPIO_", 1)[0]}"')
    print()
    if df is not None:
        print(f"  Shape: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
        tem_codmun = COL_CODMUN in set(df.columns)
        tem_verbete = any(PADRAO_VERBETE in c for c in df.columns)
        print(f"  CODMUN:    {'✅' if tem_codmun else '❌'}")
        print(f"  Verbete160:{'✅' if tem_verbete else '❌'}")
        print(f"  skip_rows: {skip}")


if __name__ == "__main__":
    main()
