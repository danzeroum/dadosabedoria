# Esquema canônico do repositório de indicadores

Documento de design da camada de dados da plataforma de Valor Triplo. Define o
modelo único onde **todos os ~50 produtos** — saúde, emprego, água, transparência —
gravam suas métricas, e onde o IVM e os cruzamentos entre domínios viram simples
consultas. Privacy by Design e LGPD estão embutidos na estrutura, não acoplados depois.

---

## 1. Decisão de arquitetura

**Modelo dimensional (star schema) relacional, semanticamente preparado.** O dado é
sempre `indicador × território × período → valor`: uma tabela-fato (`valor`) cercada de
dimensões (`indicador`, `territorio`, `fonte`) e do tempo. Não usamos ontologia formal
(OWL/RDF) no início — ela serve a inferência e integração de conhecimento heterogêneo,
que não é o nosso problema. Mas adotamos a parte útil da semântica desde já:

- **Códigos namespaced e estáveis** para indicadores (`dominio.subdominio.metrica`),
  funcionando como identificadores duráveis (quase-URIs).
- **Taxonomia hierárquica** de domínio → subdomínio → indicador, que é a arquitetura de
  informação de toda a plataforma (organização, rotulagem, hierarquia, navegação).
- **Crosswalks externos explícitos** (CID-10, CNAE, CBO, NCM, código IBGE) para que os
  joins sejam inequívocos e auditáveis.

Isso mantém a porta aberta para exportar a RDF ou acoplar um grafo (Neo4j, para os
produtos de rede como o Farol de Conluio) no futuro, sem remodelar o núcleo.

Stack: **PostgreSQL + PostGIS**. O território carrega geometria; o resto é relacional puro.

---

## 2. Visão geral do modelo

```
            +-------------+        +-------------+
            |   fonte     |        |  base_legal |
            +-------------+        +-------------+
                  |   \                 /  |
                  |    \               /   |
                  v     v             v    v
+-------------+   +---------------------------+   +-------------+
| territorio  |<--|          valor (fato)     |-->|  indicador  |
| (PostGIS,   |   |  indicador×territorio×    |   | (taxonomia, |
|  hierárq.)  |   |  periodo -> valor         |   |  governança)|
+-------------+   +---------------------------+   +-------------+
                            |
                            v
                     +-------------+
                     |  linhagem   |  (proveniência / auditoria)
                     +-------------+

   schema ISOLADO "app"  (dados pessoais do cidadão, só com consentimento)
   +----------------------+      +--------------------------+
   | app.assinante_alerta |----->| app.condicao_sensivel    |
   +----------------------+      +--------------------------+
```

Princípio central de privacidade: **o repositório analítico nunca contém dado
individual**. O grão é sempre território × período. Qualquer PII (ex.: cidadão que se
inscreve para receber alerta no seu bairro, informando ser asmático) vive num schema
`app` separado, com consentimento — descrito na seção 6.

---

## 3. DDL

### 3.1 Extensões e tipos

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- hashing de contato no schema app

CREATE TYPE periodicidade AS ENUM
  ('diaria','semanal','mensal','trimestral','anual','irregular');

CREATE TYPE nivel_territorial AS ENUM
  ('pais','regiao','uf','mesorregiao','microrregiao',
   'municipio','distrito','bairro','setor_censitario','bacia');

-- Classificação LGPD do dado EFETIVAMENTE ARMAZENADO no indicador.
-- No repositório analítico isso é quase sempre 'nao_pessoal'.
CREATE TYPE classificacao_dado AS ENUM ('nao_pessoal','pessoal','sensivel');

