import { MapaSemaforico } from "../../components/MapaSemaforico";
import { buscarIVM } from "../../lib/api";
import { corSemaforo, rotuloSemaforo } from "../../lib/semaforo";
import type { Semaforo } from "../../lib/types";

// Renderiza por requisição (busca dado vivo da API; não pré-renderiza no build).
export const dynamic = "force-dynamic";

const ESTADOS: Semaforo[] = ["verde", "amarelo", "vermelho"];

export default async function IVMPage({
  searchParams,
}: {
  searchParams: { periodo?: string };
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

  return (
    <main className="pagina">
      <h1>Mapa semafórico do IVM</h1>
      <p className="subtitulo">
        {meta.nome} — período {meta.periodo ?? "—"} · metodologia {meta.versao_metodologia}
      </p>
      <p className="metodologia">{meta.metodologia}</p>
      <ul className="legenda">
        {ESTADOS.map((s) => (
          <li key={s}>
            <span className="semaforo-dot" style={{ backgroundColor: corSemaforo(s) }} aria-hidden="true" />
            <strong>{s}</strong>: {rotuloSemaforo(s)} ({meta.semaforo[s]})
          </li>
        ))}
      </ul>
      <MapaSemaforico itens={dados} />
      <p className="nota">
        Painel por município (cartões), do mais ao menos vulnerável. A coropleta geográfica chega
        quando as malhas do IBGE forem ingeridas (ADR-0009).
      </p>
    </main>
  );
}
