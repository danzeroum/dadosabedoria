import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Metodologia · DadoSabedoria",
  description:
    "Como cada número é construído, protegido e datado: grão território × período, k-anonimato, IVM, proveniência, honestidade editorial e IA ancorada.",
};

export default function MetodologiaPage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Metodologia</h1>
      <p className="home-lead">
        Como cada número é construído, protegido e datado. Esta página é a âncora cruzada — cada
        produto aponta para a seção que explica o seu cálculo.
      </p>

      <h2>1. O grão: território × período</h2>
      <p>
        Todo indicador é agregado por município e período (mês, ano ou exercício, conforme a fonte).
        Nunca por pessoa. Isso é uma escolha de arquitetura: o que não existe no banco não pode
        vazar nem ser cruzado para reidentificar ninguém.
      </p>

      <h2>2. Supressão por privacidade (k-anonimato)</h2>
      <p>
        Quando a célula vem de origem sensível (saúde, sobretudo) e tem contagem pequena —
        tipicamente <strong>menos de 5</strong> —, o valor é suprimido <em>antes de gravar</em>. A
        tela mostra um estado honesto, nunca o número por baixo e nunca um zero falso:
      </p>
      <ul>
        <li>
          <span className="estado-chip estado-suprimido">🔒 Protegido</span> — havia dado, mas é
          pequeno demais para publicar sem risco de reidentificação.
        </li>
        <li>
          <span className="estado-chip">○ Sem cobertura</span> — a fonte não reporta este
          território/período. Ausência de dado ≠ ausência do fato.
        </li>
      </ul>
      <p>A distinção entre os dois estados é deliberada e nunca colapsa em “0”.</p>

      <h2>3. O IVM — índice de vulnerabilidade municipal</h2>
      <p>
        O IVM resume emprego, finanças e saúde num só sinal semafórico (verde → vermelho). É um{" "}
        <strong>composto descritivo</strong>, não um diagnóstico: aponta onde olhar, não o que
        concluir. Cada subíndice mantém sua fonte e período próprios, e o que é protegido entra no
        composto como protegido — não como zero.
      </p>

      <h2>4. Proveniência</h2>
      <p>
        Cada indicador carrega <strong>fonte</strong>, <strong>método</strong> e{" "}
        <strong>atraso típico</strong> (lag). O selo de confiança consolida origem, licença e
        frescor em cada tela; a página de <Link href="/fontes">Fontes</Link> é a vista agregada.
        Cadência e atraso são típicos da fonte — não garantia de tempo real.
      </p>

      <h2>5. Honestidade editorial</h2>
      <p>O vocabulário do projeto é deliberado para não confundir o leitor:</p>
      <ul>
        <li>
          <strong>Execução ≠ serviço.</strong> Liquidar uma despesa não é entregar a obra. Empenhar
          não é liquidar.
        </li>
        <li>
          <strong>Fluxo é volátil.</strong> Saldos mensais (CAGED) oscilam; a tendência merece a
          pergunta, não o pânico.
        </li>
        <li>
          <strong>Demonstração é demonstração.</strong> Quando a esteira existe mas o dado real
          ainda não fluiu, a tela diz isso.
        </li>
      </ul>

      <h2>6. IA ancorada</h2>
      <p>
        A resposta em linguagem natural só afirma o que o acervo sustenta e{" "}
        <strong>cita a fonte</strong>. Sem dado, abstém-se — não inventa número nem causalidade. A
        recuperação é restrita ao repositório; o modelo não “sabe” nada fora dele.
      </p>

      <div className="honesto">
        <strong>Limitações conhecidas, declaradas.</strong> Subnotificação em vigilância (SINAN),
        defasagem de meses em várias fontes, cobertura parcial do PNCP, e o mapa do IVM ainda em
        cartograma (falta a malha geométrica do IBGE no backend — limitação, não erro). Preferimos
        declarar a limitação a escondê-la.
      </div>

      <p className="metodologia">
        Cada produto traz sua nota metodológica específica na própria tela. Esta página é o tronco
        comum; os galhos vivem em <Link href="/produtos">cada produto</Link>.
      </p>
    </main>
  );
}
