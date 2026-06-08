import Link from "next/link";

import { Coropleta } from "../../components/Coropleta";
import { Legenda } from "../../components/Legenda";
import { MapaSemaforico } from "../../components/MapaSemaforico";
import { buscarIVM, buscarMalhaIVM } from "../../lib/api";
import type { FeatureCollectionIVM } from "../../lib/types";

// Renderiza por requisição (busca dado vivo da API; não pré-renderiza no build).
export const dynamic = "force-dynamic";

const UFS = ["SP", "RJ", "MG"];

export default async function IVMPage({
  searchParams,
}: {
  searchParams: { periodo?: string; uf?: string; q?: string };
}) {
  let dados;
  let meta;
  try {
    const resp = await buscarIVM(searchParams.periodo);
    dados = resp.dados;
    meta = resp.meta;
  } catch {
    return (
      <main className="pagina">
        <h1>Mapa semafórico do IVM</h1>
        <p className="erro">Não foi possível carregar o IVM agora. Verifique se a API está no ar.</p>
      </main>
    );
  }

  const uf = searchParams.uf?.toUpperCase();
  // Busca server-side (sem JS no cliente): filtra a lista por nome ou código IBGE.
  const q = (searchParams.q ?? "").trim();
  const ql = q.toLowerCase();
  const dadosFiltrados = q
    ? dados.filter((d) => d.nome.toLowerCase().includes(ql) || d.codigo_ibge.includes(q))
    : dados;
  let malha: FeatureCollectionIVM | null = null;
  if (uf) {
    try {
      malha = await buscarMalhaIVM(uf, meta.periodo ?? undefined);
    } catch {
      malha = null;
    }
  }

  return (
    <main className="pagina">
      <h1>Mapa semafórico do IVM</h1>
      <p className="subtitulo">
        {meta.nome} — período {meta.periodo ?? "—"} · metodologia {meta.versao_metodologia}
      </p>
      <p className="metodologia">{meta.metodologia}</p>

      <details className="of-explica">
        <summary>O que é o IVM?</summary>
        <div className="of-explica-corpo">
          <p>
            <strong>IVM = Índice de Vulnerabilidade Municipal.</strong> Combina sinais de emprego
            (CAGED), crédito/finanças (ESTBAN) e saúde (internações respiratórias, SIH) num índice
            <strong> 0–100</strong> por município — <strong>maior = mais vulnerável</strong>.
          </p>
          <p>
            É <strong>comparativo</strong> (min-max no período), não um diagnóstico absoluto: serve
            para <strong>priorizar atenção</strong>, não para rotular. A saúde é opcional (entra
            quando há dado não suprimido). Abra um município para ver os subíndices, a série e o selo
            de confiança com as fontes.
          </p>
        </div>
      </details>

      <Legenda faixas={meta.semaforo} />

      <nav className="ufs" aria-label="Coropleta por UF">
        <span>Coropleta por UF:</span>
        {UFS.map((u) => (
          <Link key={u} href={`/ivm?uf=${u}`} className={u === uf ? "uf-ativa" : ""}>
            {u}
          </Link>
        ))}
        {uf && (
          <Link href="/ivm" className="uf-limpar">
            limpar
          </Link>
        )}
      </nav>

      {uf && malha ? <Coropleta malha={malha} uf={uf} /> : null}
      {uf && !malha ? <p className="vazio">Sem mapa para {uf} no momento.</p> : null}

      <h2>Municípios</h2>
      <form className="ivm-busca" method="get" role="search">
        {uf ? <input type="hidden" name="uf" value={uf} /> : null}
        {searchParams.periodo ? (
          <input type="hidden" name="periodo" value={searchParams.periodo} />
        ) : null}
        <label htmlFor="busca-mun">Buscar município</label>
        <input
          id="busca-mun"
          name="q"
          type="search"
          defaultValue={q}
          placeholder="nome ou código IBGE"
        />
        <button type="submit">Buscar</button>
        {q ? (
          <Link href={uf ? `/ivm?uf=${uf}` : "/ivm"} className="uf-limpar">
            limpar
          </Link>
        ) : null}
      </form>
      {q && dadosFiltrados.length === 0 ? (
        <p className="vazio">Nenhum município encontrado para “{q}”.</p>
      ) : (
        <MapaSemaforico itens={dadosFiltrados} />
      )}
      <p className="nota">
        O mapa usa as malhas territoriais do IBGE; municípios sem IVM no período aparecem em cinza.
      </p>
    </main>
  );
}
