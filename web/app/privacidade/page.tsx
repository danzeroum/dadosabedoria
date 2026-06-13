import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacidade · DadoSabedoria",
  description:
    "Privacidade por arquitetura (LGPD): grão território × período, schema de dado pessoal isolado e supressão antes de gravar.",
};

export default function PrivacidadePage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Privacidade</h1>
      <p className="atualizado">
        Atualizado em <time dateTime="2026-06-13">13 de junho de 2026</time> · conforme a LGPD (Lei
        nº 13.709/2018)
      </p>

      <div className="revisao">
        ⚠ <strong>[REVISÃO JURÍDICA]</strong> — texto-base de handoff. Toda a linguagem desta página
        precisa de validação por jurídico antes de publicar; os fatos técnicos abaixo refletem a
        arquitetura implementada.
      </div>

      <p className="home-lead">
        A privacidade aqui não é uma promessa no rodapé — é uma escolha de{" "}
        <strong>arquitetura</strong>. Trabalhamos com dados públicos agregados; o pouco dado pessoal
        que existe (contato de quem opta por alertas) vive isolado do resto.
      </p>

      <h2>1. O que processamos</h2>
      <h3>Dados públicos agregados</h3>
      <p>
        A maior parte do que mostramos vem de fontes públicas abertas, sempre no grão{" "}
        <strong>território × período</strong> — nunca por pessoa. Não há identificação de indivíduos
        nesses dados.
      </p>
      <h3>Dado pessoal (apenas se você optar)</h3>
      <p>
        Se você pedir alertas (“Avise-me”) ou criar conta, tratamos o mínimo necessário (e-mail,
        identificador de login gov.br). Esse contato vive num <strong>schema isolado</strong> (
        <code>app</code>) que a camada analítica não consegue ler — uma separação garantida por
        teste que reprova o build se vazar.
      </p>

      <h2>2. Supressão antes de gravar</h2>
      <p>
        Dados de origem sensível (saúde) com contagem pequena são{" "}
        <strong>suprimidos na ingestão</strong>, antes de chegar ao banco de leitura. A consequência
        prática: não existe um “número por baixo do cadeado” para vazar — ele nunca foi gravado. É
        privacidade por estrutura, não por permissão de acesso.
      </p>

      <h2>3. Base legal (LGPD)</h2>
      <ul>
        <li>
          <strong>Dados públicos:</strong> tratamento de dado tornado manifestamente público e
          dados de acesso público (art. 7º, §§ 3º e 4º), com finalidade de transparência e interesse
          público.
        </li>
        <li>
          <strong>Contato para alertas:</strong> <strong>consentimento</strong> do titular (art. 7º,
          I), revogável a qualquer momento.
        </li>
      </ul>

      <h2>4. Seus direitos</h2>
      <p>
        Você pode confirmar a existência de tratamento, acessar, corrigir, e{" "}
        <strong>revogar o consentimento</strong> e apagar o contato a qualquer momento — pela área
        do cidadão, quando o login estiver disponível, ou pelos canais abaixo. Não vendemos nem
        compartilhamos contato com terceiros.
      </p>

      <h2>5. Cookies</h2>
      <p>
        O site funciona sem cookies de rastreamento. Usamos apenas o essencial para sessão e
        preferências; não há perfilamento publicitário.
      </p>

      <h2>6. Contato (Encarregado / DPO)</h2>
      <p>
        Dúvidas ou solicitações sobre seus dados:{" "}
        <a href="mailto:privacidade@dadosabedoria.org">privacidade@dadosabedoria.org</a>{" "}
        <span className="nota">[placeholder — definir canal real com jurídico]</span>.
      </p>

      <div className="honesto">
        <strong>Em uma frase.</strong> Não temos a chave de ninguém: o que é público é agregado, o
        que é sensível é suprimido antes de existir no banco, e o que é seu (contato) fica isolado e
        sob seu controle.
      </div>
    </main>
  );
}
