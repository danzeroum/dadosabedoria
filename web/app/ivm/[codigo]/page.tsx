import Link from "next/link";
import { notFound } from "next/navigation";

import { AcoesIVM } from "../../../components/AcoesIVM";
import { Comparador } from "../../../components/Comparador";
import { Semaforo } from "../../../components/Semaforo";
import { SeloConfianca } from "../../../components/SeloConfianca";
import { SerieTemporal } from "../../../components/SerieTemporal";
import { buscarSerieIVM, buscarSimilaresIVM } from "../../../lib/api";
import { significadoIVM, tendenciaIVM } from "../../../lib/ivm-leitura";
import { formatarIVM } from "../../../lib/semaforo";

export const dynamic = "force-dynamic";

export default async function MunicipioPage({
  params,
  searchParams,
}: {
  params: { codigo: string };
  searchParams: { compara?: string };
}) {
  const resp = await buscarSerieIVM(params.codigo);
  if (!resp || resp.dados.length === 0) {
    notFound();
  }
  const serie = resp.dados;
  const atual = serie[serie.length - 1];
  const similares = (await buscarSimilaresIVM(params.codigo))?.dados ?? [];
  // Comparação lado a lado (sem JS): a parecida escolhida vem do ?compara=, default = a mais próxima.
  const outra = similares.find((c) => c.codigo_ibge === searchParams.compara) ?? similares[0] ?? null;

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

      <p className={`dd-significado dd-sem-${atual.semaforo}`}>
        {significadoIVM(atual.nome, atual.semaforo)}
      </p>

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
        <p className="serie-nota">
          {tendenciaIVM(serie).texto} Pontos suprimidos por privacidade seriam marcados, nunca
          omitidos.
        </p>
      </section>

      {similares.length > 0 && outra && (
        <section>
          <h2>Comparar com cidade parecida{atual.uf ? ` (${atual.uf})` : ""}</h2>
          <p className="of-sub">
            Mesma UF, vulnerabilidade (IVM) mais próxima — para enxergar se o problema é local ou
            regional, não para rankear. Escolha com quem comparar:
          </p>
          <nav className="comparar-picker" aria-label="Escolher cidade para comparar">
            {similares.map((c) => (
              <Link
                key={c.codigo_ibge}
                href={`/ivm/${atual.codigo_ibge}?compara=${c.codigo_ibge}`}
                className={c.codigo_ibge === outra.codigo_ibge ? "picker-ativo" : ""}
                aria-current={c.codigo_ibge === outra.codigo_ibge ? "true" : undefined}
              >
                {c.nome}
              </Link>
            ))}
          </nav>
          <div className="comparar-grid">
            <article className="comparar-card comparar-card-base">
              <h3>
                {atual.nome} <span className="tnum">{formatarIVM(atual.ivm)} IVM</span>
                <Semaforo estado={atual.semaforo} />
              </h3>
              <Comparador
                vEmprego={atual.v_emprego}
                vFinancas={atual.v_financas}
                vSaude={atual.v_saude}
                vSaudeEstado={atual.v_saude_estado}
              />
            </article>
            <p className="comparar-vs" aria-hidden="true">
              vs
            </p>
            <article className="comparar-card">
              <h3>
                <Link href={`/ivm/${outra.codigo_ibge}`}>{outra.nome}</Link>{" "}
                <span className="tnum">{formatarIVM(outra.ivm)} IVM</span>
                <Semaforo estado={outra.semaforo} />
              </h3>
              <Comparador
                vEmprego={outra.v_emprego}
                vFinancas={outra.v_financas}
                vSaude={outra.v_saude}
                vSaudeEstado={outra.v_saude_estado}
              />
            </article>
          </div>
        </section>
      )}

      <AcoesIVM item={atual} meta={resp.meta} />

      <p className="ver-produto">
        <Link href={`/pulso/${atual.codigo_ibge}`}>
          Ver o Pulso Produtivo (saldo de emprego formal) →
        </Link>
        <br />
        <Link href={`/giro-local/${atual.codigo_ibge}`}>
          Ver o Giro Local (emprego + crédito per capita) →
        </Link>
        <br />
        <Link href={`/salario-radar/${atual.codigo_ibge}`}>
          Ver o Salário Radar (patamar salarial das novas contratações) →
        </Link>
        <br />
        <Link href={`/regiao-emprega/${atual.codigo_ibge}`}>
          Ver a Região Emprega{atual.uf ? ` (${atual.uf})` : ""} — local ou regional? →
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
