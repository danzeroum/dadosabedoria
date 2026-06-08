import Link from "next/link";
import { notFound } from "next/navigation";

import { AcoesIVM } from "../../../components/AcoesIVM";
import { Comparador } from "../../../components/Comparador";
import { Semaforo } from "../../../components/Semaforo";
import { SeloConfianca } from "../../../components/SeloConfianca";
import { SerieTemporal } from "../../../components/SerieTemporal";
import { buscarSerieIVM, buscarSimilaresIVM } from "../../../lib/api";
import { formatarIVM } from "../../../lib/semaforo";

export const dynamic = "force-dynamic";

export default async function MunicipioPage({ params }: { params: { codigo: string } }) {
  const resp = await buscarSerieIVM(params.codigo);
  if (!resp || resp.dados.length === 0) {
    notFound();
  }
  const serie = resp.dados;
  const atual = serie[serie.length - 1];
  const similares = (await buscarSimilaresIVM(params.codigo))?.dados ?? [];

  return (
    <main className="pagina">
      <Link href="/ivm" className="voltar">
        ← Voltar ao mapa
      </Link>
      <h1>{atual.nome}</h1>
      <div className="destaque">
        <span className="destaque-ivm">
          <strong>{formatarIVM(atual.ivm)}</strong> IVM
        </span>
        <Semaforo estado={atual.semaforo} />
        <span className="destaque-periodo">{atual.periodo}</span>
      </div>

      <section>
        <h2>Subíndices de vulnerabilidade ({atual.periodo})</h2>
        <Comparador
          vEmprego={atual.v_emprego}
          vFinancas={atual.v_financas}
          vSaude={atual.v_saude}
          vSaudeEstado={atual.v_saude_estado}
        />
      </section>

      <section>
        <h2>Evolução do IVM</h2>
        <SerieTemporal serie={serie} />
      </section>

      {similares.length > 0 && (
        <section>
          <h2>Cidades parecidas{atual.uf ? ` (${atual.uf})` : ""}</h2>
          <p className="of-sub">
            Mesma UF, vulnerabilidade (IVM) mais próxima — para comparar no contexto, não para
            rankear.
          </p>
          <ul className="parecidas">
            {similares.map((c) => (
              <li key={c.codigo_ibge}>
                <Link href={`/ivm/${c.codigo_ibge}`}>{c.nome}</Link>
                <span className="parecida-ivm tnum">{formatarIVM(c.ivm)} IVM</span>
                <Semaforo estado={c.semaforo} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <AcoesIVM item={atual} meta={resp.meta} />

      <p className="ver-produto">
        <Link href={`/pulso/${atual.codigo_ibge}`}>
          Ver o Pulso Produtivo (saldo de emprego formal) →
        </Link>
        <br />
        <Link href={`/municipio/${atual.codigo_ibge}`}>
          Ver o panorama completo do município →
        </Link>
      </p>

      <section className="of-proveniencia">
        <h2>De onde vem este número</h2>
        <SeloConfianca meta={resp.meta} />
        <p className="metodologia">{resp.meta.metodologia}</p>
      </section>
    </main>
  );
}
