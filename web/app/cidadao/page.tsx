import type { Metadata } from "next";
import Link from "next/link";

import { PortaoAuth } from "../../components/PortaoAuth";

export const metadata: Metadata = {
  title: "Área do cidadão · DadoSabedoria",
  description:
    "Perfil, alertas “Avise-me” e gestão de consentimento (LGPD). Requer login gov.br — prévia desenhada, inerte até o gate abrir.",
};

// Prévia inerte (mostrada enquanto não há sessão): o lugar já está preparado, nada é gravado.
function Previa() {
  return (
    <>
      <h2>Avise-me</h2>
      <p>
        Receba um alerta quando um indicador do seu município mudar de faixa (ex.: o IVM virar
        amarelo, o saldo do CAGED ficar negativo). Evolução do disclosure que hoje vive no OndeFoi.
      </p>
      <div className="toggle-fake" aria-disabled="true">
        <span>
          Alertar quando o <strong>IVM</strong> de São Paulo mudar de faixa
        </span>
        <span className="toggle-pino" role="img" aria-label="desligado (requer login)" />
      </div>
      <div className="toggle-fake" aria-disabled="true">
        <span>
          Alertar sobre o <strong>saldo de emprego</strong> (Pulso Produtivo)
        </span>
        <span className="toggle-pino" role="img" aria-label="desligado (requer login)" />
      </div>

      <h2>Meus dados &amp; consentimento</h2>
      <p>
        Veja e revogue, a qualquer momento, o consentimento dado para alertas. Seu contato vive num
        schema isolado — detalhe na <Link href="/privacidade">Privacidade</Link>.
      </p>
      <div className="toggle-fake" aria-disabled="true">
        <span>
          Consinto receber alertas por <strong>e-mail</strong>
        </span>
        <span className="toggle-pino" role="img" aria-label="desligado (requer login)" />
      </div>
      <p className="metodologia" style={{ marginTop: "14px" }}>
        Quando o login ligar, aqui também aparecem “baixar meus dados” e “apagar minha conta” —
        direitos da LGPD por construção, não por pedido.
      </p>

      <div
        className="honesto"
        style={{
          background: "var(--cor-fundo)",
          borderColor: "var(--cor-borda)",
          color: "var(--cor-texto-suave)",
        }}
      >
        <strong style={{ color: "var(--cor-texto)" }}>Nada coletado ainda.</strong> Enquanto o
        gov.br não liga, esta tela não grava nada — os controles acima são prévia inerte.
        Honestidade: não pedimos o que ainda não podemos proteger pelo fluxo completo.
      </div>
    </>
  );
}

export default function CidadaoPage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Área do cidadão</h1>
      <PortaoAuth previa={<Previa />}>
        {(sessao) => (
          <p className="home-lead">
            Olá, {sessao.nome}. Gerencie seus alertas e seu consentimento abaixo.
          </p>
        )}
      </PortaoAuth>
    </main>
  );
}
