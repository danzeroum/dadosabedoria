import Link from "next/link";
import { notFound } from "next/navigation";

import { buscarIndicador } from "../../../lib/api";

export const dynamic = "force-dynamic";

const ROTULO_DOMINIO: Record<string, string> = {
  trabalho: "Trabalho",
  credito: "Crédito",
  saude: "Saúde",
  financas: "Finanças",
  educacao: "Educação",
  compras: "Compras",
};

const ROTULO_CADENCIA: Record<string, string> = {
  diaria: "diária",
  semanal: "semanal",
  mensal: "mensal",
  trimestral: "trimestral",
  anual: "anual",
  irregular: "irregular",
};

const ROTULO_POLARIDADE: Record<string, string> = {
  maior_melhor: "maior é melhor",
  menor_melhor: "menor é melhor",
  neutra: "neutro — descritivo, sem juízo de bom/ruim",
};

const ROTULO_NIVEL: Record<string, string> = {
  municipio: "município",
  uf: "unidade federativa",
  regiao: "região",
  pais: "país",
};

export default async function IndicadorPage({ params }: { params: { codigo: string } }) {
  const ind = await buscarIndicador(params.codigo);
  if (!ind) {
    notFound();
  }

  return (
    <main className="pagina">
      <Link href="/fontes" className="voltar">
        ← Fontes &amp; confiança
      </Link>
      <p className="pulso-pergunta">Ficha técnica do indicador</p>
      <h1>{ind.nome}</h1>
      <p className="ficha-dominio">
        {ROTULO_DOMINIO[ind.dominio] ?? ind.dominio}
        {ind.subdominio ? ` · ${ind.subdominio}` : ""} · <code>{ind.codigo}</code>
      </p>
      <p className="home-lead">{ind.descricao}</p>

      <dl className="ficha-grid">
        <div className="ficha-larga">
          <dt>Como é calculado</dt>
          <dd>{ind.metodologia}</dd>
        </div>
        <div>
          <dt>Unidade</dt>
          <dd>{ind.unidade}</dd>
        </div>
        <div>
          <dt>Polaridade</dt>
          <dd>{ROTULO_POLARIDADE[ind.polaridade] ?? ind.polaridade}</dd>
        </div>
        <div>
          <dt>Atualização</dt>
          <dd>
            {ROTULO_CADENCIA[ind.atualizacao] ?? ind.atualizacao}
            {ind.meta.lag_tipico_dias != null
              ? ` · atraso típico ~${ind.meta.lag_tipico_dias} dias`
              : ""}
          </dd>
        </div>
        <div>
          <dt>Grão mínimo</dt>
          <dd>{ROTULO_NIVEL[ind.nivel_minimo_agregacao] ?? ind.nivel_minimo_agregacao}</dd>
        </div>
        <div>
          <dt>Versão da metodologia</dt>
          <dd>{ind.versao_metodologia}</dd>
        </div>
        <div>
          <dt>Fonte</dt>
          <dd>
            {ind.meta.fonte} · licença {ind.meta.licenca}
          </dd>
        </div>
      </dl>

      <p className="metodologia">
        Este é o <strong>como</strong> do número — o que ele mede e de onde vem. Para ver os{" "}
        <strong>valores</strong>, abra o panorama de um município; o protegido por privacidade sempre
        aparece protegido, nunca o número por baixo. Veja todas as fontes em{" "}
        <Link href="/fontes">Fontes &amp; confiança</Link>.
      </p>
    </main>
  );
}