CREATE TYPE polaridade AS ENUM ('maior_melhor','menor_melhor','neutra');
```

### 3.2 `base_legal` — bases legais da LGPD (documentação obrigatória)

```sql
-- Catálogo das hipóteses legais usadas, com a justificativa documentada.
-- Atende à recomendação de identificar e DOCUMENTAR a base legal de cada dado.
CREATE TABLE base_legal (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  codigo       text NOT NULL UNIQUE,            -- 'obrigacao_legal','consentimento'...
  artigo       text NOT NULL,                   -- 'LGPD Art. 7, II' / 'Art. 11, I'
  hipotese     text NOT NULL,                   -- nome da hipótese
  justificativa text NOT NULL                   -- por que se aplica a este uso
);
```

### 3.3 `fonte` — registro de fontes (licença + lag + base legal)

```sql
CREATE TABLE fonte (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  codigo        text NOT NULL UNIQUE,           -- 'datasus_sih','novo_caged'
  nome          text NOT NULL,
  orgao         text NOT NULL,
  url_doc       text,
  licenca       text NOT NULL,                  -- 'LAI/Dados Abertos','CC BY-NC-ND 4.0','ODbL'
  permite_uso_comercial   boolean NOT NULL DEFAULT true,   -- false p/ Comex Stat
  permite_redistribuicao  boolean NOT NULL DEFAULT true,   -- atenção: ODbL share-alike
  atualizacao   periodicidade NOT NULL,
  lag_tipico_dias smallint,                     -- transparência: defasagem típica
  base_legal_id bigint NOT NULL REFERENCES base_legal(id),
  observacoes   text
);
```

### 3.4 `territorio` — dimensão geográfica hierárquica (a chave de junção)

```sql
CREATE TABLE territorio (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  codigo_ibge text NOT NULL UNIQUE,             -- ex.: '3550308' (São Paulo) — o join universal
  nome        text NOT NULL,
  nivel       nivel_territorial NOT NULL,
  pai_id      bigint REFERENCES territorio(id), -- hierarquia (município -> UF -> região...)
  uf          char(2),
  populacao   integer,                          -- para normalização e contexto de k-anon
  geom        geometry(MultiPolygon, 4674)      -- SIRGAS 2000 (malhas IBGE)
);
CREATE INDEX idx_territorio_geom ON territorio USING gist (geom);
CREATE INDEX idx_territorio_nivel ON territorio (nivel);
```

### 3.5 `indicador` — dimensão + taxonomia (IA) + governança (PbD/LGPD)

```sql
CREATE TABLE indicador (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  codigo        text NOT NULL UNIQUE,           -- 'saude.resp.internacoes_j' (namespaced, estável)
  nome          text NOT NULL,                  -- rótulo em LINGUAGEM COMUM (IA / Nielsen)
  descricao     text NOT NULL,
  dominio       text NOT NULL,                  -- topo da taxonomia (IA): 'saude','trabalho'...
  subdominio    text NOT NULL,                  -- 'respiratorio','emprego_formal'...
  unidade       text NOT NULL,                  -- 'contagem','taxa_100k_hab','indice_0_100','reais'
  polaridade    polaridade NOT NULL DEFAULT 'neutra',
  atualizacao   periodicidade NOT NULL,

  -- ----- Privacy by Design embutido -----
  nivel_minimo_agregacao nivel_territorial NOT NULL,  -- nunca expor mais fino que isto
  n_minimo      integer NOT NULL DEFAULT 0,     -- limiar k-anonimato: célula com n < k é suprimida
  classificacao classificacao_dado NOT NULL DEFAULT 'nao_pessoal',
  origem_sensivel boolean NOT NULL DEFAULT false,    -- derivado de microdado sensível (saúde, violência)
  publico       boolean NOT NULL DEFAULT true,  -- Privacy by Default: indicador agregado é público

  -- ----- Transparência / proveniência -----
  base_legal_id bigint NOT NULL REFERENCES base_legal(id),
  fonte_id      bigint NOT NULL REFERENCES fonte(id),
  codigo_externo text,                          -- crosswalk: 'CID-10:J00-J99','CNAE','CBO'
  metodologia   text NOT NULL,                  -- como o número é calculado (transparência)
  versao_metodologia text NOT NULL DEFAULT 'v1'
);
CREATE INDEX idx_indicador_dominio ON indicador (dominio, subdominio);
```

### 3.6 `valor` — a tabela-fato

```sql
CREATE TABLE valor (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  indicador_id  bigint NOT NULL REFERENCES indicador(id),
  territorio_id bigint NOT NULL REFERENCES territorio(id),
  periodo       date    NOT NULL,               -- início do período de referência
  atualizacao   periodicidade NOT NULL,
  valor         numeric,                         -- NULL quando suprimido

  -- ----- Privacy by Design -----
  n_amostra     integer,                         -- contagem subjacente (checagem de k-anon)
  suprimido     boolean NOT NULL DEFAULT false,  -- célula suprimida por proteção
  motivo_supressao text,                         -- visível ao usuário ('n < limiar de privacidade')

  -- ----- Qualidade / transparência -----
  confiabilidade smallint CHECK (confiabilidade BETWEEN 1 AND 5),
  ic_inferior   numeric,
  ic_superior   numeric,
  fonte_id      bigint NOT NULL REFERENCES fonte(id),
  versao        smallint NOT NULL DEFAULT 1,
  carregado_em  timestamptz NOT NULL DEFAULT now(),

  UNIQUE (indicador_id, territorio_id, periodo, versao)
);
CREATE INDEX idx_valor_busca ON valor (indicador_id, territorio_id, periodo);
CREATE INDEX idx_valor_territorio_periodo ON valor (territorio_id, periodo);

