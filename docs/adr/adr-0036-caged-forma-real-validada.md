# ADR-0036 — CAGED: Forma Real Validada (CAGEDMOV 202604)

**Status:** Aceito  
**Data:** 2026-06-11  
**Contexto:** CAGED Fase 1 — fixture real CAGEDMOV 202604 commitada  

---

## Contexto

O adaptador CAGED (`app.ingestao.adaptadores.caged`) foi implementado antes da validação contra
dados reais do FTP do PDET (`ftp.mtps.gov.br`). O script `scripts/diagnostico_caged.py` foi
executado no ambiente com rede aberta (VPS / docker-compose com volume montado), baixou o arquivo
`CAGEDMOV202604.7z`, descompactou e gerou a amostra `api/tests/fixtures/caged_amostra_real.csv`
(2.000 linhas, sem cabeçalho — ou seja, shape = 2000 × 28).

O parser foi rodado contra a fixture real e apresentou **zero divergências** — o adaptador já estava
correto antes mesmo da validação empírica.

---

## Forma Confirmada

| Atributo | Valor |
|---|---|
| Encoding | UTF-8 sem BOM (o diagnóstico reportou `utf-8-sig`, mas os bytes iniciais da fixture não contêm BOM — Polars lida corretamente com ambos via `utf8-lossy`) |
| Separador | `;` (ponto-e-vírgula) |
| Terminador de linha | CRLF (Windows) — Polars normaliza transparentemente |
| Colunas | 28 (layout CAGEDMOV completo) |
| Municípios | Código IBGE de **6 dígitos** (sem o dígito verificador) |
| `saldomovimentação` | Inteiro: `+1` = admissão, `-1` = desligamento |
| `salário` | Decimal BR (`XXXX,XX`) — vírgula como separador decimal |
| Competência | `YYYYMM` (6 dígitos, ex.: `202604`) |

### Cabeçalho completo (28 colunas)

```
competênciamov;região;uf;município;seção;subclasse;saldomovimentação;cbo2002ocupação;
categoria;graudeinstrução;idade;horascontratuais;raçacor;sexo;tipoempregador;
tipoestabelecimento;tipomovimentação;tipodedeficiência;indtrabintermitente;indtrabparcial;
salário;tamestabjan;indicadoraprendiz;origemdainformação;competênciadec;
indicadordeforadoprazo;unidadesaláriocódigo;valorsaláriofixo
```

---

## Decisão

O parser é declarado **fiel-à-forma** a partir desta data. A fixture
`api/tests/fixtures/caged_amostra_real.csv` é a evidência empírica e os testes em
`api/tests/unit/test_caged.py` garantem a regressão:

- `test_contrato_fiel_forma_28_colunas` — valida o contrato contra `AMOSTRA_FIEL` (28 colunas)
- `test_municipio_6_digitos_na_fixture_real` — todos os municípios têm len == 6 após prata
- `test_saldo_semantica_adm_demissao` — semântica de saldo: 355030 (+1 -1) = 0, 351905 (+1) = 1
- `test_parse_fixture_real_shape` — shape da fixture real = (2000, 28)

---

## GOTCHAS registrados

### 1. Reconciliação de 6 dígitos no pipeline

O CAGED usa código IBGE de 6 dígitos; o cadastro `territorio` usa o de 7. O pipeline
(`executar_caged`) faz a reconciliação via:

```python
mapa6 = {k[:6]: v for k, v in (await _mapa_municipios(conn)).items()}
```

Nunca truncar na borda bronze ou prata — manter os 6 dígitos como vieram da fonte.

### 2. BOM ausente

O diagnóstico detectou `utf-8-sig` como encoding (porque tentou decodificar os primeiros bytes),
mas a fixture salva não contém BOM. O parser usa `encoding="utf8-lossy"` que lida corretamente
com ambos os casos.

### 3. CRLF

O arquivo original tem terminadores CRLF (Windows). Polars normaliza transparentemente via
`pl.read_csv` e `pl.scan_csv`.

### 4. Modo passivo FTP

Containers com NAT/firewall precisam de FTP passivo. `FetcherCagedFTP.baixar()` chama
`ftp.set_pasv(True)` logo após `ftp.login()`.

---

## Agregação nacional (`agregar_nacional`)

Para evitar dois passes sobre o DataFrame (um para saldo, outro para salário), o método
`agregar_nacional(bruto: bytes)` escreve os bytes em arquivo temporário e usa `pl.scan_csv` +
`collect(engine='streaming')` para agregar saldo e salário médio em **uma única passagem lazy**,
sem carregar todo o arquivo em RAM.

```python
saldos, salarios = adaptador.agregar_nacional(bruto)
```

Retorna `(saldos_df, salarios_df)` com o mesmo contrato de `agregar_saldo` / `agregar_salario_medio`.

---

## Metodologia

- **CAGEDMOV only**: o CAGED tem três arquivos por competência (CAGEDMOV, CAGEDFOR, CAGEDEXC).
  Usamos apenas CAGEDMOV (movimentações brutas). CAGEDFOR (fora do prazo) e CAGEDEXC (exclusões)
  são refinamento futuro.
- **Saldo**: soma de `saldomovimentação` por município (admissões − desligamentos).
- **Salário médio**: média de `salário` filtrada apenas nas **admissões** (`saldo_mov == 1`),
  convertendo o decimal BR para float antes de agregar. Desligamentos não têm salário informado
  na fonte.

---

## Consequências

- A fixture `caged_amostra_real.csv` entra no controle de versão como evidência empírica permanente.
- O CI valida a forma a cada commit (testes de shape, 6 dígitos, semântica de saldo).
- O pipeline está pronto para ingestão real assim que `ftp.mtps.gov.br:21` estiver no allowlist
  da VPS (ver RUNBOOK_DEPLOY.md §CAGED go-live).
