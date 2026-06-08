import type { IVMItem, MetaIVM, OndeFoiProduto } from "./types";

// Helpers puros da superfície de "agir" (etapa final do funil — handoff de design): compartilhar,
// citar com proveniência e levar o dado adiante. Tudo no cliente-zero (server components): os links
// são âncoras nativas (wa.me / mailto) e a citação é texto selecionável. Sem segredo, sem PII.

// Domínio canônico do produto. O domínio real é gate do dono (roadmap §Lista de desbloqueio); até
// lá vale o domínio pretendido (o mesmo do handoff), configurável por SITE_URL — reversível.
export function siteUrl(): string {
  return process.env.SITE_URL ?? "https://dadosabedoria.org";
}

export function urlCanonicaOndeFoi(codigoIbge: string): string {
  return `${siteUrl()}/onde-foi/${codigoIbge}`;
}

// Texto cívico de compartilhamento — honesto (execução ≠ serviço, ADR-0029): nunca veredito.
export function textoCompartilharOndeFoi(d: OndeFoiProduto): string {
  return (
    `${d.nome} liquidou ${d.pct}% do que empenhou por função (${d.meta.periodo_rotulo}). ` +
    `Execução orçamentária (SICONFI), não serviço entregue — vale perguntar. via DadoSabedoria`
  );
}

export function linkWhatsapp(texto: string, url: string): string {
  return `https://wa.me/?text=${encodeURIComponent(`${texto} ${url}`)}`;
}

export function linkEmail(assunto: string, corpo: string): string {
  return `mailto:?subject=${encodeURIComponent(assunto)}&body=${encodeURIComponent(corpo)}`;
}

// Citação ABNT a partir da meta de proveniência — todo uso sai com fonte, versão e licença embutidas.
// `hoje` é injetável para teste determinístico.
export function citacaoAbntOndeFoi(d: OndeFoiProduto, hoje: Date = new Date()): string {
  const dataAcesso = hoje.toLocaleDateString("pt-BR");
  const ano = hoje.getFullYear();
  const fontes = d.meta.fontes.map((f) => f.sigla).join(", ");
  return (
    `DadoSabedoria (${ano}). OndeFoi — execução orçamentária por função ` +
    `(${d.meta.versao_metodologia}) — ${d.nome}/${d.uf}, ${d.meta.periodo_rotulo}. ` +
    `Fontes: ${fontes}. Acesso em ${dataAcesso}. ${d.meta.licenca}`
  );
}

// ----------------------------------------------------------------- IVM (mesma superfície de agir)

export function urlCanonicaIvm(codigoIbge: string): string {
  return `${siteUrl()}/ivm/${codigoIbge}`;
}

// O IVM é índice COMPARATIVO de vulnerabilidade (maior = mais vulnerável), min-max no período — não
// veredito nem ranking de "pior cidade". O texto preserva isso (ADR-0018/0025).
export function textoCompartilharIvm(item: IVMItem): string {
  return (
    `IVM de ${item.nome}: ${item.ivm.toFixed(1)} (${item.semaforo}) — índice de vulnerabilidade ` +
    `municipal (emprego, finanças, saúde), comparativo no período ${item.periodo}, não veredito. ` +
    `via DadoSabedoria`
  );
}

export function citacaoAbntIvm(item: IVMItem, meta: MetaIVM, hoje: Date = new Date()): string {
  const dataAcesso = hoje.toLocaleDateString("pt-BR");
  const ano = hoje.getFullYear();
  const fontes = meta.fontes.map((f) => f.sigla).join(", ");
  const uf = item.uf ? `/${item.uf}` : "";
  return (
    `DadoSabedoria (${ano}). Índice de Vulnerabilidade Municipal (IVM ${meta.versao_metodologia}) — ` +
    `${item.nome}${uf}, ${meta.periodo_rotulo}. Fontes: ${fontes}. Acesso em ${dataAcesso}. ${meta.licenca}`
  );
}
