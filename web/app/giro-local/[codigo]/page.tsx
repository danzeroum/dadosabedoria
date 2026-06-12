import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarGiroLocal } from "../../../lib/api";
import { DemoAviso } from "../../../components/DemoAviso";
import type { NivelCredito, NivelEmprego } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: { codigo: string } }): Promise<Metadata> {
  const data = await buscarGiroLocal(params.codigo);
  if (!data) return { title: "Giro Local · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `Giro Local — ${local} · DadoSabedoria`,
    description: `Dinamismo econômico per capita em ${local}: emprego formal (CAGED) e crédito bancário (ESTBAN) por habitante.`,
  };
}

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

const ROTULOS_CREDITO: Record<NivelCredito, string> = {
  alto: "Alto",
  medio: "Médio",
  baixo: "Baixo",
  sem_dado: "Sem dados",
};
const CORES_CREDITO: Record<NivelCredito, string> = {
  alto: "#15803d",
  medio: "#b45309",
  baixo: "#b91c1c",
  sem_dado: "#6b7280",
};

function formatarSaldo(n: number): string {
  return n >= 0 ? `+${n.toLocaleString("pt-BR")}` : n.toLocaleString("pt-BR");
}

function formatarBRL(n: number): string {
  if (n >= 1_000_000_000) return `R$ ${(n / 1_000_000_000).toFixed(1)} bi`;
  if (n >= 1_000_000) return `R$ ${(n / 1_000_000).toFixed(0)} mi`;
  return `R$ ${n.toLocaleString("pt-BR")}`;
}

export default async function GiroLocalPage({ params }: { params: { codigo: string } }) {
  const g = await buscarGiroLocal(params.codigo);
  if (!g) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${g.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <DemoAviso />
      <p className="pulso-pergunta">Giro Local — dinamismo econômico per capita</p>
      <h1>
        {g.nome}
        {g.uf ? ` · ${g.uf}` : ""}
      </h1>
      {g.populacao != null && (
        <p className="giro-populacao">
          {g.populacao.toLocaleString("pt-BR")} hab · população estimada IBGE
        </p>
      )}

      <div className="giro-painel">
        {/* Emprego formal */}
        <div className="giro-bloco">
          <p className="giro-label">Emprego formal (CAGED)</p>
          {g.saldo_emprego != null ? (
            <>
              <p className="giro-numero">
                <strong>{formatarSaldo(g.saldo_emprego)}</strong>
                <span className="giro-rotulo-numero">vagas no mês</span>
              </p>
              {g.saldo_emprego_per_1000 != null && (
                <p className="giro-per-capita">
                  {g.saldo_emprego_per_1000 >= 0
                    ? `+${g.saldo_emprego_per_1000.toFixed(2)}`
                    : g.saldo_emprego_per_1000.toFixed(2)}{" "}
                  por 1.000 hab
                </p>
              )}
              <p
                className="giro-nivel"
                style={{ color: CORES_EMPREGO[g.nivel_emprego] }}
                aria-label={`Nível: ${ROTULOS_EMPREGO[g.nivel_emprego]}`}
              >
                ●{" "}
                <span>
                  {ROTULOS_EMPREGO[g.nivel_emprego]}
                  {g.periodo_emprego ? ` · ${g.periodo_emprego}` : ""}
                </span>
              </p>
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
        </div>

        {/* Crédito bancário */}
        <div className="giro-bloco">
          <p className="giro-label">Crédito bancário (ESTBAN)</p>
          {g.saldo_credito != null ? (
            <>
              <p className="giro-numero">
                <strong>{formatarBRL(g.saldo_credito)}</strong>
                <span className="giro-rotulo-numero">saldo total</span>
              </p>
              {g.saldo_credito_per_hab != null && (
                <p className="giro-per-capita">
                  {formatarBRL(g.saldo_credito_per_hab)} por hab
                </p>
              )}
              <p
                className="giro-nivel"
                style={{ color: CORES_CREDITO[g.nivel_credito] }}
                aria-label={`Nível: ${ROTULOS_CREDITO[g.nivel_credito]}`}
              >
                ●{" "}
                <span>
                  {ROTULOS_CREDITO[g.nivel_credito]}
                  {g.periodo_credito ? ` · ${g.periodo_credito}` : ""}
                </span>
              </p>
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
        </div>
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{g.nota}</p>
      </section>

      <dl className="giro-meta">
        {g.meta_emprego && (
          <div>
            <dt>Emprego</dt>
            <dd>
              {g.meta_emprego.fonte} · {g.meta_emprego.metodologia}
              {g.meta_emprego.lag_tipico_dias != null
                ? ` · atraso ~${g.meta_emprego.lag_tipico_dias} dias`
                : ""}{" "}
              · {g.meta_emprego.licenca}
            </dd>
          </div>
        )}
        {g.meta_credito && (
          <div>
            <dt>Crédito</dt>
            <dd>
              {g.meta_credito.fonte} · {g.meta_credito.metodologia}
              {g.meta_credito.lag_tipico_dias != null
                ? ` · atraso ~${g.meta_credito.lag_tipico_dias} dias`
                : ""}{" "}
              · {g.meta_credito.licenca}
            </dd>
          </div>
        )}
      </dl>

      <p style={{ marginTop: "16px" }}>
        <Link href={`/pulso/${g.codigo_ibge}`}>Ver série histórica do emprego →</Link>
      </p>
    </main>
  );
}
