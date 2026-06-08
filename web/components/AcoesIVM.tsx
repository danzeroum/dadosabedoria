import {
  citacaoAbntIvm,
  linkEmail,
  linkWhatsapp,
  textoCompartilharIvm,
  urlCanonicaIvm,
} from "../lib/agir";
import type { IVMItem, MetaIVM } from "../lib/types";

// Superfície de "agir" do IVM — mesmo primitivo do OndeFoi (`lib/agir.ts` + estilos `.acoes`/`.acao`),
// sem forkar. `<details>` nativos, cliente-zero. O IVM é índice COMPARATIVO de vulnerabilidade (não
// veredito nem ranking) — a copy preserva isso em cada ação. "Avise-me" prepara o lugar (auth do
// cidadão é gate do dono); "a quem levar" leva ao canal real (Fala.BR), foco no território.
export function AcoesIVM({ item, meta }: { item: IVMItem; meta: MetaIVM }) {
  const url = urlCanonicaIvm(item.codigo_ibge);
  const texto = textoCompartilharIvm(item);
  const citacao = citacaoAbntIvm(item, meta);
  const assunto = `Vulnerabilidade (IVM) de ${item.nome}`;
  const buscaOuvidoria = `https://www.google.com/search?q=${encodeURIComponent(
    `ouvidoria câmara prefeitura ${item.nome}${item.uf ? ` ${item.uf}` : ""}`,
  )}`;

  return (
    <section className="acoes" aria-label="O que fazer com este dado">
      <h2>Leve este dado adiante</h2>
      <p className="of-sub">
        Vulnerabilidade alta é um sinal para <strong>priorizar política</strong>, não um veredito
        sobre a gestão. Compartilhe, cite com proveniência e leve a quem decide.
      </p>

      <details className="acao">
        <summary>Compartilhar</summary>
        <div className="acao-corpo">
          <p className="acao-texto">{texto}</p>
          <p className="acoes-links">
            <a href={linkWhatsapp(texto, url)} rel="noopener noreferrer">
              Compartilhar no WhatsApp
            </a>
            <a href={linkEmail(assunto, `${texto}\n\n${url}`)}>Enviar por e-mail</a>
          </p>
          <p className="acao-rotulo">Link</p>
          <code className="acao-bloco">{url}</code>
        </div>
      </details>

      <details className="acao">
        <summary>Exportar com citação (ABNT)</summary>
        <div className="acao-corpo">
          <p>
            Todo uso sai <strong>com citação e proveniência</strong> — pronto para reportagem ou
            parecer.
          </p>
          <p className="acao-rotulo">Citação sugerida (ABNT)</p>
          <code className="acao-bloco">{citacao}</code>
          <p className="acao-nota">
            Selecione e copie o texto acima. Para a série e os subíndices em JSON com proveniência,
            use a API pública <code>/v1/ivm/{item.codigo_ibge}</code>.
          </p>
        </div>
      </details>

      <details className="acao">
        <summary>Avise-me se piorar</summary>
        <div className="acao-corpo">
          <p>
            Receba um aviso quando o IVM de <strong>{item.nome}</strong> mudar de faixa — por
            exemplo, ao entrar no <em>vermelho</em>.
          </p>
          <p className="acao-privacidade">
            <strong>LGPD por desenho.</strong> Seu contato ficaria num cofre isolado (schema{" "}
            <code>app</code>), cifrado e nunca cruzado com o dado público — o alerta usa só o evento
            do território, nunca você.
          </p>
          <p className="acao-nota">
            A assinatura chega com a autenticação do cidadão (próxima fatia) — o lugar já está
            preparado.
          </p>
        </div>
      </details>

      <details className="acao">
        <summary>A quem levar</summary>
        <div className="acao-corpo">
          <p>
            Leve o panorama de vulnerabilidade a quem decide — vereadores, secretarias, ouvidoria —
            para <strong>priorizar política pública</strong>. É sinal comparativo para priorizar,
            não sentença.
          </p>
          <p className="acoes-links">
            <a href="https://falabr.cgu.gov.br/" target="_blank" rel="noopener noreferrer">
              Pedido de informação / ouvidoria (Fala.BR)
              <span className="sr-only"> (abre em nova aba)</span>
            </a>
            <a href={buscaOuvidoria} target="_blank" rel="noopener noreferrer">
              Ouvidoria/câmara de {item.nome}
              <span className="sr-only"> (abre em nova aba)</span>
            </a>
          </p>
          <p className="acao-nota">
            O link direto por município chega com o cadastro gov.br das ouvidorias.
          </p>
        </div>
      </details>
    </section>
  );
}
