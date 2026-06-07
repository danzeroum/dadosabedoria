/* App — roteamento, Tweaks e modais. */
const { useState: useApp, useEffect: useAppE } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "plataforma": "desktop",
  "fonte": "plex",
  "marca": "#0f766e",
  "mapa": "cartograma",
  "vazioDemo": false
}/*EDITMODE-END*/;

const FONTES = {
  plex: '"IBM Plex Sans", system-ui, sans-serif',
  system: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  spline: '"Spline Sans", system-ui, sans-serif',
};

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [rota, setRota] = useApp({ nome: "topo" });
  const [modal, setModal] = useApp(null);
  const { META } = window.DADOS;

  // aplica tokens dos tweaks
  useAppE(() => {
    const r = document.documentElement;
    r.style.setProperty("--marca", t.marca);
    // deriva uma marca-escura simples
    r.style.setProperty("--fonte", FONTES[t.fonte] || FONTES.plex);
  }, [t.marca, t.fonte]);

  const onAbrir = (tipo, arg) => {
    if (tipo === "topo") { setRota({ nome: "topo" }); window.scrollTo(0, 0); }
    else if (tipo === "drill") { setRota({ nome: "drill", codigo: arg }); window.scrollTo(0, 0); }
    else if (tipo === "modo") { setTweak("mapa", arg); }
    else if (tipo === "avise") { setModal({ tipo: "alerta", item: { nome: "esta região", codigo_ibge: "" } }); }
  };
  const onCompartilhar = (m) => setModal({ tipo: "compartilhar", item: m });
  const onAcao = (tipo, item) => setModal({ tipo, item });

  return (
    <div className="viewport" data-modo={t.plataforma}>
      <header className="topo">
        <div className="topo-inner">
          <a className="topo-marca" href="#/ivm" onClick={(e) => { e.preventDefault(); onAbrir("topo"); }}>
            <span className="topo-logo" aria-hidden="true">DS</span>
            DadoSabedoria <small>· IVM</small>
          </a>
          <nav className="topo-links" aria-label="Seções">
            <a href="#/ivm" onClick={(e) => { e.preventDefault(); onAbrir("topo"); }} aria-current={rota.nome === "topo" ? "page" : undefined}>Mapa</a>
            <a href="#api">API</a>
            <a href="#metodo">Metodologia</a>
          </nav>
        </div>
      </header>

      <div className="conteudo">
        {rota.nome === "topo"
          ? <TelaTopo modoMapa={t.mapa} vazio={t.vazioDemo} onAbrir={onAbrir} onCompartilhar={onCompartilhar} />
          : <TelaDrill codigo={rota.codigo} onAbrir={onAbrir} onAcao={onAcao} />}
      </div>

      <footer className="rodape">
        <span><strong style={{ color: "var(--muted)" }}>DadoSabedoria</strong> · dado público vira ação cívica</span>
        <span>·</span>
        <span>Fontes: {META.fontes.map((f) => f.sigla).join(" · ")}</span>
        <span>·</span>
        <span>Índice composto {META.versao_metodologia}</span>
        <span style={{ marginLeft: "auto" }} className="mono">privacidade por desenho · LGPD</span>
      </footer>

      {modal && modal.tipo === "compartilhar" && <ModalCompartilhar item={modal.item} meta={META} onFechar={() => setModal(null)} />}
      {modal && modal.tipo === "exportar" && <ModalExportar item={modal.item} meta={META} onFechar={() => setModal(null)} />}
      {modal && modal.tipo === "alerta" && <ModalAlerta item={modal.item} onFechar={() => setModal(null)} />}

      <TweaksPanel>
        <TweakSection label="Apresentação" />
        <TweakRadio label="Plataforma" value={t.plataforma} options={["desktop", "mobile"]} onChange={(v) => setTweak("plataforma", v)} />
        <TweakRadio label="Mapa" value={t.mapa} options={["cartograma", "cartoes"]} onChange={(v) => setTweak("mapa", v)} />
        <TweakSection label="Identidade" />
        <TweakSelect label="Tipografia" value={t.fonte} options={[["plex", "IBM Plex (atual)"], ["system", "System UI"], ["spline", "Spline Sans"]]} onChange={(v) => setTweak("fonte", v)} />
        <TweakColor label="Cor da marca" value={t.marca} options={["#0f766e", "#1e5eb8", "#7c3aed", "#b45309"]} onChange={(v) => setTweak("marca", v)} />
        <TweakSection label="Demonstração" />
        <TweakToggle label="Estado vazio (correção H-01)" value={t.vazioDemo} onChange={(v) => setTweak("vazioDemo", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
