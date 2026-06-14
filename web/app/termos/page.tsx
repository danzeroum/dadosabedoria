import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Termos de uso · DadoSabedoria",
  description:
    "Termos de uso e licença de dados por fonte. Indicadores são descritivos; a licença de cada origem prevalece.",
};

export default function TermosPage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Termos de uso</h1>
      <p className="atualizado">
        Atualizado em <time dateTime="2026-06-13">13 de junho de 2026</time>
      </p>

      <div className="revisao">
        ⚠ <strong>[REVISÃO JURÍDICA]</strong> — texto-base de handoff. Validar com jurídico antes de
        publicar.
      </div>

      <h2>1. O serviço</h2>
      <p>
        A DadoSabedoria organiza dados públicos abertos e os apresenta com proveniência. Indicadores
        são <strong>descritivos</strong> — contexto para perguntar, não veredito nem aconselhamento.
        Não substituem fonte oficial para fins legais.
      </p>

      <h2>2. Uso aceitável</h2>
      <ul>
        <li>
          Você pode consultar, citar e construir sobre os dados, respeitando a licença de cada
          fonte.
        </li>
        <li>
          Não tente reidentificar indivíduos a partir de dados agregados — além de inútil pela
          supressão, é vedado.
        </li>
        <li>
          Não sobrecarregue a API além dos limites do seu plano; uso abusivo pode ser bloqueado.
        </li>
      </ul>

      <h2>3. Licença dos dados (por fonte)</h2>
      <p>
        Cada fonte traz sua própria licença e regra de redistribuição — declaradas na tela de{" "}
        <Link href="/fontes">Fontes &amp; confiança</Link>. Em resumo:
      </p>
      <ul>
        <li>
          <strong>Uso comercial / redistribuição permitidos</strong> em parte das fontes — verifique
          o selo na ficha de cada uma.
        </li>
        <li>
          <strong>Atribuição</strong> à fonte original (IBGE, DATASUS, etc.) e à DadoSabedoria é
          exigida ao redistribuir.
        </li>
        <li>
          Onde a fonte <strong>restringe</strong> uso comercial ou redistribuição, a restrição
          prevalece sobre estes termos.
        </li>
      </ul>

      <h2>4. Sem garantia</h2>
      <p>
        Os dados são fornecidos “como estão”, com as limitações declaradas (subnotificação, atraso,
        cobertura parcial). Não garantimos disponibilidade ininterrupta nem ausência de erro de
        fonte upstream.
      </p>

      <h2>5. Privacidade</h2>
      <p>
        O tratamento de dados pessoais (só para alertas/login) é regido pela{" "}
        <Link href="/privacidade">Política de Privacidade</Link>, parte integrante destes termos.
      </p>

      <h2>6. Mudanças</h2>
      <p>
        Podemos atualizar estes termos; mudanças relevantes serão sinalizadas. O uso continuado após
        a atualização implica concordância.
      </p>

      <div className="honesto">
        <strong>O espírito, em uma linha.</strong> Use os dados livremente para entender o Brasil,
        dê crédito à fonte, respeite a licença de cada origem e não tente desfazer a proteção de quem
        não pode se defender.
      </div>
    </main>
  );
}
