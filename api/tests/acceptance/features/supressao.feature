# language: pt
Funcionalidade: Supressão por k-anonimato na camada ouro
  Para proteger a privacidade (invariante 1)
  A célula com contagem abaixo do limiar é suprimida antes de gravar

  Cenário: supressão de indicador de origem sensível
    Dado um indicador com origem_sensivel = true e n_minimo = 5
    E uma célula município×mês com n_amostra = 3
    Quando a agregação ouro é executada
    Então o valor é gravado com suprimido = true e motivo "n < limiar de privacidade"
