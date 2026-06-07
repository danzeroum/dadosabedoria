// Formatação de valor por unidade do indicador (único lugar). Reais com R$/milhar sem centavos;
// contagem (e demais) em milhar pt-BR — o sinal aparece quando o valor é negativo (ex.: saldo).

export function formatarValor(valor: number, unidade: string): string {
  if (unidade === "reais") {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      maximumFractionDigits: 0,
    }).format(valor);
  }
  return new Intl.NumberFormat("pt-BR").format(valor);
}
