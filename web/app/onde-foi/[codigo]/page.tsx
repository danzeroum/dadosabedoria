import Link from "next/link";
import { notFound } from "next/navigation";

import { Donut } from "../../../components/Donut";
import { ExecucaoFuncoes } from "../../../components/ExecucaoFuncoes";
import { SeloConfianca } from "../../../components/SeloConfianca";
import { buscarOndeFoi } from "../../../lib/api";
import { formatarMilhoes, mensagemBanda } from "../../../lib/onde-foi";

export const dynamic = "force-dynamic";

export default async function OndeFoiPage({ params }: { params: { codigo: string } }) {
  const d = await buscarOndeFoi(params.codigo);
  if (!d) {
    notFound();
  }
  const nProtegidas = d.funcoes.filter((f) => f.exe_estado !== "valor").length;

  return (
    <main className="pagina">
      <Link href="/ivm" className="voltar">
        ← Voltar ao mapa
      </Link>

      <div className="of-cabecalho">
        <div>
          <p className="of-eyebrow">
            {d.uf} · {d.codigo_ibge} · {d.meta.periodo_rotulo}
          </p>
          <h1>Onde foi o dinheiro de {d.nome}?</h1>
        </div>
        <details className="of-explica">
          <summary>O que é “execução”?</summary>
          <div className="of-explica-corpo">
            <p>
              <strong>Execução ≠ serviço entregue.</strong> “Executar” é <strong>empenhar e
              liquidar</strong> a despesa — o recurso saiu do orçamento e foi pago. Isso{" "}
              <strong>não garante</strong> hospital funcionando ou obra entregue.
            </p>
            <p>
              Um <strong>% alto</strong> ainda merece a pergunta “virou serviço?”. Um{" "}
              <strong>% baixo</strong> merece a pergunta “por que não saiu?”.
            </p>
          </div>
        </details>
      </div>

      <section className="enquadra">
        <Donut pct={d.pct} banda={d.banda} />
        <div className="enquadra-txt">
          <h2>
            <strong>Executou {d.pct}%</strong> do que foi divulgado por função — e isso merece a
            pergunta.
          </h2>
          <p>
            De cada R$ 100 <strong>divulgados por função</strong>, <strong>R$ {d.pct}</strong> foram
            executados. {mensagemBanda(d.banda)}
          </p>
          <div className="recebido">
            <span>
              Divulgado por função <b className="tnum">{formatarMilhoes(d.recebido_base)}</b>
            </span>
            <span>
              Executou <b className="tnum">{formatarMilhoes(d.executado)}</b>
            </span>
            <span className="recebido-fora">
              Fora do cálculo <b className="tnum">{formatarMilhoes(d.recebido_fora_base)}</b>
            </span>
          </div>
        </div>
      </section>

      <p className="honesto">
        <strong>Atenção honesta:</strong> o % usa a <strong>mesma base</strong> (executado ÷ recebido
        das funções divulgadas). Do total recebido — <strong>{formatarMilhoes(d.recebido_total)}</strong>{" "}
        — há <strong>{formatarMilhoes(d.recebido_fora_base)}</strong> não detalhados por função ou
        protegidos, <strong>fora deste cálculo</strong> (não no denominador). E isto é{" "}
        <strong>execução orçamentária</strong> (SICONFI), não serviço entregue: um % alto não prova
        hospital funcionando; um % baixo é sinal para perguntar, não sentença.
      </p>

      <section>
        <h2>Execução por função orçamentária</h2>
        <p className="of-sub">
          {d.meta.periodo_rotulo} · a barra mostra quanto do recebido foi executado ·{" "}
          {nProtegidas > 0
            ? `${nProtegidas} função(ões) com dado protegido ou sem cobertura — não é zero`
            : "todas as funções com dado"}
        </p>
        <ExecucaoFuncoes funcoes={d.funcoes} />
      </section>

      <section className="of-proveniencia">
        <h2>De onde vem este número</h2>
        <SeloConfianca meta={d.meta} />
        <p className="metodologia">
          {d.meta.metodologia} · grau-demo até a 1ª busca real no SICONFI/DCA (#0).
        </p>
      </section>
    </main>
  );
}
