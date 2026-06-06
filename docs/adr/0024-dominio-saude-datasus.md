# ADR-0024 — Domínio `saude` via DATASUS/SIH (1ª fonte de origem sensível; Onda 2B)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
Concluída a sequência de fontes abertas de menor atrito da Onda 2A (SICONFI/INEP/PNCP), a Onda 2B
abre a saúde pelo **DATASUS/SIH** (Sistema de Informações Hospitalares). É a 1ª fonte de **origem
sensível** do acervo e o adaptador de **maior atrito** (FTP + arquivos DBC). O indicador
`saude.resp.internacoes_j` já existia no seed como exemplo sensível (com célula sub-limiar suprimida);
agora ganha seu adaptador e módulo de domínio.

## Decisão
- **`AdaptadorDatasus`** (medallion bronze→prata→ouro): parse do tabular do SIH-RD (uma linha por
  AIH) → Polars; prata filtra o diagnóstico principal do **grupo J** (CID-10 respiratório) e
  normaliza `MUNIC_RES`; ouro **conta** as AIH por município — a contagem é também o `n_amostra` que
  alimenta a supressão. **Contrato na borda bronze** (`ContratoFonte`, ADR-0017): exige `MUNIC_RES` e
  `DIAG_PRINC`. Fetcher real FTP+DBC (`pragma: no cover`, decodificação via PySUS), espelhando o
  padrão do CAGED (download/descompressão fora do teste; parse coberto por fixture).
- **Origem sensível:** nada de tratamento especial no adaptador — a contagem entra pelo **mesmo
  caminho ouro** (`escrever_ouro`), onde o k-anonimato com **piso sensível** suprime células abaixo
  do limiar (invariante 1). O indicador é `menor_melhor`, `n_minimo=5`, `origem_sensivel=true`.
- **`domains/saude`** (`ModuloSaude`): registra o adaptador + o catálogo do indicador existente.
  A API genérica já serve (`/v1/indicadores?dominio=saude`) — zero rota nova (Open/Closed).

## ASSUNÇÕES a confirmar (lacuna sinalizada)
O caminho/nome do RD no FTP (`/dissemin/publicos/SIHSUS/200801_/Dados/RD<UF><AAMM>.dbc`), a
decodificação DBC→tabular (PySUS) e os nomes de coluna (`MUNIC_RES`, `DIAG_PRINC`) são **assunções**
— a confirmar contra o arquivo real. O **IBGE do SIH tem 6 dígitos** (sem dígito verificador); o
mapa 6→7 para casar com `territorio` é responsabilidade do pipeline (não do adaptador).

## Consequências / a evoluir
- 1ª fonte sensível com adaptador no ar; a supressão passa a ser exercida sobre uma fonte externa
  (não só no seed). **Próximos:** pipeline **live** (`run_datasus` + Dagster, incremental por
  competência, mapa 6→7); produtos SAÚDE com a **dupla face** do §17 (SAUDE-01 veda seguradora,
  SAUDE-02 geo ~500 m); demais sistemas DATASUS (SIA/CNES/SINAN/SINASC/SIM) e subíndice de saúde no
  IVM completo.
