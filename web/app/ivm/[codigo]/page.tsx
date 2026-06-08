import Link from "next/link";
import { notFound } from "next/navigation";

import { Comparador } from "../../../components/Comparador";
import { Semaforo } from "../../../components/Semaforo";
import { SeloConfianca } from "../../../components/SeloConfianca";
import { SerieTemporal } from "../../../components/SerieTemporal";
import { buscarSerieIVM } from "../../../lib/api";
import { formatarIVM } from "../../../lib/semaforo";

export const dynamic = "force-dynamic";

export default async function MunicipioPage({ params }: { params: { codigo: string } }) {
  const resp = await buscarSerieIVM(params.codigo);
  if (!resp || resp.dados.length === 0) {
    notFound();
  }
  const serie = resp.dados;
  const atual = serie[serie.length - 1];

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
