# Pendências — decisões de escopo/fonte para o dono analisar

Documento de dúvidas levantadas durante a reparação dos conectores quebrados (validação ao vivo,
ADR-0039). Cada item traz o problema, as opções e uma recomendação. **Nada aqui bloqueia o que já
foi entregue** — são decisões que ampliam ou destravam o conector.

---

## SISVAN — fonte de bulk nacional (entregue com ressalva)

**Estado:** ✅ forma corrigida e mergeada (adaptador consome o JSON real da API de Dados Abertos do
MS, `apidadosabertos.saude.gov.br/sisvan/estado-nutricional`; classificações textuais; cod_ibge 6
díg.; fixture fiel-à-forma; esteira/integração verdes). Ver ADR da reescrita.

**Dúvida:** a API oficial entrega **no máximo ~20 registros por página** (confirmado ao vivo:
`limit=50` e `limit=500` retornam 20). Para agregar `% baixo peso` por município nacionalmente
seria preciso paginar por `offset` sobre **milhões** de registros individuais — inviável como bulk.

**Opções:**
1. **Manter a API JSON** e paginar por competência × município (bom-cidadão, lento). Serve para
   poucos municípios/competências, não para o país inteiro num passe.
2. **Relatório público agregado** `sisaps.saude.gov.br/sisvan/relatoriopublico/estadonutricional`
   (responde 200) — já vem no grão município × estado nutricional, que é exatamente o que
   precisamos. Requer engenharia reversa da API que alimenta o relatório (provável POST com
   parâmetros). **Recomendado** para o bulk nacional.
3. **Microdados restaurados** (o antigo CSV em S3 `ckan.saude.gov.br/SISVAN` hoje dá 403). Se o MS
   republicar o bulk, é o caminho mais simples (um arquivo por ano).

**Recomendação:** adotar a opção 2 (relatório público agregado) para a ingestão nacional; a esteira
atual (opção 1) fica como fallback/validação. Decisão do dono por envolver reverse-engineering de
endpoint não documentado.

**Ressalva secundária:** a fonte é **mensal** (`ano_mes_competencia` YYYYMM), mas o indicador está
modelado como **anual**. Definir se agregamos as 12 competências do ano ou fixamos uma competência
de referência.

---

## ESTBAN — URL de download real (bloqueado)

**Estado:** 🔴 quebrado. A URL hardcoded do fetcher devolve o HTML da SPA Angular do BCB, não o ZIP;
o caminho real do arquivo por competência não foi descoberto (testados ~10 padrões candidatos, todos
404/400/HTML). O adaptador já falha limpo (guarda de magic-bytes `PK`).

**Dúvida:** qual é o endpoint atual de download do ESTBAN (Estatística Bancária Municipal) após a
migração do site do BCB para SPA?

**Pista nova (2026-07-01):** existe um serviço **Olinda** do BCB para o ESTBAN — o endpoint
`https://olinda.bcb.gov.br/olinda/servico/ESTBAN/versao/v1/aplicacao` responde **200** (corpo vazio)
e `.../versao/v1/odata/$metadata` responde **403** (existe, mas exige a coleção certa). Não consegui
adivinhar o nome da coleção OData (`odata/<Colecao>?$format=json` deu 404 para os palpites testados).
O caminho de dados provavelmente é `.../ESTBAN/versao/v1/odata/<NomeDaColecao>` — falta descobrir o
nome exato (via `$metadata` autorizado ou a doc do serviço no portal Olinda do BCB).

**Opções:**
1. **Descobrir a coleção do serviço Olinda ESTBAN** (pista acima) — fonte estruturada moderna do BCB,
   dispensaria baixar/descompactar ZIP. **Recomendado** se o `$metadata` puder ser lido.
2. Rodar `scripts/diagnostico_estban.py` no **VPS de rede aberta** para capturar a URL do ZIP (o
   docstring do adaptador já prevê isso).
3. Inspecionar o tráfego de rede da página
   `bcb.gov.br/estatisticas/estatisticabancariamunicipios` (aba Network) para achar a chamada real.
4. Fonte-espelho: Base dos Dados publica o ESTBAN tratado
   (`basedosdados.org/dataset/.../estban`) — alternativa se o BCB seguir opaco.

**Recomendação:** opção 1 (Olinda) e/ou 2/3 para manter a fonte primária (BCB). Sem a URL/coleção
real confirmada não há como corrigir o fetcher com confiança — daí ficar como pendência e não como PR
(shipar URL adivinhada quebraria a doutrina de proveniência).

