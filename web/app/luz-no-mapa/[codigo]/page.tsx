import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarLuzNoMapa } from "../../../lib/api";
import { ProdutosRelacionados } from "../../../components/ProdutosRelacionados";
import type { NivelEnergia } from "../../../lib/types";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: { codigo: string } }): Promise<Metadata> {
  const data = await buscarLuzNoMapa(params.codigo);
  if (!data) return { title: "LuzNoMapa · DadoSabedoria" };
  const local = data.nome + (data.uf ? ` (${data.uf})` : "");
  return {
    title: `LuzNoMapa — ${local} · DadoSabedoria`,
    description: `Qualidade do fornecimento de energia elétrica em ${local}: DEC e FEC da ANEEL.`,
  };
}

const ROTULOS_NIVEL: Record<NivelEnergia, string> = {
  confiavel: "Confiável",
  regular: "Regular",
  fragil: "Frágil",
  sem_dado: "Sem dados disponíveis",
};
const CORES_NIVEL: Record<NivelEnergia, string> = {
  confiavel: "#16a34a",
  regular: "#b45309",
  fragil: "#dc2626",
  sem_dado: "#6b7280",
};

function formatarHoras(n: number | null): string {
  if (n === null) return "—";
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + " h/ano";
}

function formatarFreq(n: number | null): string {
  if (n === null) return "—";
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + " interrupções/ano";
}

function BlocoEnergia({
  label,
  valor,
  formatado,
  nivel,
}: {
  label: string;
  valor: number | null;
  formatado: string;
  nivel: NivelEnergia;
}) {
  const cor = CORES_NIVEL[nivel];
  return (
    <div className="giro-bloco">
      <p className="giro-label">{label}</p>
      {valor !== null ? (
        <p className="giro-numero">
          <strong>{formatado}</strong>
        </p>
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

export default async function LuzNoMapaPage({ params }: { params: { codigo: string } }) {
  const lnm = await buscarLuzNoMapa(params.codigo);
  if (!lnm) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href={`/municipio/${lnm.codigo_ibge}`} className="voltar">
        ← Ver o panorama do município
      </Link>
      <p className="pulso-pergunta" style={{ color: "#b45309" }}>
        ⚡ Dado demo — forma a confirmar na 1ª busca real (ANEEL, SANE-04)
      </p>
      <p className="pulso-pergunta">LuzNoMapa — qualidade da energia elétrica</p>
      <h1>
        {lnm.nome}
        {lnm.uf ? ` · ${lnm.uf}` : ""}
      </h1>
      {lnm.periodo && (
        <p className="giro-populacao">Exercício de referência: {lnm.periodo}</p>
      )}

      <div className="giro-painel">
        <BlocoEnergia
          label={`DEC — duração das interrupções${lnm.periodo ? ` · ${lnm.periodo}` : ""}`}
          valor={lnm.dec}
          formatado={formatarHoras(lnm.dec)}
          nivel={lnm.nivel_dec}
        />
        <BlocoEnergia
          label={`FEC — frequência das interrupções${lnm.periodo ? ` · ${lnm.periodo}` : ""}`}
          valor={lnm.fec}
          formatado={formatarFreq(lnm.fec)}
          nivel={lnm.nivel_fec}
        />
      </div>

      <section className="pulso-nota">
        <h2>Como ler estes números</h2>
        <p>{lnm.nota}</p>
      </section>

      {(lnm.meta_dec || lnm.meta_fec) && (
        <dl className="giro-meta">
          {lnm.meta_dec && (
            <div>
              <dt>Fonte (DEC)</dt>
              <dd>
                {lnm.meta_dec.fonte} · {lnm.meta_dec.metodologia}
                {lnm.meta_dec.lag_tipico_dias != null
                  ? ` · atraso ~${lnm.meta_dec.lag_tipico_dias} dias`
                  : ""}
                {" "}· {lnm.meta_dec.licenca}
              </dd>
            </div>
          )}
          {lnm.meta_fec && (
            <div>
              <dt>Fonte (FEC)</dt>
              <dd>
                {lnm.meta_fec.fonte} · {lnm.meta_fec.metodologia}
                {lnm.meta_fec.lag_tipico_dias != null
                  ? ` · atraso ~${lnm.meta_fec.lag_tipico_dias} dias`
                  : ""}
                {" "}· {lnm.meta_fec.licenca}
              </dd>
            </div>
          )}
        </dl>
      )}

      <p style={{ marginTop: "16px" }}>
        <Link href={`/municipio/${lnm.codigo_ibge}`}>Ver o panorama completo do município →</Link>
      </p>

      <ProdutosRelacionados slug="luz-no-mapa" codigoIbge={lnm.codigo_ibge} />
    </main>
  );
}
