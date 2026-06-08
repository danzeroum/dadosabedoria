import Link from "next/link";
import { notFound } from "next/navigation";

import { EstadoSupressao } from "../../components/EstadoSupressao";
import { buscarPanorama, buscarValores } from "../../lib/api";
import { formatarValor } from "../../lib/formato";
import type { IndicadorValor, ValorSerie } from "../../lib/types";

export const dynamic = "force-dynamic";

function Valor({ v, unidade }: { v: ValorSerie; unidade: string }) {
  if (v.suprimido) {
    return <EstadoSupressao estado="suprimido" rotulo="Valor" />;
  }
  return <>{v.valor != null ? formatarValor(v.valor, unidade) : "—"}</>;
}

export default async function SeriePage({
  searchParams,
}: {
  searchParams: { territorio?: string; indicador?: string };
}) {
  const { territorio, indicador } = searchParams;
  if (!territorio || !indicador) {
    notFound();
  }

  const [panorama, valores] = await Promise.all([
    buscarPanorama(territorio),
    buscarValores(indicador, territorio),
  ]);
  if (!panorama) {
    notFound();
  }

  const ind: IndicadorValor | undefined = panorama.indicadores.find((i) => i.codigo === indicador);
  const serie = valores?.dados ?? [];
  const nome = ind?.nome ?? valores?.meta.nome ?? indicador;
  const unidade = ind?.unidade ?? "";
  const fonte = ind?.fonte ?? valores?.meta.fonte ?? "—";
  const metodologia = ind?.metodologia ?? valores?.meta.metodologia ?? "";
  const lag = ind?.lag_tipico_dias ?? valores?.meta.lag_tipico_dias ?? null;

  const divulgados = serie.filter(
    (v): v is ValorSerie & { valor: number } => !v.suprimido && v.valor != null,
  );

  return (
    <main className="pagina">
      <Link href={`/municipio/${territorio}`} className="voltar">
        ← Panorama de {panorama.nome}
      </Link>
      <p className="pulso-pergunta">Série histórica</p>
      <h1>{nome}</h1>
      <p className="ficha-dominio">
        {panorama.nome}
        {panorama.uf ? ` · ${panorama.uf}` : ""} · <code>{indicador}</code>
      </p>

      {serie.length === 0 ? (
        <p className="vazio">Sem série deste indicador para este município no acervo ainda.</p>
      ) : (
        <>
          {divulgados.length >= 2 ? (
            <p className="serie-variacao">
              De <strong>{formatarValor(divulgados[0].valor, unidade)}</strong> (
              {divulgados[0].periodo}) a{" "}
              <strong>{formatarValor(divulgados[divulgados.length - 1].valor, unidade)}</strong> (
              {divulgados[divulgados.length - 1].periodo}) — descrição do que foi divulgado, não
              tendência projetada.
            </p>
          ) : null}
          <table className="serie-tabela">
            <caption className="sr-only">
              Série de {nome} em {panorama.nome}
            </caption>
            <thead>
              <tr>
                <th scope="col">Período</th>
                <th scope="col">Valor</th>
              </tr>
            </thead>
            <tbody>
              {serie.map((v) => (
                <tr key={v.periodo}>
                  <th scope="row">{v.periodo}</th>
                  <td>
                    <Valor v={v} unidade={unidade} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <section>
        <h2>Proveniência</h2>
        <p className="metodologia">
          Fonte: <strong>{fonte}</strong>
          {lag != null ? ` · atraso típico ~${lag} dias` : ""}. {metodologia}
        </p>
        <p className="metodologia">
          Veja <Link href={`/indicador/${indicador}`}>o como deste indicador</Link> (metodologia
          completa). Uma célula protegida por privacidade aparece como protegida — nunca o número por
          baixo.
        </p>
      </section>
    </main>
  );
}
