import {
  citacaoAbntOndeFoi,
  linkEmail,
  linkWhatsapp,
  textoCompartilharOndeFoi,
  urlCanonicaOndeFoi,
} from "../lib/agir";
import type { OndeFoiProduto } from "../lib/types";

// Superfície de "agir" (etapa final do funil do OndeFoi — handoff de design): levar o dado adiante
// sem JS no cliente, com os gates degradando honestamente. São <details> nativos (acessíveis,
// operáveis por teclado), no mesmo idioma do "O que é execução". Compartilhar e citar já funcionam;
// "avise-me" prepara o lugar (a autenticação do cidadão é gate do dono); "a quem cobrar" leva ao
// canal real de LAI/ouvidoria (Fala.BR), sem expor pessoas — o foco é o território.
export function AcoesOndeFoi({ d }: { d: OndeFoiProduto }) {
  const url = urlCanonicaOndeFoi(d.codigo_ibge);
  const texto = textoCompartilharOndeFoi(d);
  const citacao = citacaoAbntOndeFoi(d);
  const assunto = `Onde foi o dinheiro de ${d.nome}?`;
  const buscaOuvidoria = `https://www.google.com/search?q=${encodeURIComponent(
    `ouvidoria câmara prefeitura ${d.nome} ${d.uf}`,
  )}`;

  return (
    <section className="of-acoes" aria-label="O que fazer com este dado">
      <h2>Leve este dado adiante</h2>
      <p className="of-sub">
        O número sozinho não cobra — você cobra. Compartilhe, cite com proveniência e leve à
        ouvidoria. Sem expor pessoas: o foco é o território, não quem.
      </p>

      <details className="of-acao">
        <summary>Compartilhar</summary>
        <div className="of-acao-corpo">
          <p className="of-acao-texto">{texto}</p>
          <p className="of-acoes-links">
            <a href={linkWhatsapp(texto, url)} rel="noopener noreferrer">
              Compartilhar no WhatsApp
            </a>
            <a href={linkEmail(assunto, `${texto}\n\n${url}`)}>Enviar por e-mail</a>
          </p>
          <p className="of-acao-rotulo">Link</p>
          <code className="of-acao-bloco">{url}</code>
        </div>
      </details>

      <details className="of-acao">
        <summary>Exportar com citação (ABNT)</summary>
        <div className="of-acao-corpo">
          <p>
            Todo uso sai <strong>com citação e proveniência</strong> — pronto para reportagem ou
            parecer.
          </p>
          <p className="of-acao-rotulo">Citação sugerida (ABNT)</p>
          <code className="of-acao-bloco">{citacao}</code>
          <p className="of-acao-nota">
            Selecione e copie o texto acima. Para os dados em JSON com proveniência, use a API
            pública <code>/v1/onde-foi/{d.codigo_ibge}</code>.
          </p>
        </div>
      </details>

      <details className="of-acao">
        <summary>Avise-me se travar</summary>
        <div className="of-acao-corpo">
          <p>
            Receba um aviso quando a execução de <strong>{d.nome}</strong> mudar de faixa — por
            exemplo, ao cair para <em>liquidou pouco</em>.
          </p>
          <p className="of-acao-privacidade">
            <strong>LGPD por desenho.</strong> Seu contato ficaria num cofre isolado (schema{" "}
            <code>app</code>), cifrado e nunca cruzado com o dado público — o alerta usa só o evento
            do território, nunca você.
          </p>
          <p className="of-acao-nota">
            A assinatura chega com a autenticação do cidadão (próxima fatia) — o lugar já está
            preparado.
          </p>
        </div>
      </details>

      <details className="of-acao">
        <summary>A quem cobrar</summary>
        <div className="of-acao-corpo">
          <p>
            Leve a execução orçamentária a quem decide e pergunte <strong>por que travou</strong> ou{" "}
            <strong>se virou serviço</strong>. Execução não é entrega — a pergunta é legítima.
          </p>
          <p className="of-acoes-links">
            <a href="https://falabr.cgu.gov.br/" target="_blank" rel="noopener noreferrer">
              Pedido de informação / ouvidoria (Fala.BR)
              <span className="sr-only"> (abre em nova aba)</span>
            </a>
            <a href={buscaOuvidoria} target="_blank" rel="noopener noreferrer">
              Ouvidoria/câmara de {d.nome}
              <span className="sr-only"> (abre em nova aba)</span>
            </a>
          </p>
          <p className="of-acao-nota">
            O link direto por município chega com o cadastro gov.br das ouvidorias.
          </p>
        </div>
      </details>
    </section>
  );
}
