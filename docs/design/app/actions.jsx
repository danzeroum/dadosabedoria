/* Superfície de ação (etapa "agir" do funil) — modais. */
const { useState: useStateA } = React;

function Modal({ titulo, onFechar, children }) {
  return (
    <div className="overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onFechar(); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={titulo}>
        <div className="modal-cabeca">
          <h3>{titulo}</h3>
          <button className="fechar" aria-label="Fechar" onClick={onFechar}>×</button>
        </div>
        <div className="modal-corpo">{children}</div>
      </div>
    </div>
  );
}

/* ---------- Compartilhar: card cívico + link à ouvidoria ---------- */
function ModalCompartilhar({ item, meta, onFechar }) {
  const [copiado, setCopiado] = useStateA(false);
  const link = "dadosabedoria.org/ivm/" + item.codigo_ibge;
  const copiar = () => { setCopiado(true); setTimeout(() => setCopiado(false), 1800); };
  return (
    <Modal titulo={"Compartilhar — " + item.nome} onFechar={onFechar}>
      <div className="share-card">
        <div className="sc-eyebrow">DadoSabedoria · IVM {meta.periodo_rotulo}</div>
        <div className="sc-cidade">{item.nome}<span style={{ opacity: 0.7, fontWeight: 400, fontSize: "0.9rem" }}> · {item.uf}</span></div>
        <div className="sc-ivm">
          <span className="n tnum">{item.ivm.toFixed(1)}</span>
          <SemPill estado={item.semaforo} />
        </div>
        <div className="sc-bar"><span style={{ width: item.ivm + "%" }} /></div>
        <div className="sc-rodape">
          <span>Fonte: {meta.fontes.map((f) => f.sigla).join(" · ")}</span>
          <span>dado até {meta.periodo_rotulo}</span>
        </div>
      </div>
      <div className="compart-opcoes">
        <button className="btn" onClick={copiar}>{copiado ? <><Icon.check /> Link copiado</> : <>Copiar link</>}</button>
        <button className="btn">WhatsApp</button>
        <button className="btn">Baixar imagem</button>
      </div>
      <p className="mono" style={{ fontSize: "0.72rem", color: "var(--faint)", margin: "10px 0 18px" }}>{link}</p>

      <div style={{ borderTop: "1px solid var(--border)", paddingTop: "16px" }}>
        <h4 style={{ margin: "0 0 4px", fontSize: "0.95rem", display: "flex", alignItems: "center", gap: "7px" }}><Icon.megafone /> A quem cobrar</h4>
        <p style={{ margin: "0 0 12px", color: "var(--muted)", fontSize: "0.86rem" }}>Leve o dado a quem decide. Sem expor pessoas — o foco é o território.</p>
        <div style={{ display: "grid", gap: "8px" }}>
          <a className="btn" href="#ouvidoria" style={{ justifyContent: "space-between" }}>Ouvidoria de {item.nome} <Icon.externo /></a>
          <a className="btn" href="#camara" style={{ justifyContent: "space-between" }}>Vereadores e secretarias ({item.uf}) <Icon.externo /></a>
        </div>
      </div>
    </Modal>
  );
}

