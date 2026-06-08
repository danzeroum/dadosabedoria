import Link from "next/link";
import { notFound } from "next/navigation";

import { EstadoSupressao } from "../../components/EstadoSupressao";
import { buscarIVM, buscarPanorama } from "../../lib/api";
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

// Célula de valor (reusa o tratamento do panorama): protegido → cadeado; sem valor → travessão.
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
  searchParams: { a?: string; b?: string };
}) {
  let municipios: { codigo_ibge: string; nome: string; uf?: string | null }[] = [];
  try {
    municipios = (await buscarIVM()).dados;
  } catch {
    municipios = [];
  }
  if (municipios.length < 2) {
    return (
      <main className="pagina">
        <Link href="/" className="voltar">
          ← Início
        </Link>
        <h1>Comparar municípios</h1>
        <p className="vazio">
          Preciso de pelo menos dois municípios no acervo para comparar. Volte quando houver mais
          cobertura.
        </p>
      </main>
    );
  }

  const codA = municipios.find((m) => m.codigo_ibge === searchParams.a)?.codigo_ibge ?? municipios[0].codigo_ibge;
  const codB =
    municipios.find((m) => m.codigo_ibge === searchParams.b && m.codigo_ibge !== codA)?.codigo_ibge ??
    municipios.find((m) => m.codigo_ibge !== codA)!.codigo_ibge;

  const [pa, pb] = await Promise.all([buscarPanorama(codA), buscarPanorama(codB)]);
  if (!pa || !pb) {
    notFound();
  }
  const grupos = agruparPorDominio(alinharIndicadores(pa.indicadores, pb.indicadores));

  const linkPicker = (lado: "a" | "b", codigo: string) =>
    lado === "a" ? `/comparar?a=${codigo}&b=${codB}` : `/comparar?a=${codA}&b=${codigo}`;

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

      <nav className="cmp-picker" aria-label="Escolher municípios">
        <div className="cmp-picker-lado">
          <span className="cmp-picker-rotulo">Município A</span>
          {municipios.map((m) => (
            <Link
              key={`a-${m.codigo_ibge}`}
              href={linkPicker("a", m.codigo_ibge)}
              className={m.codigo_ibge === codA ? "picker-ativo" : ""}
              aria-current={m.codigo_ibge === codA ? "true" : undefined}
            >
              {m.nome}
            </Link>
          ))}
        </div>
        <div className="cmp-picker-lado">
          <span className="cmp-picker-rotulo">Município B</span>
          {municipios.map((m) => (
            <Link
              key={`b-${m.codigo_ibge}`}
              href={linkPicker("b", m.codigo_ibge)}
              className={m.codigo_ibge === codB ? "picker-ativo" : ""}
              aria-current={m.codigo_ibge === codB ? "true" : undefined}
            >
              {m.nome}
            </Link>
          ))}
        </div>
        <p className="cmp-trocar">
          <Link href={`/comparar?a=${codB}&b=${codA}`}>trocar A ↔ B</Link>
        </p>
      </nav>

      {grupos.length === 0 ? (
        <p className="vazio">Sem indicadores em comum no acervo para estes municípios.</p>
      ) : (
        <div className="cmp-tabela">
          <div className="cmp-linha cmp-cabeca">
            <span>Indicador</span>
            <span>{pa.nome}</span>
            <span>{pb.nome}</span>
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
