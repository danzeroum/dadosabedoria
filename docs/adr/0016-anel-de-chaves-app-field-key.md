# ADR-0016 — Anel de chaves para a `APP_FIELD_KEY` (rotação sem perda)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
A `APP_FIELD_KEY` (chave de campo do schema `app`) era **uma só** chave, usada de forma
determinística para o pseudônimo (`contato_hash = HMAC(chave, contato)`) e para a cifragem de campo
(`condicao_sensivel`, Fernet). Como o e-mail bruto **nunca** é guardado (privacidade), trocar a chave
“na lata” deixaria os hashes órfãos e os textos ilegíveis — a chave era, na prática, **não
rotacionável sem perda** (lacuna sinalizada nos ADRs 0012 e 0013).

## Decisão — anel de chaves, compatível para trás
- **Config:** `APP_FIELD_KEY` é a chave **primária**; `APP_FIELD_KEYS_ANTIGAS` (CSV) lista as
  **aposentadas**, aceitas só para **decifrar/verificar**. Anel vazio ⇒ comportamento de chave única.
- **Cifragem (`cripto.py`):** `MultiFernet([primária, *antigas])` — cifra com a primária, decifra com
  qualquer; `recifrar` re-cifra um token para a primária (sem precisar do dado bruto).
- **Pseudônimo:** `hash_contato` usa a primária (hash canônico); `hashes_contato` devolve o hash de
  cada chave. No **login**, `migrar_pseudonimo` casa qualquer versão e **regrava** a linha com o hash
  da primária — **re-chave preguiçoso** (sem coluna de versão; a migração é por casamento de hash).
- **Re-cifragem em lote:** `python -m app.consentimento.run_rechave` (no contêiner de consentimento)
  re-cifra todas as `condicao_sensivel` para a primária. Auditado (`acao='rechave_campo'`).
- **Isolamento §8.1 preservado:** a nova `APP_FIELD_KEYS_ANTIGAS` entra na lista de segredos negados
  a api/worker/ai (checagem estática do compose). Só o serviço de consentimento a recebe.

## Procedimento (runbook `docs/runbooks/rotacao-de-segredos.md`)
1. Mover a chave atual para `APP_FIELD_KEYS_ANTIGAS`, pôr a nova em `APP_FIELD_KEY`, reiniciar.
2. `run_rechave` (re-cifra as condições). 3. Pseudônimos migram no login. 4. Remover a antiga do anel.

## Consequências / a evoluir
- A `APP_FIELD_KEY` passa a ser **rotacionável sem perda** (verificado: unidade + integração de
  rotação A→B contra Postgres real — pseudônimo migra, condição re-cifra e decifra só com a nova).
- Pseudônimos de cidadãos que nunca mais acessam ficam na chave antiga até a re-cifragem/aposentação;
  aceitável (não há dado bruto para forçar a migração). Um job de varredura é evolução possível.
- Próximo da trilha de segurança do consentimento: rotação graciosa do `JWT_SECRET` (lista aceita) e
  OIDC real do cidadão.
