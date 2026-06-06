# Captura de telas (Playwright) — artefato de CI + smoke visual

O job **`screenshot`** (`.github/workflows/ci.yml`) sobe a stack a cada PR
(Postgres + `app.migrate` semeia → API uvicorn → `next build`/`start`), abre as telas do IVM num
Chromium headless e publica os PNGs como **artefato `telas-ivm`**. É também um **smoke visual**: se uma
tela não responde 2xx, o job falha — mas ainda publica o que capturou (para você ver o estado quebrado).

## Como ver as telas (você e o time de design)

PR → aba **Checks** → run do CI → seção **Artifacts** → baixe **`telas-ivm`**. Conteúdo (estado
semeado; sem geometria de mapa ainda — a coropleta mostra o estado "carregue geometrias"):

- `ivm-mapa.png` — `/ivm`: cartões semafóricos (SP vermelho / Campinas verde) + subíndices
  **Emprego / Finanças / Saúde**.
- `ivm-municipio-sp.png` — `/ivm/3550308`: drill-down (série temporal + subíndices + proveniência).

Use esta linha de base para validar os achados de usabilidade **contra a tela renderizada** (mensagens
de dev vazando, supressão parecendo zero, etc.). Correções de UX e a tela do OndeFoi aparecem nos
artefatos dos PRs seguintes.

## Rodar local (com a stack de pé)

```bash
cd e2e
npm install && npx playwright install chromium
API_URL=http://localhost:8000 WEB_URL=http://localhost:3000 node captura.mjs   # PNGs em e2e/capturas/
```
