import type { Metadata } from "next";
import Link from "next/link";

import { AUTH_HABILITADO } from "../../lib/auth";

export const metadata: Metadata = {
  title: "Entrar · DadoSabedoria",
  description:
    "Login pela conta gov.br — para receber alertas e gerir consentimento, nunca para acessar dados públicos (esses são abertos a todos, sem conta).",
};

export default function EntrarPage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Entrar</h1>
      <p className="home-lead">
        O login será pela conta <strong>gov.br</strong> — para receber alertas e gerir seu
        consentimento, nunca para acessar dados públicos (esses são abertos a todos, sem conta).
      </p>

      <div style={{ maxWidth: "420px", margin: "22px 0" }}>
        <button
          className="gov-botao"
          type="button"
          disabled={!AUTH_HABILITADO}
          aria-disabled={!AUTH_HABILITADO}
        >
          Entrar com <span className="gov-marca">gov.br</span>
        </button>
        {!AUTH_HABILITADO ? (
          <p className="gov-nota">Botão desabilitado — a integração OIDC ainda não foi liberada.</p>
        ) : null}
      </div>

      {!AUTH_HABILITADO ? (
        <div className="portao" role="note">
          <span className="portao-icone" aria-hidden="true">
            🔒
          </span>
          <div>
            <strong>Ainda não liberado.</strong> A entrada por gov.br depende de uma habilitação
            externa (OIDC) que ainda não está no ar. O lugar já está preparado: quando o gate abrir,
            este botão funciona e a área do cidadão liga junto — sem redesenho.
          </div>
        </div>
      ) : null}

      <h2>Enquanto isso, sem login</h2>
      <ul>
        <li>
          Todos os <strong>dados públicos</strong> e os 28 produtos seguem abertos —{" "}
          <Link href="/produtos">explore o catálogo</Link>.
        </li>
        <li>
          A <strong>API de leitura</strong> não exige conta — veja{" "}
          <Link href="/desenvolvedores">Desenvolvedores</Link>.
        </li>
        <li>
          Só <strong>alertas</strong> e <strong>consentimento</strong> aguardam o login — prévia em{" "}
          <Link href="/cidadao">Área do cidadão</Link>.
        </li>
      </ul>

      <p className="metodologia">
        Não pediremos nenhum dado pessoal antes do gov.br estar ativo. Como tratamos contato e
        consentimento está na <Link href="/privacidade">Privacidade</Link>.
      </p>
    </main>
  );
}
