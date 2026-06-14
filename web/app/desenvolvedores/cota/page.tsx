import type { Metadata } from "next";
import Link from "next/link";

import { CotaForm } from "./CotaForm";

export const metadata: Metadata = {
  title: "Painel de cota · DadoSabedoria",
  description:
    "Consumo da sua chave de API na janela atual, lido de GET /v1/quota. A chave é processada no servidor — nunca vai para o navegador.",
};

export default function CotaPage() {
  return (
    <main className="pagina">
      <Link href="/desenvolvedores" className="voltar">
        ← API &amp; Desenvolvedores
      </Link>
      <h1>Painel de cota</h1>
      <p className="home-lead">
        Consumo da sua chave na janela atual, lido de <code>GET /v1/quota</code>. A chave é
        processada no servidor — nunca vai para o navegador.
      </p>

      <CotaForm />

      <div className="honesto">
        <strong>Segurança por construção.</strong> A consulta a <code>/v1/quota</code> roda numa
        Server Action: a chave fica server-side e jamais entra no bundle do cliente. O front só
        recebe os números agregados de consumo.
      </div>
    </main>
  );
}