-- View pública (Privacy by Default + open-core): só agregado, não suprimido, e marcado público.
CREATE VIEW valor_publico AS
SELECT v.indicador_id, v.territorio_id, v.periodo, v.valor,
       v.confiabilidade, v.suprimido, v.motivo_supressao
FROM   valor v
JOIN   indicador i ON i.id = v.indicador_id
WHERE  i.publico = true
  AND  v.suprimido = false;
```

### 3.7 `linhagem` — proveniência e auditoria (transparência + segurança)

```sql
CREATE TABLE linhagem (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  fonte_id      bigint NOT NULL REFERENCES fonte(id),
  indicador_id  bigint REFERENCES indicador(id),
  executado_em  timestamptz NOT NULL DEFAULT now(),
  url_extracao  text,
  hash_origem   text,                            -- hash do arquivo/resposta bruta
  transformacoes text,                           -- descrição do que a pipeline fez (bronze->prata->ouro)
  registros_carregados integer,
  responsavel   text
);
```

---

## 4. Exemplos: saúde e emprego no mesmo modelo

O ponto-chave: **os dois indicadores são linhas da mesma tabela `valor`, ligadas pelo
mesmo `território` e `período`.** É isso que torna o cruzamento (ex.: choque de emprego
hoje → demanda de saúde meses depois, no `Pulso Econômico-Sanitário`) uma consulta trivial.

### 4.1 Seeds de governança

```sql
INSERT INTO base_legal (codigo, artigo, hipotese, justificativa) VALUES
('obrigacao_legal','LGPD Art. 7, II','Cumprimento de obrigação legal',
 'Dados estatísticos públicos coletados por órgão governamental no exercício de política pública; reuso de dado já público e anonimizado.'),
('consentimento','LGPD Art. 7, I','Consentimento do titular',
 'Cidadão que opta por receber alertas fornece contato e localização para finalidade específica e informada.'),
('consentimento_sensivel','LGPD Art. 11, I','Consentimento específico e destacado',
 'Condição de saúde informada pelo cidadão (ex.: asmático) para personalizar alertas; dado sensível, consentimento explícito e em destaque.');

INSERT INTO fonte (codigo, nome, orgao, url_doc, licenca, permite_uso_comercial,
                   permite_redistribuicao, atualizacao, lag_tipico_dias, base_legal_id)
SELECT 'novo_caged','Novo CAGED','MTE/PDET','https://pdet.mte.gov.br',
       'LAI/Dados Abertos', true, true, 'mensal', 40, id
FROM base_legal WHERE codigo='obrigacao_legal';

INSERT INTO fonte (codigo, nome, orgao, url_doc, licenca, permite_uso_comercial,
                   permite_redistribuicao, atualizacao, lag_tipico_dias, base_legal_id)
SELECT 'datasus_sih','SIH/SUS','Ministério da Saúde/DATASUS','https://datasus.saude.gov.br',
       'LAI/Dados Abertos (anonimizado)', true, true, 'mensal', 90, id
FROM base_legal WHERE codigo='obrigacao_legal';

