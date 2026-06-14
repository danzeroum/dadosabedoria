import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Acessibilidade · DadoSabedoria",
  description:
    "Declaração de conformidade WCAG 2.1 AA (ADR-0009): nunca só por cor, contraste AA, foco visível, navegação por teclado e limitações honestas.",
};

export default function AcessibilidadePage() {
  return (
    <main className="pagina legal">
      <Link href="/" className="voltar">
        ← Início
      </Link>
      <h1>Acessibilidade</h1>
      <p className="atualizado">
        Conformidade-alvo: <strong>WCAG 2.1 nível AA</strong> · ADR-0009
      </p>
      <p className="home-lead">
        Dados públicos só são públicos se todo mundo consegue lê-los. A acessibilidade aqui é
        requisito de DS, não enfeite — verificada a cada commit.
      </p>

      <h2>Compromissos</h2>
      <ul>
        <li>
          <strong>Nunca só por cor.</strong> Todo semáforo e nível traz rótulo textual e/ou ícone. A
          cor é reforço redundante.
        </li>
        <li>
          <strong>Contraste AA.</strong> Texto ≥ 4.5:1 sobre o fundo. Os tons de tendência foram
          escurecidos de propósito (verde #15803d, vermelho #b91c1c) para passar no axe/WCAG.
        </li>
        <li>
          <strong>Foco visível.</strong> Contorno de 3px na cor da marca em todo elemento focável (
          <code>:focus-visible</code>).
        </li>
        <li>
          <strong>Navegável por teclado.</strong> Sem armadilhas de foco; os disclosures de “agir”
          são <code>&lt;details&gt;</code> nativos.
        </li>
        <li>
          <strong>Estrutura semântica.</strong> Um <code>&lt;h1&gt;</code> por página, hierarquia de
          títulos correta, <code>&lt;main&gt;</code>/<code>&lt;nav&gt;</code>/<code>&lt;footer&gt;</code>{" "}
          com rótulos.
        </li>
        <li>
          <strong>Texto alternativo de sentido.</strong> Gráficos SVG têm <code>role=&quot;img&quot;</code>{" "}
          + <code>aria-label</code> que descreve o dado, não a forma.
        </li>
        <li>
          <strong>Movimento opcional.</strong> Animações (skeleton) respeitam{" "}
          <code>prefers-reduced-motion</code>.
        </li>
      </ul>

      <h2>Como verificamos</h2>
      <p>
        Checagens automáticas (axe) entram na esteira; o build reprova em regressão de contraste ou
        rótulo. Testes manuais de teclado e leitor de tela acompanham telas novas — esta declaração
        é viva, não decorativa.
      </p>

      <h2>Limitações conhecidas</h2>
      <p>
        O cartograma do IVM ainda usa tiles (falta a malha geométrica do IBGE); a leitura por tabela
        acessível acompanha o mapa. Faltam, em DS v2: documentação formal de breakpoints e estados
        de hover/active — registrados no backlog do ADR-0009.
      </p>

      <h2>Encontrou uma barreira?</h2>
      <p>
        Relate em{" "}
        <a href="mailto:acessibilidade@dadosabedoria.org">acessibilidade@dadosabedoria.org</a>{" "}
        <span className="nota">[placeholder]</span>. Tratamos relato de barreira como bug de
        prioridade alta.
      </p>
    </main>
  );
}
