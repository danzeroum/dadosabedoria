"""Ingestão — a regra única de supressão e o caminho de escrita ouro compartilhado.

A regra de k-anonimato existe em UM lugar (``supressao.py``) e é aplicada em UM ponto
(``ouro.escrever_ouro``). Tanto o seed quanto a futura ingestão real passam por aqui — nada
escreve em ``valor`` por fora (garantido por teste no quality gate).
"""
