// "Dados Relacionados" — primeiro mecanismo de descoberta não-linear (Bloco 3.1 da auditoria).
// Reusa o catálogo único (lib/catalogo.ts): dado o produto atual, sugere outros do MESMO domínio,
// reancorados no mesmo município. Não inventa nada — só navega o acervo já existente.

import { CATALOGO } from "./catalogo";

// Extrai o slug-base de um href de produto MUNICIPAL ("/pulso/3550308" -> "pulso").
// Telas não-municipais (/ivm, /comparar, /perguntar) retornam null.
export function slugBase(href: string): string | null {
  const m = href.match(/^\/([a-z-]+)\/\d+$/);
  return m ? m[1] : null;
}

export interface ProdutoRelacionado {
  titulo: string;
  pergunta: string;
  href: string;
}

// Produtos do mesmo domínio do produto `slugAtual`, com tela municipal, exceto ele próprio,
// reancorados em `codigoIbge`. Ordem do catálogo; no máximo `max`.
export function produtosRelacionados(
  slugAtual: string,
  codigoIbge: string,
  max = 4,
): ProdutoRelacionado[] {
  const atual = CATALOGO.find((p) => slugBase(p.href) === slugAtual);
  if (!atual) return [];
  return CATALOGO.filter((p) => {
    const s = slugBase(p.href);
    return s !== null && s !== slugAtual && p.dominio === atual.dominio;
  })
    .slice(0, max)
    .map((p) => ({
      titulo: p.titulo,
      pergunta: p.pergunta,
      href: `/${slugBase(p.href)}/${codigoIbge}`,
    }));
}
