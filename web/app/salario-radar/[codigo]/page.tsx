import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarSalarioRadar } from "../../../lib/api";
import type { NivelSalario } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelSalario, string> = {
  alto: "Alto",
  medio: "Médio",
  baixo: "Baixo",
  sem_dado: "Sem dados",
};

const CORES_NIVEL: Record<NivelSalario, string> = {
  alto: "#15803d",
  medio: "#b45309",
  baixo: "#b91c1c",
  sem_dado: "#6b7280",
};

function formatarBRL(n: number): string {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 });
}

export default async function SalarioRadarPage({ params }: { params: { codigo: string } }) {
  const s = await buscarSalarioRadar(params.codigo);
  if (!s) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${s.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <p className="pulso-pergunta">Salário Radar — patamar salarial das novas contratações formais</p>
      <h1>
        {s.nome}
        {s.uf ? ` · ${s.uf}` : ""}
      </h1>

      <div className="salario-painel">
        <div className="salario-bloco">
          <p className="salario-label">Salário médio de admissão (Novo CAGED)</p>
          {s.salario_medio != null ? (
            <>
              <p className="salario-numero">
                <strong>{formatarBRL(s.salario_medio)}</strong>
                <span className="salario-rotulo-numero">média das admissões no mês</span>
              </p>
              <p
                className="salario-nivel"
                style={{ color: CORES_NIVEL[s.nivel] }}
                aria-label={`Nível: ${ROTULOS_NIVEL[s.nivel]}`}
              >
                ●{" "}
                <span>
                  {ROTULOS_NIVEL[s.nivel]}
                  {s.periodo ? ` · ${s.periodo}` : ""}
                </span>
              </p>
            </>
          ) : (
            <p className="salario-sem-dado">Sem dado disponível</p>
          )}
        </div>
      </div>

      <section className="salario-referencia">
        <h2>Referências salariais</h2>
        <dl className="salario-ref-lista">
          <div>
            <dt>Salário mínimo federal (jan/2026)</dt>
            <dd>R$ 1.518,00</dd>
          </div>
          <div>
            <dt>Faixa Baixo (abaixo de R$ 2.000)</dt>
            <dd>Próximo ou abaixo do salário mínimo</dd>
          </div>
          <div>
            <dt>Faixa Médio (R$ 2.000 – R$ 3.999)</dt>
            <dd>Vagas de renda intermediária</dd>
          </div>
          <div>
            <dt>Faixa Alto (R$ 4.000 ou mais)</dt>
            <dd>Vagas técnicas e qualificadas</dd>
          </div>
        </dl>
      </section>

      <section className="pulso-nota">
        <h2>Como ler este número</h2>
        <p>{s.nota}</p>
      </section>

      <dl className="giro-meta">
        <div>
          <dt>Fonte</dt>
          <dd>
            {s.meta.fonte} · {s.meta.metodologia}
            {s.meta.lag_tipico_dias != null ? ` · atraso ~${s.meta.lag_tipico_dias} dias` : ""} ·{" "}
            {s.meta.licenca}
          </dd>
        </div>
      </dl>

      <p style={{ marginTop: "16px" }}>
        <Link href={`/pulso/${s.codigo_ibge}`}>Ver série histórica do emprego formal →</Link>
        <br />
        <Link href={`/giro-local/${s.codigo_ibge}`}>
          Ver o Giro Local (emprego + crédito per capita) →
        </Link>
      </p>
    </main>
  );
}
