/* OndeFoi — app: router, modais (reusam Modal/Icon), tweaks. */
const { useState: useOFA, useEffect: useOFAE } = React;

const OF_TWEAKS = /*EDITMODE-BEGIN*/{
  "plataforma": "desktop",
  "fonte": "plex"
}/*EDITMODE-END*/;
const OF_FONTES = { plex: '"IBM Plex Sans", system-ui, sans-serif', system: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif' };

/* ---------- Compartilhar (card honesto + a quem cobrar TCE) ---------- */
function OFCompartilhar({ item, meta, onFechar }) {
  const [copiado, setCopiado] = useOFA(false);
  return (
    <Modal titulo={"Compartilhar — " + item.nome} onFechar={onFechar}>
      <div className="share-card" style={{ background: "linear-gradient(160deg,#0f766e,#115e59)" }}>
        <div className="sc-eyebrow">DadoSabedoria · OndeFoi · {meta.periodo_rotulo}</div>
        <div className="sc-cidade">{item.nome}<span style={{ opacity: .7, fontWeight: 400, fontSize: ".9rem" }}> · {item.uf}</span></div>
        <div className="sc-ivm"><span className="n tnum">{item.pctGeral}%</span><span style={{ fontSize: ".9rem", opacity: .9 }}>do divulgado por função foi executado</span></div>
        <div className="sc-bar"><span style={{ width: item.pctGeral + "%" }} /></div>
        <div className="sc-rodape"><span>executou {fmtBRL(item.executado)} de {fmtBRL(item.recDivulgado)} divulgados</span><span>+{fmtBRL(item.recForaCalculo)} fora do cálculo · SICONFI</span></div>
      </div>
      <p style={{ fontSize: ".78rem", color: "var(--muted)", margin: "10px 2px 0" }}>O card diz <b>execução</b>, não serviço entregue — a honestidade viaja junto com o número.</p>
      <div className="compart-opcoes">
        <button className="btn" onClick={() => { setCopiado(true); setTimeout(() => setCopiado(false), 1600); }}>{copiado ? <><Icon.check /> Link copiado</> : "Copiar link"}</button>
        <button className="btn">WhatsApp</button>
        <button className="btn">Baixar imagem</button>
      </div>
      <div style={{ borderTop: "1px solid var(--border)", paddingTop: 16, marginTop: 16 }}>
        <h4 style={{ margin: "0 0 4px", fontSize: ".95rem", display: "flex", alignItems: "center", gap: 7 }}><Icon.megafone /> A quem cobrar</h4>
        <p style={{ margin: "0 0 12px", color: "var(--muted)", fontSize: ".86rem" }}>Quem fiscaliza a execução do orçamento — leve o dado a quem decide.</p>
        <div style={{ display: "grid", gap: 8 }}>
          <a className="btn" href="#camara" style={{ justifyContent: "space-between" }}>Câmara Municipal de {item.nome} <Icon.externo /></a>
          <a className="btn" href="#tce" style={{ justifyContent: "space-between" }}>Tribunal de Contas — TCE-{item.uf} <Icon.externo /></a>
        </div>
      </div>
    </Modal>
  );
}

/* ---------- Exportar com citação (SICONFI) ---------- */
function OFExportar({ item, meta, onFechar }) {
  const [fmt, setFmt] = useOFA("csv");
  const hoje = new Date().toLocaleDateString("pt-BR");
  const cita = `DadoSabedoria (2026). Execução orçamentária municipal (SICONFI) — ${item.nome}/${item.uf}, ${meta.periodo_rotulo}: ${item.pctGeral}% executado (executado ${fmtBRL(item.executado)} ÷ recebido divulgado por função ${fmtBRL(item.recDivulgado)}; ${fmtBRL(item.recForaCalculo)} do recebido fora do cálculo). Fonte: Tesouro Nacional/STN — SICONFI. Acesso em ${hoje}. ${meta.licenca}`;
  const formatos = [["csv", "CSV", "execução por função"], ["json", "JSON", "com meta de proveniência"], ["embed", "Embed", "iframe para reportagem"]];
  return (
    <Modal titulo={"Exportar — " + item.nome} onFechar={onFechar}>
      <p style={{ margin: "0 0 6px", color: "var(--muted)", fontSize: ".88rem" }}>Export <b>com citação e proveniência</b> — e com a ressalva de que SICONFI é execução, não serviço.</p>
      <div className="export-formatos">
        {formatos.map(([k, nome, desc]) => (<button key={k} className="fmt" aria-pressed={fmt === k} onClick={() => setFmt(k)}><span className="fmt-nome">{nome}</span><span className="fmt-desc">{desc}</span></button>))}
      </div>
      {fmt === "embed"
        ? <div className="cita-bloco">{`<iframe src="dadosabedoria.org/embed/of/${item.codigo_ibge}"\n  width="100%" height="340" title="OndeFoi ${item.nome}"></iframe>`}</div>
        : <div><div className="sub-eyebrow" style={{ marginBottom: 6 }}>Citação sugerida (ABNT)</div><div className="cita-bloco">{cita}</div></div>}
      <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
        <button className="btn btn-primario"><Icon.baixar /> Baixar {fmt.toUpperCase()}</button>
        <button className="btn">Copiar citação</button>
        <a className="btn btn-fantasma" href="#api" style={{ marginLeft: "auto" }}>Ver a API ↗</a>
      </div>
    </Modal>
  );
}

/* ---------- Avise-me se travar (consentimento) ---------- */
function OFAlerta({ item, onFechar }) {
  const [ok, setOk] = useOFA(false);
  return (
    <Modal titulo={"Avise-me — " + item.nome} onFechar={onFechar}>
      {ok ? (
        <div className="sucesso">
          <span className="check" aria-hidden="true"><Icon.check style={{ width: 26, height: 26 }} /></span>
          <h3 style={{ margin: 0 }}>Pronto!</h3>
          <p style={{ margin: 0, color: "var(--muted)", maxWidth: "36ch" }}>Você será avisado se a execução de {item.nome} cair de faixa numa função-chave. Cancele quando quiser.</p>
          <button className="btn btn-primario" onClick={onFechar} style={{ marginTop: 6 }}>Fechar</button>
        </div>
      ) : (
        <div>
          <p style={{ margin: "0 0 4px", color: "var(--muted)", fontSize: ".9rem" }}>Receba um aviso se a execução de <b style={{ color: "var(--ink)" }}>{item.nome}</b> travar — por exemplo, saúde ou educação caírem para <span style={{ color: "var(--exec-baixa)", fontWeight: 600 }}>executou pouco</span>.</p>
          <div className="alerta-campo"><label htmlFor="of-al">E-mail ou telefone</label><input id="of-al" type="email" placeholder="voce@exemplo.org" /></div>
          <div className="nota-privacidade">
            <Icon.cadeado style={{ flex: "0 0 auto", marginTop: 1 }} aria-hidden="true" />
            <span>Seu contato fica num cofre isolado (schema <span className="mono">app</span>), cifrado e nunca cruzado com o dado público. O alerta usa só o evento orçamentário, nunca você. <b>LGPD por desenho.</b></span>
          </div>
          <button className="btn btn-primario" style={{ width: "100%", marginTop: 14 }} onClick={() => setOk(true)}><Icon.sino /> Quero ser avisado</button>
          <p className="mono" style={{ fontSize: ".68rem", color: "var(--faint)", textAlign: "center", margin: "10px 0 0" }}>protótipo · auth do cidadão chega com o runtime de consentimento</p>
        </div>
      )}
    </Modal>
  );
}

function OFApp() {
  const [t, setTweak] = useTweaks(OF_TWEAKS);
  const [rota, setRota] = useOFA({ nome: "lista" });
  const [modal, setModal] = useOFA(null);
  const { META } = window.ONDEFOI;

  useOFAE(() => { document.documentElement.style.setProperty("--fonte", OF_FONTES[t.fonte] || OF_FONTES.plex); }, [t.fonte]);

  const onAbrir = (tipo, arg) => {
    if (tipo === "lista") { setRota({ nome: "lista" }); window.scrollTo(0, 0); }
    else if (tipo === "painel") { setRota({ nome: "painel", codigo: arg }); window.scrollTo(0, 0); }
  };
  const onAcao = (tipo, item) => setModal({ tipo, item });

  return (
    <div className="viewport" data-modo={t.plataforma}>
      <header className="topo">
        <div className="topo-inner">
          <a className="topo-marca" href="#/of" onClick={(e) => { e.preventDefault(); onAbrir("lista"); }}>
            <span className="topo-logo" aria-hidden="true">DS</span> DadoSabedoria <small>· OndeFoi</small>
          </a>
          <nav className="topo-links" aria-label="Produtos">
            <a href="IVM.html">IVM</a>
            <a href="#/of" onClick={(e) => { e.preventDefault(); onAbrir("lista"); }} aria-current={rota.nome === "lista" ? "page" : undefined}>OndeFoi</a>
            <a href="#api">API</a>
          </nav>
        </div>
      </header>

      <div className="conteudo">
        {rota.nome === "lista" ? <OFLista onAbrir={onAbrir} /> : <OFPainel codigo={rota.codigo} onAbrir={onAbrir} onAcao={onAcao} />}
      </div>

      <footer className="rodape">
        <span><b style={{ color: "var(--muted)" }}>DadoSabedoria · OndeFoi</b> · execução ≠ serviço</span>
        <span>·</span><span>Fonte: SICONFI (Tesouro Nacional)</span>
        <span style={{ marginLeft: "auto" }} className="mono">nasce nos primitivos do IVM</span>
      </footer>

      {modal && modal.tipo === "compartilhar" && <OFCompartilhar item={modal.item} meta={META} onFechar={() => setModal(null)} />}
      {modal && modal.tipo === "exportar" && <OFExportar item={modal.item} meta={META} onFechar={() => setModal(null)} />}
      {modal && modal.tipo === "alerta" && <OFAlerta item={modal.item} onFechar={() => setModal(null)} />}

      <TweaksPanel>
        <TweakSection label="Apresentação" />
        <TweakRadio label="Plataforma" value={t.plataforma} options={["desktop", "mobile"]} onChange={(v) => setTweak("plataforma", v)} />
        <TweakSelect label="Tipografia" value={t.fonte} options={[["plex", "IBM Plex"], ["system", "System UI"]]} onChange={(v) => setTweak("fonte", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<OFApp />);