/* ---------- Exportar com citação (gestor / ONG / jornalista) ---------- */
function ModalExportar({ item, meta, onFechar }) {
  const [fmt, setFmt] = useStateA("csv");
  const hoje = new Date().toLocaleDateString("pt-BR");
  const cita = `DadoSabedoria (2026). Índice de Vulnerabilidade Municipal (IVM ${meta.versao_metodologia}) — ${item.nome}/${item.uf}, ${meta.periodo_rotulo}. Fontes: ${meta.fontes.map((f) => f.sigla).join(", ")}. Acesso em ${hoje}. ${meta.licenca}`;
  const formatos = [
    ["csv", "CSV", "série + subíndices"],
    ["json", "JSON", "com meta de proveniência"],
    ["embed", "Embed", "iframe para reportagem"],
  ];
  return (
    <Modal titulo={"Exportar — " + item.nome} onFechar={onFechar}>
      <p style={{ margin: "0 0 6px", color: "var(--muted)", fontSize: "0.88rem" }}>Todo export sai <strong>com citação e proveniência</strong> embutidas — pronto para reportagem ou parecer.</p>
      <div className="export-formatos">
        {formatos.map(([k, nome, desc]) => (
          <button key={k} className="fmt" aria-pressed={fmt === k} onClick={() => setFmt(k)}>
            <span className="fmt-nome">{nome}</span>
            <span className="fmt-desc">{desc}</span>
          </button>
        ))}
      </div>
      {fmt === "embed" ? (
        <div className="cita-bloco">{`<iframe src="dadosabedoria.org/embed/ivm/${item.codigo_ibge}"\n  width="100%" height="320" title="IVM ${item.nome}"></iframe>`}</div>
      ) : (
        <div>
          <div className="sub-eyebrow" style={{ marginBottom: "6px" }}>Citação sugerida (ABNT)</div>
          <div className="cita-bloco">{cita}</div>
        </div>
      )}
      <div style={{ display: "flex", gap: "8px", marginTop: "16px", flexWrap: "wrap" }}>
        <button className="btn btn-primario"><Icon.baixar /> Baixar {fmt.toUpperCase()}</button>
        <button className="btn">Copiar citação</button>
        <a className="btn btn-fantasma" href="#api" style={{ marginLeft: "auto" }}>Precisa de tudo? Ver a API ↗</a>
      </div>
    </Modal>
  );
}

/* ---------- Assinar alerta (prepara o lugar; auth chega depois) ---------- */
function ModalAlerta({ item, onFechar }) {
  const [enviado, setEnviado] = useStateA(false);
  return (
    <Modal titulo={"Avise-me — " + item.nome} onFechar={onFechar}>
      {enviado ? (
        <div className="sucesso">
          <span className="check" aria-hidden="true"><Icon.check style={{ width: 26, height: 26 }} /></span>
          <h3 style={{ margin: 0 }}>Pronto!</h3>
          <p style={{ margin: 0, color: "var(--muted)", maxWidth: "36ch" }}>Você será avisado se {item.nome} entrar no vermelho. Pode cancelar a qualquer momento — é a sua escolha.</p>
          <button className="btn btn-primario" onClick={onFechar} style={{ marginTop: "6px" }}>Fechar</button>
        </div>
      ) : (
        <div>
          <p style={{ margin: "0 0 4px", color: "var(--muted)", fontSize: "0.9rem" }}>Receba um aviso quando o IVM de <strong style={{ color: "var(--ink)" }}>{item.nome}</strong> mudar de faixa — por exemplo, ao entrar no <span style={{ color: "var(--vermelho)", fontWeight: 600 }}>vermelho</span>.</p>
          <div className="alerta-campo">
            <label htmlFor="al-email">E-mail ou telefone</label>
            <input id="al-email" type="email" placeholder="voce@exemplo.org" />
          </div>
          <div className="nota-privacidade">
            <Icon.cadeado style={{ flex: "0 0 auto", marginTop: "1px" }} aria-hidden="true" />
            <span>Seu contato fica num cofre isolado (schema <span className="mono">app</span>), cifrado e nunca cruzado com o dado público. O alerta usa só o evento do território, nunca você. <strong>LGPD por desenho.</strong></span>
          </div>
          <button className="btn btn-primario" style={{ width: "100%", marginTop: "14px" }} onClick={() => setEnviado(true)}><Icon.sino /> Quero ser avisado</button>
          <p className="mono" style={{ fontSize: "0.68rem", color: "var(--faint)", textAlign: "center", margin: "10px 0 0" }}>protótipo · a autenticação do cidadão chega na próxima fatia</p>
        </div>
      )}
    </Modal>
  );
}

Object.assign(window, { Modal, ModalCompartilhar, ModalExportar, ModalAlerta });
