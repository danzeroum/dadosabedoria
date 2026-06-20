import Link from "next/link";

import { buscarCuriosidades } from "../lib/api";

// "Você Sabia?" — fatos ANCORADOS do município (cita a fonte, sem causalidade). Server component:
// busca no backend; sem fato nítido → não renderiza nada (honesto, sem card vazio).
export async function VoceSabia({ codigoIbge }: { codigoIbge: string }) {
  let dados;
  try {
    dados = await buscarCuriosidades(codigoIbge);
  } catch {
    return null; // degrada em silêncio — a tela segue inteira
  }
  if (!dados || dados.curiosidades.length === 0) return null;
  return (
    <section className="voce-sabia" aria-label="Você sabia?">
      <h2>Você sabia?</h2>
      <ul>
        {dados.curiosidades.map((c) => (
          <li key={c.texto}>
            <p className="voce-sabia-fato">{c.texto}</p>
            <p className="voce-sabia-fonte">
              Fonte: {c.fonte}
              {c.produto ? (
                <>
                  {" · "}
                  <Link href={`/${c.produto}/${codigoIbge}`}>explorar →</Link>
                </>
              ) : null}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