INSERT INTO territorio (codigo_ibge, nome, nivel, uf, populacao)
VALUES ('3550308','São Paulo','municipio','SP', 11451245);
```

### 4.2 Indicadores — emprego e saúde, lado a lado

```sql
-- EMPREGO: saldo do CAGED (admissões - desligamentos). Não-pessoal, sem sensibilidade.
INSERT INTO indicador (codigo, nome, descricao, dominio, subdominio, unidade, polaridade,
       atualizacao, nivel_minimo_agregacao, n_minimo, classificacao, origem_sensivel,
       publico, base_legal_id, fonte_id, codigo_externo, metodologia)
SELECT 'trabalho.emprego.saldo_caged',
       'Saldo de empregos formais',
       'Admissões menos desligamentos com carteira no mês.',
       'trabalho','emprego_formal','contagem','maior_melhor','mensal',
       'municipio', 0, 'nao_pessoal', false, true,
       bl.id, f.id, 'CNAE',
       'Soma de admissões menos desligamentos do Novo CAGED por município/mês.'
FROM base_legal bl, fonte f
WHERE bl.codigo='obrigacao_legal' AND f.codigo='novo_caged';

-- SAÚDE: internações por doença respiratória (CID J). Valor armazenado é NÃO-PESSOAL
-- (agregado), MAS deriva de microdado sensível -> origem_sensivel=true, k-anon mais rígido.
INSERT INTO indicador (codigo, nome, descricao, dominio, subdominio, unidade, polaridade,
       atualizacao, nivel_minimo_agregacao, n_minimo, classificacao, origem_sensivel,
       publico, base_legal_id, fonte_id, codigo_externo, metodologia)
SELECT 'saude.resp.internacoes_j',
       'Internações por doenças respiratórias',
       'Internações no SUS com CID-10 do grupo J (doenças respiratórias) por mês.',
       'saude','respiratorio','contagem','menor_melhor','mensal',
       'municipio', 5, 'nao_pessoal', true, true,   -- n_minimo=5: célula com <5 casos é suprimida
       bl.id, f.id, 'CID-10:J00-J99',
       'Contagem de AIH com diagnóstico principal no grupo J do SIH/SUS por município/mês.'
FROM base_legal bl, fonte f
WHERE bl.codigo='obrigacao_legal' AND f.codigo='datasus_sih';
```

### 4.3 Valores (fato) — três meses

```sql
-- Saldo de emprego (sinal precoce)
INSERT INTO valor (indicador_id, territorio_id, periodo, atualizacao, valor, confiabilidade, fonte_id)
SELECT i.id, t.id, p.periodo, 'mensal', p.v, 5, i.fonte_id
FROM indicador i, territorio t,
     (VALUES (DATE '2026-02-01', 8200),
             (DATE '2026-03-01', -15400),   -- choque negativo de emprego
             (DATE '2026-04-01', -9100)) AS p(periodo, v)
WHERE i.codigo='trabalho.emprego.saldo_caged' AND t.codigo_ibge='3550308';

-- Internações respiratórias (consequência, com defasagem)
INSERT INTO valor (indicador_id, territorio_id, periodo, atualizacao, valor, n_amostra, confiabilidade, fonte_id)
SELECT i.id, t.id, p.periodo, 'mensal', p.v, p.v, 4, i.fonte_id
FROM indicador i, territorio t,
     (VALUES (DATE '2026-04-01', 310),
             (DATE '2026-05-01', 420),
             (DATE '2026-06-01', 660)) AS p(periodo, v)   -- sobe ~2 meses após o choque
WHERE i.codigo='saude.resp.internacoes_j' AND t.codigo_ibge='3550308';
```

### 4.4 O cruzamento entre domínios em UMA consulta

```sql
-- Choque de emprego no mês T x internações respiratórias em T+2, mesmo município.
-- Esta é a "sabedoria" do Pulso Econômico-Sanitário, possível porque emprego e saúde
-- são linhas da MESMA tabela, unidas por território + período.
SELECT  ter.nome,
        emp.periodo                AS mes_emprego,
        emp.valor                  AS saldo_emprego,
        sau.periodo                AS mes_saude,
        sau.valor                  AS internacoes_resp
