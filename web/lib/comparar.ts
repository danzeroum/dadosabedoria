import type { IndicadorValor } from "./types";

// Comparar municípios — alinhamento puro de dois panoramas por indicador. Uma linha por indicador,
// com o valor de cada lado (null onde um município não tem aquele indicador no acervo). Ordenado por
// domínio e nome para leitura estável. A tela só renderiza; aqui mora a regra (testável).

export interface LinhaComparacao {
  codigo: string;
  nome: string;
  dominio: string;
  unidade: string;
  a: IndicadorValor | null;
  b: IndicadorValor | null;
}

export function alinharIndicadores(
  a: IndicadorValor[],
  b: IndicadorValor[],
): LinhaComparacao[] {
  const mapaA = new Map(a.map((i) => [i.codigo, i]));
  const mapaB = new Map(b.map((i) => [i.codigo, i]));
  const codigos = [...new Set([...mapaA.keys(), ...mapaB.keys()])];
  const linhas: LinhaComparacao[] = codigos.map((codigo) => {
    const ia = mapaA.get(codigo) ?? null;
    const ib = mapaB.get(codigo) ?? null;
    const ref = (ia ?? ib) as IndicadorValor; // ao menos um existe (o código veio de um dos mapas)
    return { codigo, nome: ref.nome, dominio: ref.dominio, unidade: ref.unidade, a: ia, b: ib };
  });
  linhas.sort((x, y) => x.dominio.localeCompare(y.dominio) || x.nome.localeCompare(y.nome));
  return linhas;
}

// Agrupa as linhas alinhadas por domínio (preserva a ordem já ordenada).
export function agruparPorDominio(linhas: LinhaComparacao[]): [string, LinhaComparacao[]][] {
  const grupos = new Map<string, LinhaComparacao[]>();
  for (const l of linhas) {
    const g = grupos.get(l.dominio) ?? [];
    g.push(l);
    grupos.set(l.dominio, g);
  }
  return [...grupos.entries()];
}
