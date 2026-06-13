import Link from "next/link";

// 404 dedicado: notFound() é chamado em ~15 páginas de detalhe (município/produto sem dado).
// Mantém o header/footer do layout. Moldura honesta: ausência não é veredito, é falta de cobertura.
export default function NotFound() {
  return (
    <main className="sistema-centro">
      <p className="sistema-codigo">404</p>
      <h1>Esta página não existe</h1>
      <p>
        O endereço pode ter mudado, ou o município/produto que você procura não está no acervo. Nem
        todo município tem dado em todo produto — ausência aqui não é veredito, é falta de cobertura.
      </p>
      <div className="sistema-acoes">
        <Link className="botao botao-primario" href="/produtos">
          Ver os produtos
        </Link>
        <Link className="botao botao-secundario" href="/ivm">
          Abrir o mapa do IVM
        </Link>
      </div>
      <p className="nota" style={{ marginTop: "18px" }}>
        Se você chegou por um link nosso, <Link href="/perguntar">pergunte aos dados</Link> o que
        procurava.
      </p>
    </main>
  );
}