FROM        valor emp
JOIN        indicador i_emp ON i_emp.id = emp.indicador_id
                           AND i_emp.codigo = 'trabalho.emprego.saldo_caged'
JOIN        valor sau ON sau.territorio_id = emp.territorio_id
JOIN        indicador i_sau ON i_sau.id = sau.indicador_id
                           AND i_sau.codigo = 'saude.resp.internacoes_j'
JOIN        territorio ter ON ter.id = emp.territorio_id
WHERE       sau.periodo = (emp.periodo + INTERVAL '2 months')
  AND       emp.suprimido = false AND sau.suprimido = false
ORDER BY    emp.periodo;
```

Para somar ao IVM, o mesmo `valor` é a base de um índice composto: cada subíndice é uma
agregação de indicadores de um domínio, normalizada e ponderada — sem nenhuma tabela nova.

---

## 5. Privacy by Design — os 7 princípios mapeados ao esquema

| Princípio | Como o esquema o realiza |
|---|---|
| 1. Proativo e preventivo | `n_minimo` (k-anonimato) e `nivel_minimo_agregacao` são checados na ingestão; a célula é suprimida *antes* de ser gravada, não depois de exposta. |
| 2. Privacy by Default | `valor_publico` só mostra indicador `publico=true`, não suprimido; o padrão é o agregado. Nada pessoal é gravado por padrão no schema analítico. |
| 3. Privacidade embutida no design | O grão é território × período: **não existe chave de pessoa em lugar nenhum** do repositório. Ele é estruturalmente incapaz de guardar dado individual. |
| 4. Soma positiva | Agregar não reduz utilidade — os indicadores foram concebidos para servir agregados (open-core). Ganha-se privacidade *e* função. |
| 5. Transparência | Todo valor carrega `fonte`, `metodologia`, `versao_metodologia`, `base_legal`, `lag_tipico_dias`, `confiabilidade`; `linhagem` registra extração e transformação. |
| 6. Segurança ponta a ponta | Schemas separados (analítico vs `app`), Row-Level Security, criptografia em repouso/trânsito, `hash` de contato no `app`, trilha em `linhagem`. |
| 7. Centrado no usuário | Rótulos em linguagem comum (`indicador.nome`), `motivo_supressao` visível ("dado protegido"), metadados legíveis; o cidadão entende e pode contestar. |

---

## 6. LGPD — bases legais e classificação pessoal × sensível

A separação de armazenamento é a decisão de privacidade mais importante:

**Repositório analítico (tabelas acima).** Contém apenas estatística agregada/anonimizada.
Dado efetivamente anonimizado está, em regra, fora do escopo da LGPD (Art. 12); a base
legal da *coleta original* (pelo governo) é obrigação legal / execução de política pública,
e o nosso uso é de dado já público. O único risco é reidentificação em células pequenas —
mitigado por `n_minimo`/supressão. Indicadores de **origem sensível** (saúde, violência)
recebem `origem_sensivel=true`, `n_minimo` mais alto e `nivel_minimo_agregacao` mais grosso,
e podem ter `publico=false` mesmo agregados.

**Schema `app` (isolado).** Só aqui existe dado pessoal — quando o cidadão *opta* por um
alerta. É fisicamente separado, com consentimento por finalidade:

```sql
CREATE SCHEMA app;

-- Dado PESSOAL: base legal = consentimento (Art. 7, I). Contato pseudonimizado.
CREATE TABLE app.assinante_alerta (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  contato_hash    text NOT NULL,                 -- hash do e-mail/telefone (pgcrypto)
  territorio_id   bigint NOT NULL REFERENCES territorio(id),
  finalidade      text NOT NULL,                 -- 'alerta_qualidade_ar'
  base_legal_id   bigint NOT NULL REFERENCES base_legal(id),  -- 'consentimento'
  consentido_em   timestamptz NOT NULL,
  revogado_em     timestamptz                    -- revogação a qualquer tempo (Art. 8, §5)
);

