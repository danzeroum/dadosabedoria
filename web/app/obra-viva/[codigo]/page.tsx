import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarObraViva } from "../../../lib/api";
import type { NivelContratos } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelContratos, string> = {
  elevado: "Alta intensidade de contratação (≥ R$ 3.000/hab)",
  moderado: "Intensidade moderada (R$ 500–2.999/hab)",
  baixo: "Baixa intensidade (< R$ 500/hab)",
  sem_dado: "Sem dados disponíveis",
};
const CORES_NIVEL: Record<NivelContratos, string> = {
  elevado: "#1d4ed8",
  moderado: "#b45309",
  baixo: "#6b7280",
  sem_dado: "#6b7280",
};

function formatarBRL(n: number): string {
  return n.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  });
}

export default async function ObraVivaPage({ params }: { params: { codigo: string } }) {
  const o = await buscarObraViva(params.codigo);
  if (!o) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${o.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <p className="pulso-pergunta">ObraViva — contratações públicas via PNCP</p>
      <h1>
        {o.nome}
        {o.uf ? ` · ${o.uf}` : ""}
      </h1>
      {o.populacao != null && (
        <p className="giro-populacao">{o.populacao.toLocaleString("pt-BR")} hab · população estimada IBGE</p>
      )}

      <div className="giro-painel">
        {/* Bloco principal — valor total de contratos */}
        <div className="giro-bloco">
          <p className="giro-label">
            Contratos públicos (PNCP){o.periodo ? ` · ${o.periodo}` : ""}
          </p>
          {o.valor_contratos != null ? (
            <>
              <p className="giro-numero">
                <strong>{formatarBRL(o.valor_contratos)}</strong>
                <span className="giro-rotulo-numero">valor total dos contratos</span>
              </p>
              {o.valor_por_hab != null && (
                <p className="giro-per-capita">{formatarBRL(o.valor_por_hab)} por habitante</p>
              )}
              <p
                className="giro-nivel"
                style={{ color: CORES_NIVEL[o.nivel] }}
                aria-label={`Nível: ${ROTULOS_NIVEL[o.nivel]}`}
              >
                ● <span>{ROTULOS_NIVEL[o.nivel]}</span>
              </p>
            </>
          ) : (
            <p className="giro-sem-dado">Sem dado disponível</p>
          )}
        </div>

        {/* Bloco de contexto */}
        <div className="giro-bloco">
          <p className="giro-label">O que o PNCP registra?</p>
          <p style={{ fontSize: "0.85rem", color: "#374151", marginTop: "8px", lineHeight: 1.5 }}>
            O PNCP reúne contratos publicados por órgãos federais, estaduais e municipais.
            Inclui <strong>obras, serviços e bens</strong> — não distingue tipos.
          </p>
          <p style={{ fontSize: "0.78rem", color: "#6b7280", marginTop: "8px" }}>
            Municípios que ainda não publicam no PNCP aparecem sem dado.{" "}
            <strong>Ausência ≠ ausência de contratação.</strong>
          </p>
        </div>
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{o.nota}</p>
      </section>

      {o.meta && (
        <dl className="giro-meta">
          <div>
            <dt>Fonte</dt>
            <dd>
              {o.meta.fonte} · {o.meta.metodologia}
              {o.meta.lag_tipico_dias != null ? ` · atraso ~${o.meta.lag_tipico_dias} dias` : ""}
              {" "}· {o.meta.licenca}
            </dd>
          </div>
        </dl>
      )}

      <p style={{ marginTop: "16px" }}>
        <Link href={`/municipio/${o.codigo_ibge}`}>Ver o panorama completo do município →</Link>
        <br />
        <Link href={`/onde-foi/${o.codigo_ibge}`}>Ver o OndeFoi (execução orçamentária) →</Link>
        <br />
        <Link href={`/ivm/${o.codigo_ibge}`}>Ver o Índice de Vulnerabilidade Municipal →</Link>
      </p>
    </main>
  );
}
