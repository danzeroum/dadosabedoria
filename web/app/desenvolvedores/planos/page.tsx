import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Planos & preços · DadoSabedoria",
  description:
    "Open-core: a leitura pública é grátis para sempre. O que custa é a escala — lote, cota maior e SLA — que sustenta a esteira.",
};

export default function PlanosPage() {
  return (
    <main className="pagina">
      <Link href="/desenvolvedores" className="voltar">
        ← API &amp; Desenvolvedores
      </Link>
      <h1>Planos &amp; preços</h1>
      <p className="home-lead">
        Modelo <strong>open-core</strong>: a leitura pública é grátis para sempre — é dado público
        devolvido legível. O que custa é a escala (lote, cota maior, SLA), que sustenta a esteira.
      </p>

      <div className="planos">
        <div className="plano">
          <p className="plano-nome">Público</p>
          <p className="plano-preco">Grátis</p>
          <p className="plano-desc">Para o cidadão, o jornalista e quem está experimentando.</p>
          <ul className="plano-lista">
            <li>
              Todos os endpoints <code>/v1/*</code> de leitura
            </li>
            <li>Proveniência e licença em cada resposta</li>
            <li>Sem chave, sem cadastro</li>
            <li className="nao">Sem consultas em lote</li>
            <li className="nao">Limite por IP (uso justo)</li>
          </ul>
          <Link className="botao botao-secundario" href="/desenvolvedores">
            Ver endpoints
          </Link>
        </div>

        <div className="plano plano-destaque">
          <p className="plano-nome">Profundo</p>
          <p className="plano-preco">
            sob consulta <small>/ mês</small>
          </p>
          <p className="plano-desc">Para produtos e painéis que consomem o acervo em escala.</p>
          <ul className="plano-lista">
            <li>Tudo do Público</li>
            <li>
              <strong>1.000 req/h</strong> por chave
            </li>
            <li>
              Consultas em lote (até <strong>50</strong> por requisição)
            </li>
            <li>Painel de cota em tempo real</li>
            <li>Suporte por e-mail</li>
          </ul>
          <Link className="botao botao-primario" href="/entrar">
            Obter uma chave
          </Link>
        </div>

        <div className="plano">
          <p className="plano-nome">Institucional</p>
          <p className="plano-preco">sob consulta</p>
          <p className="plano-desc">
            Para órgãos públicos, universidades e uso de missão crítica.
          </p>
          <ul className="plano-lista">
            <li>Tudo do Profundo</li>
            <li>Cota e lote sob medida</li>
            <li>SLA e canal dedicado</li>
            <li>Apoio à integração</li>
          </ul>
          <a className="botao botao-secundario" href="mailto:institucional@dadosabedoria.org">
            Falar com a equipe
          </a>
        </div>
      </div>

      <div className="honesto">
        <strong>O que nunca cobramos.</strong> O dado público é, e continua, público. Não há paywall
        sobre a verdade — o que monetizamos é conveniência e escala (lote, cota maior, SLA), nunca o
        acesso ao número em si.
      </div>

      <p className="metodologia">
        Limites e janelas valem por chave e podem mudar; o{" "}
        <Link href="/desenvolvedores/cota">Painel de cota</Link> mostra seu consumo real.
        Redistribuir dados depende da licença da fonte — veja{" "}
        <Link href="/fontes">Fontes &amp; confiança</Link>.
      </p>
    </main>
  );
}
