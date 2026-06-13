// Skeleton de carregamento durante o SSR force-dynamic (todo fetch é server-side). Decorativo: o
// leitor de tela ouve o aviso .sr-only, não os blocos. A animação respeita prefers-reduced-motion.
export default function Loading() {
  return (
    <main aria-busy="true" aria-label="Carregando conteúdo">
      <div className="skeleton">
        <div className="sk-bloco sk-titulo" />
        <div className="sk-bloco sk-linha" />
        <div className="sk-bloco sk-linha curta" />
        <div className="sk-grid">
          <div className="sk-bloco sk-card" />
          <div className="sk-bloco sk-card" />
          <div className="sk-bloco sk-card" />
          <div className="sk-bloco sk-card" />
          <div className="sk-bloco sk-card" />
          <div className="sk-bloco sk-card" />
        </div>
        <p className="sr-only">Carregando os dados do acervo…</p>
      </div>
    </main>
  );
}