**Sonda 2026-07-04 (sessão nova, rede aberta — atualiza a pista de 2026-07-01):**
- `.../ESTBAN/versao/v1/aplicacao` segue **200 (corpo vazio)**; `.../odata/$metadata` agora responde
  **404** (antes 403) — o serviço existe mas não expõe metadados nem catálogo (`odata/` e
  `odata?$format=json` = 404). Palpites de coleção testados e reprovados (404):
  `EstatisticasBancariasPorMunicipio`, `EstatisticaBancariaMunicipios`, `estbans`, `ESTBANs`,
  `Valores`, `getEstban`. `.../documentacao` responde 200 **vazio**.
- **Opção 3 parcialmente executada por fora do browser:** baixados o HTML da SPA
  (`/estatisticas/estatisticabancariamunicipios`), o `main-*.js` e os **51 chunks** lazy do Angular —
  **nenhum contém a string `estban`** nem a URL de download; a página monta o link via chamada de
  conteúdo dinâmica (a API `www.bcb.gov.br/api/...` recusa os caminhos óbvios com "Requisição
  Inválida"). Chromium headless não atravessa o proxy do contêiner (ERR_CONNECTION_RESET), então a
  captura de tráfego autêntica (aba Network) segue exigindo **VPS/máquina do dono**.
- **Conclusão:** as opções 2/3 na VPS (ou a fonte-espelho Base dos Dados, opção 4) são o caminho;
  esgotar palpites de OData daqui tem retorno decrescente.

---

## ANEEL (DEC/FEC) — ponte conjunto→município (bloqueado por dado externo)

**Estado:** 🔴 quebrado. O dado real (CKAN `dadosabertos.aneel.gov.br`, pacote
`indicadores-coletivos-de-continuidade-dec-e-fec`) vem em **formato longo** (`SigIndicador` = DEC/FEC
como valor de linha) e é chaveado por **conjunto de unidades consumidoras** (`IdeConjUndConsumidoras`),
**não** por código IBGE de município.

**Dúvida:** como mapear conjunto de unidades consumidoras → município (código IBGE) para atender ao
grão território×período do projeto?

**Opções:**
1. Obter da ANEEL a tabela de correspondência **conjunto → município** (a ANEEL publica o cadastro de
   conjuntos por distribuidora). Um conjunto pode cruzar mais de um município → definir rateio
   (por nº de UCs, área, ou atribuição ao município-sede).
2. Trocar o indicador para o grão **distribuidora/UF** (que o dado suporta direto) — muda a promessa
   do produto (não seria mais municipal).
3. Descartar DEC/FEC municipal e usar outra fonte de qualidade de energia com grão municipal (se
   existir).

**Recomendação:** decisão de produto. Se DEC/FEC municipal é requisito, opção 1 (com regra de rateio
explícita e documentada). O parser precisa ser reescrito para formato-longo + pivot DEC/FEC de
qualquer forma — mas só vale codar depois de definida a ponte.

---

## ANA (Monitor de Secas) — ausência de grão municipal (bloqueado por natureza da fonte)

**Estado:** 🔴 quebrado. A API real (`apimsbr.ana.gov.br/rpc/v1/dados-tabulares-monitor`) serve JSON
por **UF / Região / País** — **não há grão de município** — e usa a escala de severidade **S0–S4**
(não a escala USDM D0–D4 que o adaptador assume). Não há `cod_ibge`.

**Dúvida:** o Monitor de Secas não oferece o dado no grão município×período que o projeto exige. Como
proceder?

**Opções:**
1. **Rebaixar o grão** do produto de seca para **UF** (o que a fonte suporta) — replicar o valor da
   UF para seus municípios seria honesto só se rotulado como "recorte estadual".
2. Buscar o **shapefile mensal** do Monitor de Secas (mapa poligonal por município) e cruzar
   geograficamente com as malhas municipais do IBGE para derivar a classe por município. É a única
   forma de obter grão municipal real — trabalho de geoprocessamento.
3. **Aposentar** o conector ANA se seca municipal não for prioridade.

**Recomendação:** decisão de produto. Se seca municipal é requisito, opção 2 (geoprocessamento do
shapefile + malhas IBGE); caso contrário, opção 1 rotulada ou opção 3. O adaptador atual (CSV/D0–D4/
município) não corresponde a nenhuma dessas realidades e precisa ser refeito conforme a escolha.
