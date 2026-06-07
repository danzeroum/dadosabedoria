import Link from "next/link";
import { notFound } from "next/navigation";

import { BandaSelo } from "../../../components/BandaSelo";
import { ExecucaoFuncoes } from "../../../components/ExecucaoFuncoes";
import { buscarOndeFoi } from "../../../lib/api";
import { formatarReais } from "../../../lib/onde-foi";

export const dynamic = "force-dynamic";

export default async function OndeFoiPage({ params }: { params: { codigo: string } }) {
  const d = await buscarOndeFoi(params.codigo);
  if (!d) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href="/ivm" className="voltar">
        ← Voltar ao mapa
      </Link>
      <p className="pulso-pergunta">OndeFoi — a transferência virou serviço?</p>
      <h1>
        {d.nome} · {d.uf}
      </h1>

      <div className="pulso-destaque">
        <span className="pulso-numero">
          <strong>{d.pct}%</strong>
          <span className="pulso-numero-rotulo">executado da base divulgada</span>
        </span>
        <BandaSelo banda={d.banda} />
        <span className="ondefoi-valores">
          {formatarReais(d.executado)} de {formatarReais(d.recebido_base)}
        </span>
      </div>

      <section className="pulso-nota ondefoi-aviso">
        <h2>Como ler este número</h2>
        <p>
          Isto é <strong>execução orçamentária</strong> (empenho/liquidação),{" "}
          <strong>não serviço entregue</strong>. Executar o orçamento não é o mesmo que a obra ficar
          pronta ou o atendimento chegar — execução baixa <strong>merece a pergunta</strong>, não é
          veredito de corrupção.
        </p>
      </section>

      <section>
        <h2>Por função ({d.meta.periodo_rotulo})</h2>
        <ExecucaoFuncoes funcoes={d.funcoes} />
        {d.recebido_fora_base > 0 ? (
          <p className="pulso-aviso">
            Fora da base detalhada: <strong>{formatarReais(d.recebido_fora_base)}</strong> recebidos
            sem execução por função divulgada (sem cobertura ou não detalhado). Por transparência
            ficam <strong>fora do %</strong> — o total recebido ({formatarReais(d.recebido_total)})
            nunca é o denominador.
          </p>
        ) : null}
      </section>

      <p className="metodologia">
        {d.meta.metodologia} · Fontes:{" "}
        {d.meta.fontes.map((f) => `${f.sigla} (${f.orgao}, ${f.ate})`).join("; ")} · atraso típico ~
        {d.meta.atraso_dias} dias
      </p>
    </main>
  );
}
