"""Adaptadores de fonte (padrão Adapter) — isolam o formato de cada fonte pública.

Contrato §6: ``AdaptadorFonte.extrair(janela) -> DataFrame`` para a camada bronze. A
transformação prata→ouro é um Template Method comum (cada adaptador sobrescreve os passos), e a
carga ouro passa SEMPRE pela regra única de supressão (``app.ingestao.ouro.escrever_ouro``).
"""
