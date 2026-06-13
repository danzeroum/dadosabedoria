import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Sobre · DadoSabedoria",
  description:
    "Inteligência sobre dados públicos brasileiros onde a confiança é o ativo: privacidade por estrutura, proveniência em cada número e qualidade provada a cada commit.",
};

export default function SobrePage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Sobre a DadoSabedoria</h1>
      <p className="home-lead">
        Inteligência sobre dados públicos brasileiros onde a <strong>confiança é o ativo</strong>:
        privacidade por estrutura, proveniência em cada número e qualidade provada a cada commit.
      </p>

      <h2>O Valor Triplo</h2>
      <p>
        Os mesmos dados, lidos com honestidade, servem a três públicos sem trair nenhum: o{" "}
        <strong>cidadão</strong> que quer entender seu município, o <strong>gestor</strong> que
        precisa de evidência para decidir e o <strong>desenvolvedor</strong> que constrói sobre uma
        API com proveniência. Não vendemos o dado de ninguém — organizamos o que já é público e o
        devolvemos legível.
      </p>

      <div className="pilares">
        <div className="pilar">
          <h3>Privacidade estrutural</h3>
          <p>
            O grão é sempre território × período, nunca pessoa. Não há chave de indivíduo. Células
            pequenas demais são suprimidas <em>antes</em> de gravar — a tela mostra um cadeado,
            jamais o número por baixo.
          </p>
        </div>
        <div className="pilar">
          <h3>Proveniência sempre</h3>
          <p>
            Cada indicador carrega fonte, método e atraso. Confiança não como promessa, mas como
            fato verificável a cada consulta — auditável na tela de{" "}
            <Link href="/fontes">Fontes</Link>.
          </p>
        </div>
        <div className="pilar">
          <h3>Qualidade provada</h3>
          <p>
            O que não passa em teste não chega ao ar. A separação de dados pessoais, a supressão e a
            metodologia são verificadas por testes que reprovam o build se a invariante vazar.
          </p>
        </div>
      </div>

      <h2>Como funciona</h2>
      <p>
        Lemos fontes públicas abertas (IBGE, CAGED, DATASUS, SICONFI, INEP, PNCP, SNIS e outras),
        calculamos indicadores no grão municipal, aplicamos supressão de privacidade e publicamos
        cada número com sua origem. Sobre essa base ficam os 24 produtos — cada um uma{" "}
        <Link href="/produtos">pergunta com resposta</Link> — e a IA ancorada, que só afirma o que o
        acervo sustenta.
      </p>

      <div className="honesto">
        <strong>O que não somos.</strong> Não somos um ranking de “melhores” e “piores” municípios,
        nem um veredito sobre gestões. Um número alto ou baixo é um convite à pergunta — execução
        não é serviço, fluxo é volátil, ausência de dado não é ausência de fato. O lugar do
        julgamento é de quem lê.
      </div>

      <p className="metodologia">
        Para o detalhe técnico de cada cálculo, supressão e fonte, veja a{" "}
        <Link href="/metodologia">Metodologia</Link>. Para como tratamos dados pessoais, a{" "}
        <Link href="/privacidade">Privacidade</Link>.
      </p>
    </main>
  );
}
