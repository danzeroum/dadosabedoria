import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "API & Desenvolvedores · DadoSabedoria",
  description:
    "A API pública com proveniência: endpoints /v1 de leitura abertos e grátis; tier profundo (lote e cota) com chave. Toda resposta carrega a fonte.",
};

// Domínio de API ilustrativo para os exemplos curl (o base real é configurado por ambiente).
const API = "https://api.dadosabedoria.org/v1";

export default function DesenvolvedoresPage() {
  return (
    <main className="pagina">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>API &amp; Desenvolvedores</h1>
      <p className="home-lead dev-intro">
        Tudo que o site mostra vem de uma API pública com proveniência. Os endpoints{" "}
        <code>/v1/*</code> de leitura são abertos e grátis; o tier profundo (lote e cota) usa chave.
        Toda resposta carrega a fonte.
      </p>
      <p className="migalha">
        <Link href="/desenvolvedores/planos">Planos &amp; preços</Link> ·{" "}
        <Link href="/desenvolvedores/cota">Painel de cota</Link> ·{" "}
        <Link href="/fontes">Licenças por fonte</Link>
      </p>

      <h2>Base &amp; autenticação</h2>
      <div className="endpoint">
        <div className="endpoint-cab">
          <span className="metodo metodo-get">BASE</span>
          <span className="endpoint-rota">{API}</span>
        </div>
        <div className="endpoint-corpo">
          <p>
            Endpoints de leitura são públicos. O tier profundo exige a chave no header — nunca em
            querystring nem no bundle do front.
          </p>
          <code className="bloco-codigo">{`# leitura pública — sem chave
curl ${API}/fontes

# tier profundo — chave no header
curl ${API}/quota \\
  -H "Authorization: Bearer SUA_CHAVE"`}</code>
        </div>
      </div>

      <h2>Endpoints públicos</h2>
      <div className="endpoint">
        <div className="endpoint-cab">
          <span className="metodo metodo-get">GET</span>
          <span className="endpoint-rota">/v1/fontes</span>
          <span className="endpoint-tag">público</span>
        </div>
        <div className="endpoint-corpo">
          <p>
            Catálogo de fontes do acervo: domínios, cadência, atraso típico, licença e base legal.
          </p>
          <code className="bloco-codigo">{`curl ${API}/fontes`}</code>
        </div>
      </div>
      <div className="endpoint">
        <div className="endpoint-cab">
          <span className="metodo metodo-get">GET</span>
          <span className="endpoint-rota">/v1/territorios/{"{codigo}"}/panorama</span>
          <span className="endpoint-tag">público</span>
        </div>
        <div className="endpoint-corpo">
          <p>
            Panorama de um município pelo código IBGE — todos os indicadores do acervo, com
            proveniência. O protegido vem como protegido (<code>null</code> + motivo), nunca como
            zero.
          </p>
          <code className="bloco-codigo">{`curl ${API}/territorios/3550308/panorama`}</code>
        </div>
      </div>
      <div className="endpoint">
        <div className="endpoint-cab">
          <span className="metodo metodo-get">GET</span>
          <span className="endpoint-rota">/v1/mapa/ivm</span>
          <span className="endpoint-tag">público</span>
        </div>
        <div className="endpoint-corpo">
          <p>
            IVM por UF como GeoJSON (<code>FeatureCollection</code>). Onde falta a malha geométrica,
            a tela degrada para cartograma de tiles.
          </p>
          <code className="bloco-codigo">{`curl "${API}/mapa/ivm?uf=SP"`}</code>
        </div>
      </div>

      <h2>
        Tier profundo{" "}
        <span
          style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--cor-texto-suave)" }}
        >
          requer chave
        </span>
      </h2>
      <div className="endpoint">
        <div className="endpoint-cab">
          <span className="metodo metodo-get">GET</span>
          <span className="endpoint-rota">/v1/quota</span>
          <span className="endpoint-tag">chave</span>
        </div>
        <div className="endpoint-corpo">
          <p>
            Consumo da sua chave na janela atual (lê sem debitar). Alimenta o{" "}
            <Link href="/desenvolvedores/cota">Painel de cota</Link>.
          </p>
          <code className="bloco-codigo">{`curl ${API}/quota \\
  -H "Authorization: Bearer SUA_CHAVE"

# 200 →
{ "limite": 1000, "usado": 342, "restante": 658, "reset": 1718000400 }`}</code>
        </div>
      </div>
      <div className="endpoint">
        <div className="endpoint-cab">
          <span className="metodo metodo-post">POST</span>
          <span className="endpoint-rota">/v1/consultas-lote</span>
          <span className="endpoint-tag">chave</span>
        </div>
        <div className="endpoint-corpo">
          <p>
            Até <strong>50</strong> consultas por requisição — vários municípios × indicadores de
            uma vez. Cada item da resposta mantém sua própria proveniência e estado de supressão.
          </p>
          <code className="bloco-codigo">{`curl -X POST ${API}/consultas-lote \\
  -H "Authorization: Bearer SUA_CHAVE" \\
  -H "Content-Type: application/json" \\
  -d '{ "consultas": [
        { "indicador": "trabalho.emprego.saldo_caged", "territorio": "3550308" },
        { "indicador": "credito.operacoes.saldo_total", "territorio": "3304557" }
      ] }'`}</code>
        </div>
      </div>

      <div className="honesto">
        <strong>Contrato de honestidade da API.</strong> Todo número vem com <code>fonte</code>,{" "}
        <code>periodo</code> e <code>lag</code>. Dado suprimido por privacidade volta como{" "}
        <code>null</code> com <code>motivo_supressao</code> (k-anonimato) — nunca como zero. Sem
        cobertura é <code>null</code> sem supressão. Sua aplicação deve distinguir os dois.
      </div>

      <p className="metodologia">
        Limites, preços e o que cada plano libera estão em{" "}
        <Link href="/desenvolvedores/planos">Planos &amp; preços</Link>. As licenças de
        redistribuição variam por fonte — confira em <Link href="/fontes">Fontes &amp; confiança</Link>.
      </p>
    </main>
  );
}
