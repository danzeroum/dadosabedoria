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
  searchParams: { periodo?: string; uf?: string };
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
      <MapaSemaforico itens={dados} />
      <p className="nota">
        A coropleta usa as malhas do IBGE (carregue com <code>run_ibge &lt;UF&gt;</code>). Município sem
        IVM fica cinza. ADR-0010.
      </p>
    </main>
  );
}
