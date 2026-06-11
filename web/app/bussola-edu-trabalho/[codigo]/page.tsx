import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarBussolaEduTrab } from "../../../lib/api";
import type { NivelEducacao, NivelEmprego, NivelSalario } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_EDUCACAO: Record<NivelEducacao, string> = {
  alto: "Cobertura alta",
  medio: "Cobertura moderada",
  baixo: "Cobertura baixa",
  sem_dado: "Sem dados",
};
const CORES_EDUCACAO: Record<NivelEducacao, string> = {
  alto: "#15803d",
  medio: "#b45309",
  baixo: "#b91c1c",
  sem_dado: "#6b7280",
};

const ROTULOS_EMPREGO: Record<NivelEmprego, string> = {
  criando: "Criando empregos",
  estavel: "Estável",
  reduzindo: "Reduzindo empregos",
  sem_dado: "Sem dados",
};
const CORES_EMPREGO: Record<NivelEmprego, string> = {
  criando: "#15803d",
  estavel: "#b45309",
  reduzindo: "#b91c1c",
  sem_dado: "#6b7280",
};

const ROTULOS_SALARIO: Record<NivelSalario, string> = {
  alto: "Alto (≥ R$ 4.000)",
  medio: "Médio (R$ 2.000–3.999)",
  baixo: "Próximo ao mínimo (< R$ 2.000)",
  sem_dado: "Sem dados",
};
const CORES_SALARIO: Record<NivelSalario, string> = {
  alto: "#15803d",
  medio: "#b45309",
  baixo: "#b91c1c",
  sem_dado: "#6b7280",
};

function formatarSaldo(n: number): string {
  return n >= 0 ? `+${n.toLocaleString("pt-BR")}` : n.toLocaleString("pt-BR");
}

function formatarBRL(n: number): string {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
}

export default async function BussolaEduTrabPage({ params }: { params: { codigo: string } }) {
  const b = await buscarBussolaEduTrab(params.codigo);
  if (!b) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${b.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <p className="pulso-pergunta">Bússola Educação-Trabalho — base educacional e emprego formal</p>
      <h1>
        {b.nome}
        {b.uf ? ` · ${b.uf}` : ""}
      </h1>
      {b.populacao != null && (
        <p className="giro-populacao">{b.populacao.toLocaleString("pt-BR")} hab · população estimada IBGE</p>
      )}

      <div className="giro-painel">
        {/* Educação (INEP — anual) */}
        <div className="giro-bloco">
          <p className="giro-label">
            Matrículas no ensino fundamental (INEP)
            {b.periodo_educacao ? ` · ${b.periodo_educacao}` : ""}
          </p>
          {b.matriculas != null ? (
            <>
              <p className="giro-numero">
                <strong>{b.matriculas.toLocaleString("pt-BR")}</strong>
                <span className="giro-rotulo-numero">matrículas</span>
              </p>
              {b.matriculas_por_mil != null && (
                <p className="giro-per-capita">{b.matriculas_por_mil.toFixed(1)} por 1.000 hab</p>
              )}
              <p
                className="giro-nivel"
                style={{ color: CORES_EDUCACAO[b.nivel_educacao] }}
                aria-label={`Nível: ${ROTULOS_EDUCACAO[b.nivel_educacao]}`}
              >
                ● <span>{ROTULOS_EDUCACAO[b.nivel_educacao]}</span>
              </p>
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
        </div>

        {/* Emprego formal (CAGED — mensal) */}
        <div className="giro-bloco">
          <p className="giro-label">
            Emprego formal (CAGED)
            {b.periodo_emprego ? ` · ${b.periodo_emprego}` : ""}
          </p>
          {b.saldo_emprego != null ? (
            <>
              <p className="giro-numero">
                <strong>{formatarSaldo(b.saldo_emprego)}</strong>
                <span className="giro-rotulo-numero">vagas no mês</span>
              </p>
              <p
                className="giro-nivel"
                style={{ color: CORES_EMPREGO[b.nivel_emprego] }}
                aria-label={`Nível: ${ROTULOS_EMPREGO[b.nivel_emprego]}`}
              >
                ● <span>{ROTULOS_EMPREGO[b.nivel_emprego]}</span>
              </p>
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
        </div>

        {/* Salário médio das admissões */}
        <div className="giro-bloco">
          <p className="giro-label">Salário médio das novas contratações</p>
          {b.salario_medio != null ? (
            <>
              <p className="giro-numero">
                <strong>{formatarBRL(b.salario_medio)}</strong>
                <span className="giro-rotulo-numero">média das admissões</span>
              </p>
              <p
                className="giro-nivel"
                style={{ color: CORES_SALARIO[b.nivel_salario] }}
                aria-label={`Nível: ${ROTULOS_SALARIO[b.nivel_salario]}`}
              >
                ● <span>{ROTULOS_SALARIO[b.nivel_salario]}</span>
              </p>
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
        </div>
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{b.nota}</p>
      </section>

      <dl className="giro-meta">
        {b.meta_educacao && (
          <div>
            <dt>Educação</dt>
            <dd>
              {b.meta_educacao.fonte} · {b.meta_educacao.metodologia}
              {b.meta_educacao.lag_tipico_dias != null
                ? ` · atraso ~${b.meta_educacao.lag_tipico_dias} dias`
                : ""}{" "}
              · {b.meta_educacao.licenca}
            </dd>
          </div>
        )}
        {b.meta_emprego && (
          <div>
            <dt>Emprego</dt>
            <dd>
              {b.meta_emprego.fonte} · {b.meta_emprego.metodologia}
              {b.meta_emprego.lag_tipico_dias != null
                ? ` · atraso ~${b.meta_emprego.lag_tipico_dias} dias`
                : ""}{" "}
              · {b.meta_emprego.licenca}
            </dd>
          </div>
        )}
        {b.meta_salario && (
          <div>
            <dt>Salário</dt>
            <dd>
              {b.meta_salario.fonte} · {b.meta_salario.metodologia}
              {b.meta_salario.lag_tipico_dias != null
                ? ` · atraso ~${b.meta_salario.lag_tipico_dias} dias`
                : ""}{" "}
              · {b.meta_salario.licenca}
            </dd>
          </div>
        )}
      </dl>

      <p style={{ marginTop: "16px" }}>
        <Link href={`/pulso/${b.codigo_ibge}`}>Ver série histórica do emprego formal →</Link>
        <br />
        <Link href={`/salario-radar/${b.codigo_ibge}`}>Ver o Salário Radar (patamar das contratações) →</Link>
        <br />
        <Link href={`/giro-local/${b.codigo_ibge}`}>Ver o Giro Local (emprego + crédito per capita) →</Link>
      </p>
    </main>
  );
}
