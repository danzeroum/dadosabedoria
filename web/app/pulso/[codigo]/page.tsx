import Link from "next/link";
import { notFound } from "next/navigation";

import { PulsoSelo } from "../../../components/PulsoSelo";
import { SerieSaldo } from "../../../components/SerieSaldo";
import { buscarPulso } from "../../../lib/api";
import { ROTULOS_TENDENCIA, SETA_TENDENCIA, formatarSaldo } from "../../../lib/pulso";

export const dynamic = "force-dynamic";

export default async function PulsoPage({ params }: { params: { codigo: string } }) {
  const p = await buscarPulso(params.codigo);
  if (!p) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${p.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <p className="pulso-pergunta">Pulso Produtivo — emprego formal</p>
      <h1>
        {p.nome}
        {p.uf ? ` · ${p.uf}` : ""}
      </h1>

      <div className="pulso-destaque">
        <span className="pulso-numero" style={{ color: "var(--cor-texto)" }}>
          <strong>{formatarSaldo(p.saldo_mes)}</strong>
          <span className="pulso-numero-rotulo">vagas no mês ({p.periodo})</span>
        </span>
        <PulsoSelo estado={p.pulso} />
        {p.tendencia ? (
          <span className={`tendencia tendencia-${p.tendencia}`} title={ROTULOS_TENDENCIA[p.tendencia]}>
            <span aria-hidden="true">{SETA_TENDENCIA[p.tendencia]}</span> {ROTULOS_TENDENCIA[p.tendencia]}
          </span>
        ) : null}
      </div>

      <section>
        <h2>Mês a mês</h2>
        <SerieSaldo meses={p.meses} />
        <dl className="pulso-contexto">
          <div>
            <dt>Acumulado na janela</dt>
            <dd>{formatarSaldo(p.saldo_acumulado)} vagas</dd>
          </div>
          <div>
            <dt>Meses positivos</dt>
            <dd>{p.meses_positivos}</dd>
          </div>
          <div>
            <dt>Meses negativos</dt>
            <dd>{p.meses_negativos}</dd>
          </div>
        </dl>
        <p className="pulso-aviso">
          O acumulado é <strong>contexto</strong>, não veredito — uma janela curta pode ser puxada
          por um único mês. Por isso a batida atual e a série inteira ficam à vista.
        </p>
      </section>

      <section className="pulso-nota">
        <h2>Como ler este número</h2>
        <p>{p.nota}</p>
      </section>

      <p className="metodologia">
        Fonte: {p.meta.fonte} · {p.meta.metodologia}
        {p.meta.lag_tipico_dias != null ? ` · atraso típico ~${p.meta.lag_tipico_dias} dias` : ""} ·{" "}
        {p.meta.licenca}
      </p>

      <p style={{ marginTop: "16px" }}>
        <Link href={`/regiao-emprega/${p.codigo_ibge}`}>
          Ver a Região Emprega{p.uf ? ` (${p.uf})` : ""} — o problema é local ou regional? →
        </Link>
        <br />
        <Link href={`/salario-radar/${p.codigo_ibge}`}>
          Ver o Salário Radar (patamar salarial das novas contratações) →
        </Link>
        <br />
        <Link href={`/giro-local/${p.codigo_ibge}`}>Ver o Giro Local (emprego + crédito per capita) →</Link>
      </p>
    </main>
  );
}
