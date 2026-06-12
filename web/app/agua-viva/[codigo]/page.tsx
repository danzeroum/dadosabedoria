import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarAguaViva } from "../../../lib/api";
import { DemoAvisoSnis } from "../../../components/DemoAvisoSnis";
import type { NivelAcesso } from "../../../lib/types";

export const dynamic = "force-dynamic";

const ROTULOS_NIVEL: Record<NivelAcesso, string> = {
  adequado: "Adequado (≥ 90%)",
  atencao: "Atenção (70–89%)",
  alerta: "Alerta (< 70%)",
  sem_dado: "Sem dados disponíveis",
};
const CORES_NIVEL: Record<NivelAcesso, string> = {
  adequado: "#16a34a",
  atencao: "#b45309",
  alerta: "#dc2626",
  sem_dado: "#6b7280",
};

function formatarPct(n: number | null): string {
  if (n === null) return "—";
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " %";
}

function BarraNivel({
  label,
  pct,
  nivel,
}: {
  label: string;
  pct: number | null;
  nivel: NivelAcesso;
}) {
  const cor = CORES_NIVEL[nivel];
  const largura = pct !== null ? Math.min(Math.max(pct, 0), 100) : 0;
  return (
    <div className="giro-bloco">
      <p className="giro-label">{label}</p>
      {pct !== null ? (
        <>
          <p className="giro-numero">
            <strong>{formatarPct(pct)}</strong>
          </p>
          <div
            style={{
              background: "#e5e7eb",
              borderRadius: "4px",
              height: "12px",
              marginTop: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                background: cor,
                height: "100%",
                width: `${largura}%`,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </>
      ) : (
        <p className="giro-sem-dado">Sem dado disponível</p>
      )}
      <p
        className="giro-nivel"
        style={{ color: cor, marginTop: "6px" }}
        aria-label={`Nível: ${ROTULOS_NIVEL[nivel]}`}
      >
        ● <span>{ROTULOS_NIVEL[nivel]}</span>
      </p>
    </div>
  );
}

export default async function AguaVivaPage({ params }: { params: { codigo: string } }) {
  const av = await buscarAguaViva(params.codigo);
  if (!av) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/ivm/${av.codigo_ibge}`} className="voltar">
        ← Ver o IVM do município
      </Link>
      <DemoAvisoSnis />
      <p className="pulso-pergunta">AguaViva — saneamento básico</p>
      <h1>
        {av.nome}
        {av.uf ? ` · ${av.uf}` : ""}
      </h1>
      {av.periodo && (
        <p className="giro-populacao">Exercício de referência: {av.periodo}</p>
      )}

      <div className="giro-painel">
        <BarraNivel
          label={`Atendimento de água${av.periodo ? ` · ${av.periodo}` : ""}`}
          pct={av.agua_pct}
          nivel={av.nivel_agua}
        />
        <BarraNivel
          label={`Coleta de esgoto${av.periodo ? ` · ${av.periodo}` : ""}`}
          pct={av.esgoto_pct}
          nivel={av.nivel_esgoto}
        />
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{av.nota}</p>
      </section>

      {(av.meta_agua || av.meta_esgoto) && (
        <dl className="giro-meta">
          {av.meta_agua && (
            <div>
              <dt>Fonte (água)</dt>
              <dd>
                {av.meta_agua.fonte} · {av.meta_agua.metodologia}
                {av.meta_agua.lag_tipico_dias != null
                  ? ` · atraso ~${av.meta_agua.lag_tipico_dias} dias`
                  : ""}
                {" "}· {av.meta_agua.licenca}
              </dd>
            </div>
          )}
          {av.meta_esgoto && (
            <div>
              <dt>Fonte (esgoto)</dt>
              <dd>
                {av.meta_esgoto.fonte} · {av.meta_esgoto.metodologia}
                {av.meta_esgoto.lag_tipico_dias != null
                  ? ` · atraso ~${av.meta_esgoto.lag_tipico_dias} dias`
                  : ""}
                {" "}· {av.meta_esgoto.licenca}
              </dd>
            </div>
          )}
        </dl>
      )}

      <p style={{ marginTop: "16px" }}>
        <Link href={`/ivm/${av.codigo_ibge}`}>Ver o Índice de Vulnerabilidade Municipal →</Link>
        <br />
        <Link href={`/municipio/${av.codigo_ibge}`}>Ver o panorama completo do município →</Link>
      </p>
    </main>
  );
}
