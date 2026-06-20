import Link from "next/link";

import { produtosRelacionados } from "../lib/relacionados";

// "Veja também" — descoberta não-linear entre produtos do mesmo domínio, no mesmo município.
export function ProdutosRelacionados({ slug, codigoIbge }: { slug: string; codigoIbge: string }) {
  const rel = produtosRelacionados(slug, codigoIbge);
  if (rel.length === 0) return null;
  return (
    <nav className="relacionados" aria-label="Dados relacionados neste município">
      <h2>Veja também, neste município</h2>
      <ul>
        {rel.map((p) => (
          <li key={p.href}>
            <Link href={p.href}>
              <strong>{p.titulo}</strong>
              <span>{p.pergunta}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
