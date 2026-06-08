# Runbook do destrave — tornar os conectores VIVOS em minutos

Companheiro de execução do `docs/PENDENCIAS_DO_DONO.md` §1 (#0 — allowlist). Os conectores já estão
**vivo-prontos** (esteira `adapter→bronze→prata→ouro` + schedule Dagster + fixture fiel + fetcher real,
exercidos no CI por fetcher *fake*). Falta **a 1ª busca real**, que só roda com o host no allowlist.
SICONFI e IBGE já foram validados assim (ADR-0028); este runbook repete o mesmo padrão para os demais.

> **Tempo:** ~2–5 min por conector depois que o host está liberado. **Quem faz o flip do allowlist:**
> você (dono do ambiente). **Quem valida e grava o ADR:** o dev (é só dizer "valide o conector X").

---

## 0. Pré-requisitos (uma vez)

1. **Allowlist (editor do ambiente, claude.ai/code → Network):** modo **Custom**, marque **"include
   default list of common package managers"**, adicione os hosts da tabela §2, e **Salve**.
2. **⚠️ Abra uma SESSÃO NOVA depois de salvar.** O egress Custom **só vale em sessão nova** — uma
   sessão *resumida* herda a política antiga e dá **falso negativo** (parece 403 mesmo liberado).
3. **Stack de pé** (contêiner novo; detalhe no `README.md` §Como testar):
   ```bash
   sudo pg_ctlcluster 16 main start && redis-server --daemonize yes
   cd api && uv pip install -e ".[dev]"        # se o venv estiver velho
   export ADMIN_DATABASE_URL=… DATABASE_URL=… CONSENT_DATABASE_URL=… REDIS_URL=…
   python -m app.migrate                        # cria schema + semeia dimensões (fonte/indicador)
   ```
   A 1ª busca real **acrescenta** fatos reais em `valor`/`execucao_funcao` pelo caminho ouro (supressão
   + linhagem) — não há INSERT cru.

## 1. Sonda (confirme que o host abriu — só confiável em sessão nova)

```bash
for h in apidatalake.tesouro.gov.br servicodados.ibge.gov.br download.inep.gov.br \
         pncp.gov.br ftp.datasus.gov.br ftp.mtps.gov.br www.bcb.gov.br dadosabertos.bcb.gov.br; do
  echo "== $h =="; curl -sS -D - -o /dev/null --max-time 15 "https://$h/" | grep -iE "^HTTP/|x-deny-reason"
done
```
`HTTP/…` **sem** `x-deny-reason` → **aberto**. `x-deny-reason: host_not_allowed` → ainda **bloqueado**
(o flip não pegou: confira Custom + "include default list" + **salvo** + sessão **nova**).

## 2. Por conector — host, comando, e o que confirmar na 1ª busca

| Conector | Host(s) a liberar | Comando (após `cd api`) | Forma a confirmar (vs. fixture/`ContratoFonte`) | Alimenta |
|---|---|---|---|---|
| **SICONFI** | `apidatalake.tesouro.gov.br` ✅ | `python -m app.ingestao.run_siconfi <ano>` | **✅ validado (ADR-0028)** | `financas.transferencias.correntes` |
| **SICONFI/funções** | (mesmo host) ✅ | `python -m app.ingestao.run_siconfi_funcoes <ano>` | Anexo I-E (despesa por função): filtro `cod_conta`+`coluna`; Empenhado/Liquidado | `execucao_funcao` (OndeFoi) |
| **IBGE** | `servicodados.ibge.gov.br` ✅ | `python -m app.ingestao.run_ibge <UF>` | **✅ validado** (`localidades/municipios` + `v3/malhas`) | territórios/malhas |
| **INEP** | `download.inep.gov.br` | `python -m app.ingestao.run_inep <ano>` | microdado de escolas traz `CO_MUNICIPIO` + `QT_MAT_FUND`; censo **anual** (nome/URL do CSV) | `educacao.matriculas.fundamental` |
| **PNCP** | `pncp.gov.br` | `python -m app.ingestao.run_pncp <ano>` | lista `data` paginada; item com `valorGlobal` + `unidadeOrgao.codigoIbge` (7 díg.) | `compras.contratos.valor_total` |
| **DATASUS/SIH** | `ftp.datasus.gov.br` | `python -m app.ingestao.run_datasus <ano> <mes>` | RD do SIH traz `MUNIC_RES` + `DIAG_PRINC`; IBGE **6 díg.** (mapa 6→7 no pipeline); k-anon suprime <5 | `saude.resp.internacoes_j` |
| **CAGED** | `ftp.mtps.gov.br` | `python -m app.ingestao.run_caged <ano> <mes>` | layout do Novo CAGED (FTP do PDET/MTPS): saldo = admissões − desligamentos por município | `trabalho.emprego.saldo_caged` |
| **ESTBAN** ⚠️ | `www.bcb.gov.br` **ou** `dadosabertos.bcb.gov.br` | `python -m app.ingestao.run_estban <ano> <mes>` | `CODMUN` IBGE 7 díg.; valor em **R$ mil** (×1000). **Portal migrou** — o fetcher aponta p/ `www4` (404): o dev ajusta a URL na 1ª busca | `credito.operacoes.saldo_total` |

> **Exemplos de argumentos:** anuais → o último ano fechado (ex.: `run_inep 2024`, `run_pncp 2024`,
> `run_siconfi 2024`). Mensais → ano+mês (ex.: `run_caged 2026 4`, `run_estban 2026 2`,
> `run_datasus 2026 4`). IBGE → a UF (ex.: `run_ibge SP`).

## 3. Fechar o loop (o padrão do ADR-0028, por conector)

1. **Rodar uma vez** o comando da §2. Erro `403/host_not_allowed` → volte à §0/§1 (host/sessão).
2. **Confirmar a forma:** as colunas/campos reais batem com as **ASSUNÇÕES** do adaptador
   (`api/app/ingestao/adaptadores/<fonte>.py`, cabeçalho) e com a **fixture**
   (`api/tests/fixtures/<fonte>.*`)?
   - **Batem** → a fixture é **fiel-à-forma**: nada de código muda.
   - **Não batem** → ajuste o `ContratoFonte`/fixture (forma real manda), rode o teste do pipeline.
3. **Gravar o ADR** "forma real do `<fonte>` (validação #0)" — como o **ADR-0028** fez para o SICONFI:
   campos confirmados, vocabulário promovido da fonte, e a fixture marcada fiel-à-forma.
4. **Promover na doc:** marque o item em `docs/PENDENCIAS_DO_DONO.md` §1 e na *Lista de desbloqueio*
   do `roadmap.md`; o conector passa de "vivo-pronto" a **VIVO**.
5. **Produto à tela:** com dado real fluindo, o produto daquela fonte sai do grau-demo (ex.: EDU-01
   sobre `educacao.matriculas`, OndeFoi sobre `execucao_funcao`).

## 4. Atalho — validar tudo que estiver aberto, de uma vez

Depois do flip + sessão nova, rode a sonda (§1); para cada host **aberto**, dispare o comando
correspondente (§2). Ou peça ao dev: **"valide os conectores abertos"** — ele roda a sonda, exercita
cada fetcher aberto uma vez, confirma a forma, grava o ADR e promove a fixture, conector por conector.

---

**Ordem de impacto** (qual destrava mais produto): **INEP** (EDU-01) · **DATASUS** (SAÚDE) · **PNCP**
(TRANSP/compras) · **CAGED**/**ESTBAN** (já no IVM/Pulso por seed — viram reais) · **SICONFI/funções**
(OndeFoi go-live, junto do referendo do item B em PENDENCIAS). Veja `CLAUDE.md` (topo) e
`docs/PENDENCIAS_DO_DONO.md` para o contexto completo.
