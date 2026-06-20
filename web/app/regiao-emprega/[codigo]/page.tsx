import Link from "next/link";
import { notFound } from "next/navigation";

import { DemoAviso } from "../../../components/DemoAviso";
import { buscarRegiaoEmprega } from "../../../lib/api";
import { ProdutosRelacionados } from "../../../components/ProdutosRelacionados";
import type { NivelEmprego } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelEmprego, string> = {
  criando: "Criando empregos",
  estavel: "Estável",
  reduzindo: "Reduzindo empregos",
  sem_dado: "Sem dados",
};

const CORES_NIVEL: Record<NivelEmprego, string> = {
  criando: "#15803d",
  estavel: "#b45309",
  reduzindo: "#b91c1c",
  sem_dado: "#6b7280",
};

function formatarSaldo(n: number): string {
  return n >= 0 ? `+${n.toLocaleString("pt-BR")}` : n.toLocaleString("pt-BR");
}

export default async function RegiaoEmpregaPage({ params }: { params: { codigo: string } }) {
  const r = await buscarRegiaoEmprega(params.codigo);
  if (!r) {
    notFound();
  }

  const municipiosComDado = r.municipios.filter((m) => m.saldo != null);
  const municipiosSemDado = r.municipios.filter((m) => m.saldo == null);

  return (
    <main className="pagina">
      <Link href={`/ivm/${params.codigo}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <DemoAviso />
      <p className="pulso-pergunta">Região Emprega — emprego formal no estado</p>
      <h1>
        {r.nome} ({r.uf})
      </h1>
      {r.periodo && <p className="giro-populacao">Período: {r.periodo}</p>}

      {/* Resumo regional */}
      <div className="regiao-resumo">
        <div className="regiao-total">
          <p className="giro-label">Saldo regional (soma de {r.municipios_total} municípios)</p>
          <p className="regiao-numero">
            <strong style={{ color: CORES_NIVEL[r.nivel] }}>{formatarSaldo(r.saldo_total)}</strong>
            <span className="salario-rotulo-numero">vagas no mês</span>
          </p>
          <p
            className="salario-nivel"
            style={{ color: CORES_NIVEL[r.nivel] }}
            aria-label={`Nível regional: ${ROTULOS_NIVEL[r.nivel]}`}
          >
            ● {ROTULOS_NIVEL[r.nivel]}
          </p>
        </div>

        <div className="regiao-contagens">
          <p className="giro-label">Distribuição dos municípios</p>
          <dl className="regiao-dist">
            <div>
              <dt style={{ color: CORES_NIVEL["criando"] }}>Criando empregos</dt>
              <dd>{r.municipios_criando}</dd>
            </div>
            <div>
              <dt style={{ color: CORES_NIVEL["estavel"] }}>Estáveis</dt>
              <dd>{r.municipios_estaveis}</dd>
            </div>
            <div>
              <dt style={{ color: CORES_NIVEL["reduzindo"] }}>Reduzindo empregos</dt>
              <dd>{r.municipios_reduzindo}</dd>
            </div>
            {r.municipios_sem_dado > 0 && (
              <div>
                <dt style={{ color: CORES_NIVEL["sem_dado"] }}>Sem dado no período</dt>
                <dd>{r.municipios_sem_dado}</dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Tabela de municípios com dado */}
      {municipiosComDado.length > 0 && (
        <section>
          <h2>Municípios com dado no período</h2>
          <div className="regiao-tabela-wrapper">
            <table className="regiao-tabela">
              <thead>
                <tr>
                  <th scope="col">Município</th>
                  <th scope="col" className="tnum">Saldo</th>
                  <th scope="col" className="tnum">Por 1.000 hab</th>
                  <th scope="col">Nível</th>
                </tr>
              </thead>
              <tbody>
                {municipiosComDado.map((m) => (
                  <tr key={m.codigo_ibge}>
                    <td>
                      <Link href={`/ivm/${m.codigo_ibge}`}>{m.nome}</Link>
                    </td>
                    <td
                      className="tnum"
                      style={{ color: CORES_NIVEL[m.nivel] }}
                      aria-label={`Saldo: ${m.saldo}`}
                    >
                      {m.saldo != null ? formatarSaldo(m.saldo) : "–"}
                    </td>
                    <td className="tnum">
                      {m.per_1000 != null
                        ? (m.per_1000 >= 0
                            ? `+${m.per_1000.toFixed(2)}`
                            : m.per_1000.toFixed(2))
                        : "–"}
                    </td>
                    <td style={{ color: CORES_NIVEL[m.nivel] }}>{ROTULOS_NIVEL[m.nivel]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {municipiosSemDado.length > 0 && (
        <section>
          <h2>Municípios sem dado no período</h2>
          <p className="salario-sem-dado">
            {municipiosSemDado.map((m) => m.nome).join(", ")}
          </p>
        </section>
      )}

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{r.nota}</p>
      </section>

      <dl className="giro-meta">
        <div>
          <dt>Fonte</dt>
          <dd>
            {r.meta.fonte} · {r.meta.metodologia}
            {r.meta.lag_tipico_dias != null ? ` · atraso ~${r.meta.lag_tipico_dias} dias` : ""} ·{" "}
            {r.meta.licenca}
          </dd>
        </div>
      </dl>

      <ProdutosRelacionados slug="regiao-emprega" codigoIbge={r.codigo_ibge} />
    </main>
  );
}