-- Dado SENSÍVEL (saúde): base legal = consentimento específico e destacado (Art. 11, I).
CREATE TABLE app.condicao_sensivel (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assinante_id    bigint NOT NULL REFERENCES app.assinante_alerta(id) ON DELETE CASCADE,
  tipo            text NOT NULL,                  -- 'asma','idoso_em_casa'
  base_legal_id   bigint NOT NULL REFERENCES base_legal(id),  -- 'consentimento_sensivel'
  consentido_em   timestamptz NOT NULL
);
```

Classificação resumida:

| Dado | Classificação | Base legal | Proteção |
|---|---|---|---|
| Indicadores agregados (emprego, água, transparência) | Não-pessoal | Obrigação legal (coleta) / reuso público | k-anon, supressão |
| Indicadores de saúde/violência (agregados) | Não-pessoal, **origem sensível** | Obrigação legal | k-anon rígido, agregação mais grossa, `publico` restringível |
| Assinatura de alerta (contato + localização) | **Pessoal** | Consentimento (Art. 7, I) | hash, isolamento, revogável |
| Condição de saúde do assinante (asmático) | **Sensível** | Consentimento específico e destacado (Art. 11, I) | criptografia, isolamento, finalidade única |
| Camada B2B (API profunda) | Não-pessoal | — | contrato veda reidentificação e usos antissociais (teste da dupla face) |

---

## 7. Arquitetura de informação (a taxonomia é a navegação)

`indicador.dominio → subdominio → codigo` não é só organização de banco: é a **hierarquia,
a rotulagem e a navegação** de toda a plataforma. Os 10 domínios do Capítulo 12 são o
primeiro nível; o subdomínio é o segundo; o indicador é a folha. Isso dá, de graça:

- **Organização**: cada produto/dashboard é um recorte por `dominio`/`subdominio`.
- **Navegação**: domínio → subdomínio → indicador → (território, período) é o caminho de
  drill-down dos painéis, e o IVM é a vista de topo que agrega os domínios.
- **Rotulagem**: `indicador.nome` em linguagem comum garante o "match between system and
  the real world" (Nielsen) — o cidadão lê "Internações por doenças respiratórias", não
  "SIH CID J".
- **Hierarquia/consistência**: o mesmo vocabulário controlado vale para URL, menu, busca e
  legenda dos mapas, evitando rótulos divergentes entre telas.

---

## 8. Notas para a fase de dashboards (UCD, protótipo, heurística)

O esquema é o entregável da etapa **"definir"** do design centrado no usuário. As próximas
etapas — empatizar, idear, prototipar, testar — acontecem sobre os painéis, não sobre o
banco. Recomendações para quando chegarmos lá:

- **Empatizar/idear**: comece pelas três personas do valor triplo (cidadão, gestor/empresa,
  ONG) e rode *Crazy 8s* para a tela do IVM e para um painel de domínio (ex.: ar/saúde),
  antes de qualquer código.
- **Prototipar (co-criação)**: protótipos de baixa fidelidade (papel/Figma) do mapa
  semafórico e do drill-down, testados com usuários reais de cada persona — protótipo como
  ferramenta de descoberta, não só de validação.
- **Heurística de Nielsen**, já apoiada pelo esquema: *visibilidade do estado do sistema*
  (mostrar `lag_tipico_dias` e data de carga), *prevenção de erro* (`suprimido` +
  `motivo_supressao` evitam interpretar célula vazia como zero), *ajuda e documentação*
  (`metodologia` acessível em cada indicador), *consistência* (vocabulário controlado).
  As demais — aprendizado, eficiência, retenção, satisfação — serão avaliadas na revisão de
  cada interface, com teste de usabilidade por persona.

---

### Próximos passos sugeridos
1. Popular a `base_legal`, a `fonte` e a taxonomia de `indicador` para os produtos da Onda 1
   (emprego + crédito + IVM), que usam só CAGED/BCB/IBGE.
2. Escrever a regra de supressão por k-anonimato como uma checagem única na camada de
   ingestão (prata → ouro), aplicada a todo indicador com `n_minimo > 0`.
3. Definir as personas e rodar os Crazy 8s do IVM antes de codar o primeiro painel.
