import Link from "next/link";

import { EstadoSupressao } from "../../components/EstadoSupressao";
import { buscarPanorama, buscarTerritorios } from "../../lib/api";
import { agruparPorDominio, alinharIndicadores, type LinhaComparacao } from "../../lib/comparar";
import { formatarValor } from "../../lib/formato";
import type { IndicadorValor } from "../../lib/types";

export const dynamic = "force-dynamic";

const ROTULO_DOMINIO: Record<string, string> = {
  trabalho: "Trabalho",
  credito: "Crédito",
  saude: "Saúde",
  financas: "Finanças",
  educacao: "Educação",
  compras: "Compras",
};

function Celula({ ind }: { ind: IndicadorValor | null }) {
  if (!ind) {
    return <span className="cmp-vazio">sem indicador</span>;
  }
  if (ind.suprimido) {
    return <EstadoSupressao estado="suprimido" rotulo="Valor" />;
  }
  return (
    <span className="cmp-valor tnum">
      {ind.valor != null ? formatarValor(ind.valor, ind.unidade) : "—"}
      <small>
        {ind.periodo} · {ind.fonte}
      </small>
    </span>
  );
}

export default async function CompararPage({
  searchParams,
}: {
  searchParams: { a?: string; b?: string; qa?: string; qb?: string };
}) {
  const codA = searchParams.a?.trim() ?? "";
  const codB = searchParams.b?.trim() ?? "";
  const qa = (searchParams.qa ?? "").trim();
  const qb = (searchParams.qb ?? "").trim();

  // Busca de candidatos para A e B (server-side, sem JS)
  const [resA, resB] = await Promise.all([
    qa.length >= 2 ? buscarTerritorios(qa) : Promise.resolve(null),
    qb.length >= 2 ? buscarTerritorios(qb) : Promise.resolve(null),
  ]);

  // Se ambos os códigos estão definidos, carrega o panorama para comparação
  const [pa, pb] =
    codA && codB
      ? await Promise.all([buscarPanorama(codA), buscarPanorama(codB)])
      : [null, null];

  const grupos =
    pa && pb ? agruparPorDominio(alinharIndicadores(pa.indicadores, pb.indicadores)) : [];

  return (
    <main className="pagina">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Comparar municípios</h1>
      <p className="home-lead">
        Lado a lado, o último valor de cada indicador público do acervo nos dois municípios — com a
        fonte e o período. O que é protegido por privacidade aparece como protegido, nunca o número
        por baixo. É descritivo: contexto para perguntar, não um ranking de melhor/pior.
      </p>

      <div className="cmp-picker">
        {/* Picker A */}
        <div className="cmp-picker-lado">
          <span className="cmp-picker-rotulo">Município A</span>
          {pa && (
            <p className="picker-ativo-nome">
              <strong>{pa.nome}</strong>
              {pa.uf ? ` · ${pa.uf}` : ""}
              <Link href={`/comparar?b=${codB}&qb=${qb}`} className="picker-trocar-link">
                {" "}trocar
              </Link>
            </p>
          )}
          <form method="get" className="picker-busca-form">
            <input type="hidden" name="b" value={codB} />
            <input type="hidden" name="a" value={codA} />
            <label htmlFor="busca-a">Buscar A</label>
            <input
              id="busca-a"
              name="qa"
              type="search"
              defaultValue={qa}
              placeholder="nome do município"
            />
            <button type="submit">Buscar</button>
          </form>
          {resA && resA.dados.length === 0 && qa && (
            <p className="vazio">Nenhum município para &ldquo;{qa}&rdquo;.</p>
          )}
          {resA && resA.dados.length > 0 && (
            <ul className="busca-resultados">
              {resA.dados.map((t) => (
                <li key={t.codigo_ibge}>
                  <Link href={`/comparar?a=${t.codigo_ibge}&b=${codB}`}>
                    {t.nome}
                    {t.uf ? ` · ${t.uf}` : ""}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Picker B */}
        <div className="cmp-picker-lado">
          <span className="cmp-picker-rotulo">Município B</span>
          {pb && (
            <p className="picker-ativo-nome">
              <strong>{pb.nome}</strong>
              {pb.uf ? ` · ${pb.uf}` : ""}
              <Link href={`/comparar?a=${codA}&qa=${qa}`} className="picker-trocar-link">
                {" "}trocar
              </Link>
            </p>
          )}
          <form method="get" className="picker-busca-form">
            <input type="hidden" name="a" value={codA} />
            <input type="hidden" name="b" value={codB} />
            <label htmlFor="busca-b">Buscar B</label>
            <input
              id="busca-b"
              name="qb"
              type="search"
              defaultValue={qb}
              placeholder="nome do município"
            />
            <button type="submit">Buscar</button>
          </form>
          {resB && resB.dados.length === 0 && qb && (
            <p className="vazio">Nenhum município para &ldquo;{qb}&rdquo;.</p>
          )}
          {resB && resB.dados.length > 0 && (
            <ul className="busca-resultados">
              {resB.dados.map((t) => (
                <li key={t.codigo_ibge}>
                  <Link href={`/comparar?a=${codA}&b=${t.codigo_ibge}`}>
                    {t.nome}
                    {t.uf ? ` · ${t.uf}` : ""}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {codA && codB && (
          <p className="cmp-trocar">
            <Link href={`/comparar?a=${codB}&b=${codA}`}>trocar A ↔ B</Link>
          </p>
        )}
      </div>

      {!codA || !codB ? (
        <p className="vazio">Busque e selecione dois municípios acima para ver a comparação.</p>
      ) : grupos.length === 0 ? (
        <p className="vazio">Sem indicadores em comum no acervo para estes municípios.</p>
      ) : (
        <div className="cmp-tabela">
          <div className="cmp-linha cmp-cabeca">
            <span>Indicador</span>
            <span>{pa!.nome}</span>
            <span>{pb!.nome}</span>
          </div>
          {grupos.map(([dominio, linhas]: [string, LinhaComparacao[]]) => (
            <div key={dominio} className="cmp-grupo">
              <h2 className="cmp-dominio">{ROTULO_DOMINIO[dominio] ?? dominio}</h2>
              {linhas.map((l) => (
                <div key={l.codigo} className="cmp-linha">
                  <span className="cmp-ind">{l.nome}</span>
                  <span>
                    <Celula ind={l.a} />
                  </span>
                  <span>
                    <Celula ind={l.b} />
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <p className="metodologia">
        Cada número traz seu período e sua fonte. Valores mais recentes no acervo; a periodicidade
        varia por fonte. Comparar não é rankear — unidades e contextos diferem entre indicadores.
      </p>
    </main>
  );
}
