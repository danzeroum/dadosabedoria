# ADR-0040 — SISVAN: migração do CSV/S3 para a API de Dados Abertos do MS

**Status:** Aceito
**Data:** 2026-07-01
**Contexto:** Validação ao vivo (ADR-0039) mostrou o conector SISVAN **quebrado** — o CSV no bucket
S3 (`ckan.saude.gov.br/SISVAN`) responde **403 AccessDenied** e a forma que o adaptador assumia
(colunas `CO_MUNICIPIO_IBGE`/`CO_ESTADO_NUTRI_CRIANCA` numéricas, CSV `;`) não existe mais.

---

## Decisão

Reescrever o adaptador SISVAN (crianças e gestantes) para consumir a **API pública de Dados Abertos
do Ministério da Saúde** — `GET https://apidadosabertos.saude.gov.br/sisvan/estado-nutricional` —
que substituiu o bulk S3.

## Forma real confirmada ao vivo (2026-07-01)

- JSON: `{"estados_nutricionais": [ {...}, ... ]}`.
- `codigo_municipio`: IBGE de **6 dígitos** (sem dígito verificador; ex. `355030`) → pipeline passa a
  reconciliar por `mapa6` (como SIH/CAGED), não `mapa7`.
- `idade`: inteiro (anos completos).
- `crianca_imc_x_idade`: **texto** (não código) — categorias `Magreza acentuada`, `Magreza`,
  `Eutrofia`, `Risco de sobrepeso`, `Sobrepeso`, `Obesidade`, `Obesidade grave`; nulo p/ não-criança.
  **Baixo peso infantil** = `Magreza acentuada` + `Magreza`.
- `codigo_estado_nutricional_imc_gestante`: **texto** apesar do nome "codigo" — `Baixo peso`,
  `Adequado ou eutrófico`, `Sobrepeso`, `Obesidade`; nulo fora de gestante. **Baixo peso gestacional**
  = `Baixo peso`. A presença dessa classificação identifica a gestante (não há mais `CO_PUBLICO_ALVO`).
- `ano_mes_competencia`: `YYYYMM` — chave incremental (invariante 6).

O matching textual é **normalizado** (minúsculas, sem acento) para robustez.

## Consequências

- O contrato de saída da prata/ouro é **preservado** (`cod_ibge` + `baixo_peso_pct`/
  `gestante_baixo_peso_pct` + `n_total`), então os produtos FomeOculta (ALIM-02) e SentinelaMaterna
  (SAUDE-03) seguem funcionando sem mudança — confirmado pelos testes de integração.
- Fixtures promovidas a **fiel-à-forma** (JSON com campos e categorias reais); testes unitários e de
  integração verdes.
- O fetcher real pagina a API por competência (`offset`), mas a API entrega **~20 registros/página**
  → **bulk nacional é decisão em aberto** (relatório público agregado vs. microdados restaurados):
  ver `pendencias.md` (SISVAN). Como todo conector, a ingestão real roda na VPS de rede aberta; no
  CI a esteira é exercida pelo fetcher fake.
