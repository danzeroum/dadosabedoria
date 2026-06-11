#!/usr/bin/env python3
"""Descobre a URL de download do ESTBAN via Playwright (headless Chromium).

O portal BCB usa SPA Angular — o arquivo ZIP é entregue por uma requisição
de rede disparada pelo JavaScript do browser. Este script:
  1. Navega até a página ESTBAN do BCB
  2. Intercepta todas as requisições de rede
  3. Clica no link de download mais recente
  4. Captura a URL do ZIP

Uso:
  pip install playwright && playwright install chromium --with-deps
  python scripts/descobrir_url_estban.py

Saída: imprime a URL do ZIP e como atualizar FetcherEstbanHTTP.
"""

from __future__ import annotations

import sys
import time
from urllib.parse import urlparse

URL_PAGINA = "https://www.bcb.gov.br/estabilidadefinanceira/estatisticabancariamunicipios"
TIMEOUT_MS = 30_000  # 30s para a página carregar


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERRO: playwright não instalado.")
        print("Instale com: pip install playwright && playwright install chromium --with-deps")
        sys.exit(1)

    urls_capturadas: list[str] = []

    print(f"Abrindo: {URL_PAGINA}")
    print("Aguardando carregamento da SPA Angular...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # Intercepta requisições que parecem ZIPs ou downloads
        def on_request(req: object) -> None:
            url = req.url  # type: ignore[union-attr]
            if any(x in url.upper() for x in (".ZIP", "ESTBAN", "DOWNLOAD", "ARQUIVO")):
                print(f"  [REDE] {req.method} {url}")  # type: ignore[union-attr]
                urls_capturadas.append(url)

        page.on("request", on_request)

        # Também captura via download event
        download_urls: list[str] = []

        def on_download(dl: object) -> None:
            url = dl.url  # type: ignore[union-attr]
            print(f"  [DOWNLOAD] {url}")
            download_urls.append(url)

        page.on("download", on_download)

        page.goto(URL_PAGINA, timeout=TIMEOUT_MS, wait_until="networkidle")
        print("  Página carregada.")
        time.sleep(2)

        # Encontrar links de download (ESTBAN municipal = por município)
        links = page.locator("a").all()
        print(f"  Total de links na página: {len(links)}")

        candidatos = []
        for link in links:
            try:
                txt = link.inner_text(timeout=500).strip().lower()
                href = link.get_attribute("href") or ""
                if any(
                    x in txt for x in ("municip", "estban", "download", "zip", "arquivo")
                ) or any(x in href.upper() for x in (".ZIP", "ESTBAN", "MUNICIP")):
                    candidatos.append((txt, href, link))
            except Exception:  # noqa: S112,BLE001  # stale Playwright element
                continue

        print(f"  Links candidatos encontrados: {len(candidatos)}")
        for txt, href, _ in candidatos[:10]:
            print(f"    texto={txt!r:.50}  href={href!r:.80}")

        # Clicar no mais promissor (por município)
        for txt, href, link in candidatos:
            if "municip" in txt or "MUNICIP" in href.upper():
                print(f"\n  Clicando: {txt!r}")
                try:
                    with page.expect_download(timeout=15_000) as dl_info:
                        link.click(timeout=5_000)
                    dl = dl_info.value
                    print(f"  Download disparado: {dl.url}")
                    download_urls.append(dl.url)
                except Exception as exc:
                    print(f"  Clique sem evento de download: {exc}")
                break

        # Aguardar mais requisições de rede
        time.sleep(3)
        browser.close()

    # Resultado
    todas = list(dict.fromkeys(urls_capturadas + download_urls))
    zips = [u for u in todas if ".ZIP" in u.upper() or "ESTBAN" in u.upper()]

    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)

    if not zips:
        print("Nenhuma URL de ZIP capturada.")
        print()
        print("Todas as URLs de rede capturadas:")
        for u in todas[:20]:
            print(f"  {u}")
        print()
        print("Próximo passo: abrir a página no browser, clicar em")
        print("'Por Município', inspecionar aba Rede (DevTools) e")
        print("copiar a URL do ZIP manualmente.")
        sys.exit(1)

    print("URLs capturadas relacionadas ao ESTBAN:")
    for u in zips:
        print(f"  {u}")
        parsed = urlparse(u)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}"
        print("\nAtualize FetcherEstbanHTTP:")
        print(f'  BASE = "{base}"')

    print()
    print("Cole a URL acima na config e rode o diagnóstico novamente:")
    print("  docker compose --profile ingestion run --rm worker \\")
    print("    python scripts/diagnostico_estban.py")


if __name__ == "__main__":
    main()
