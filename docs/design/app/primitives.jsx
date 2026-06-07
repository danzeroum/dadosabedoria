/* Primitivos compartilhados — DadoSabedoria IVM.
   Acessibilidade: estado nunca só por cor (cor + ícone + texto + aria). */
const { useState, useRef, useEffect } = React;

/* ---------- Ícones (simples, decorativos salvo aria) ---------- */
const Icon = {
  check: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" {...p}><polyline points="20 6 9 17 4 12" /></svg>),
  alerta: (p) => (<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M12 9v4M12 17h.01" /><path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z" /></svg>),
  cadeado: (p) => (<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>),
  lupa: (p) => (<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>),
  escudo: (p) => (<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></svg>),
  compartilhar: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><path d="m8.6 13.5 6.8 4M15.4 6.5 8.6 10.5" /></svg>),
  baixar: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>),
  sino: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>),
  externo: (p) => (<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /></svg>),
  seta: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M19 12H5M12 19l-7-7 7-7" /></svg>),
  chevron: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><polyline points="6 9 12 15 18 9" /></svg>),
  grade: (p) => (<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>),
  mapa: (p) => (<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m9 4 6 2 5-2v14l-5 2-6-2-5 2V6l5-2Z" /><path d="M9 4v14M15 6v14" /></svg>),
  megafone: (p) => (<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m3 11 14-7v16L3 13zM3 11v2M17 8a4 4 0 0 1 0 8" /></svg>),
};

/* ---------- helpers de semáforo ---------- */
const ROTULO_SEM = { verde: "baixa vulnerabilidade", amarelo: "vulnerabilidade média", vermelho: "alta vulnerabilidade" };
const PALAVRA_SEM = { verde: "menos vulnerável", amarelo: "atenção", vermelho: "mais vulnerável" };
function intensidade(v) { return v < 33 ? "baixa" : v <= 66 ? "media" : "alta"; }

/* ---------- Semáforo pill (cor + ícone + texto) ---------- */
function SemPill({ estado, mini }) {
  const Ico = estado === "vermelho" ? Icon.alerta : estado === "amarelo" ? Icon.alerta : Icon.check;
  return (
    <span className={"sem-pill sem-" + estado}>
      <Ico className="icone" aria-hidden="true" />
      <span>{PALAVRA_SEM[estado]}</span>
      <span className="sr-only"> — {ROTULO_SEM[estado]}</span>
    </span>
  );
}

/* ---------- Selo de confiança (frescor + proveniência) ---------- */
function SeloConfianca({ meta, compacto }) {
  const [aberto, setAberto] = useState(false);
  const fresco = meta.atraso_dias <= 60;
  return (
    <div className="selo">
      <button className="selo-cabeca" aria-expanded={aberto} onClick={() => setAberto(!aberto)}>
        <span className="selo-shield" aria-hidden="true"><Icon.escudo /></span>
        <span className="selo-meta">
          <span className="selo-linha1">
            <strong>Fonte verificada</strong>
            <span className="selo-fontes">
              {meta.fontes.map((f) => (<span key={f.sigla} className="chip-fonte">{f.sigla}</span>))}
            </span>
          </span>
          <span className="selo-frescor">
            <span className={"frescor-dot " + (fresco ? "fresco" : "atencao")} aria-hidden="true" />
            <span>Dado até <strong>{meta.periodo_rotulo}</strong> · atraso típico ~{meta.atraso_dias} dias · metodologia {meta.versao_metodologia}</span>
          </span>
        </span>
        <span className="selo-toggle">
          {aberto ? "ocultar" : "ver fontes"} <Icon.chevron style={{ transform: aberto ? "rotate(180deg)" : "none", transition: "transform .15s" }} />
        </span>
      </button>
      {aberto && (
        <div className="selo-detalhe">
          {meta.fontes.map((f) => (
            <div key={f.sigla} className="selo-fonte-row">
              <span className="sig">{f.sigla}</span>
              <span className="org">{f.nome} · <span style={{ color: "var(--faint)" }}>{f.orgao}</span> · domínio {f.dominio}</span>
              <span className="ate">até {f.ate} · {f.atraso}</span>
            </div>
          ))}
          <div className="selo-rodape">
            <span>{meta.licenca}</span>
            <a href="#metodologia" className="mono" style={{ color: "var(--marca-escura)" }}>metodologia {meta.versao_metodologia} ↗</a>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Legenda (semáforo + estados honestos de dado) ---------- */
function Legenda() {
  const itens = [
    ["sw-verde", "Menos vulnerável", "0–32"],
    ["sw-amarelo", "Atenção", "33–66"],
    ["sw-vermelho", "Mais vulnerável", "67–100"],
    ["sw-protegido", "Protegido (privacidade)", null],
    ["sw-semcob", "Sem cobertura", null],
  ];
  return (
    <ul className="legenda" aria-label="Legenda do índice">
      {itens.map(([cls, txt, faixa]) => (
        <li key={txt}><span className={"leg-amostra " + cls} aria-hidden="true" /><span>{txt}{faixa ? <span className="mono" style={{ color: "var(--faint)" }}> &nbsp;{faixa}</span> : null}</span></li>
      ))}
    </ul>
  );
}

/* ---------- Comparador honesto (polaridade + supressão/sem cobertura) ---------- */
function LinhaBarra({ rotulo, valor }) {
  if (valor === "suprimido") {
    return (
      <div className="barra">
        <span className="barra-rotulo">{rotulo}</span>
        <span className="barra-protegido protegido"><Icon.cadeado aria-hidden="true" /> protegido — privacidade</span>
      </div>
    );
  }
  if (valor === "sem_cobertura") {
    return (
      <div className="barra">
        <span className="barra-rotulo">{rotulo}</span>
        <span className="barra-protegido semcob">sem cobertura neste período</span>
      </div>
    );
  }
  const pct = Math.max(0, Math.min(100, valor));
  return (
    <div className="barra">
      <span className="barra-rotulo">{rotulo}</span>
      <span className="barra-trilha" aria-hidden="true"><span className="barra-fill" data-int={intensidade(valor)} style={{ width: pct + "%" }} /></span>
      <span className="barra-valor">{valor}</span>
    </div>
  );
}

function Comparador({ item, detalhado }) {
  return (
    <div className="comparador" role="group" aria-label="Subíndices de vulnerabilidade (maior = mais vulnerável)">
      <LinhaBarra rotulo="Emprego" valor={item.v_emprego} />
      <LinhaBarra rotulo="Finanças" valor={item.v_financas} />
      <LinhaBarra rotulo="Saúde" valor={item.v_saude} />
      {detalhado && (
        <p className="mono" style={{ fontSize: "0.7rem", color: "var(--faint)", margin: "4px 0 0" }}>
          escala 0–100 · maior = mais vulnerável
        </p>
      )}
    </div>
  );
}

/* ---------- Popover "O que é o IVM?" ---------- */
function OQueEhIVM() {
  const [aberto, setAberto] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    if (!aberto) return;
    const fora = (e) => { if (ref.current && !ref.current.contains(e.target)) setAberto(false); };
    const esc = (e) => { if (e.key === "Escape") setAberto(false); };
    document.addEventListener("mousedown", fora);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", fora); document.removeEventListener("keydown", esc); };
  }, [aberto]);
  return (
    <span style={{ position: "relative", display: "inline-block" }} ref={ref}>
      <button className="info-btn" aria-expanded={aberto} onClick={() => setAberto(!aberto)}>
        <i className="info-i" aria-hidden="true">?</i> O que é o IVM?
      </button>
      {aberto && (
        <div className="pop" role="dialog" aria-label="O que é o IVM" style={{ top: "calc(100% + 8px)", left: 0 }}>
          <h4>Índice de Vulnerabilidade Municipal</h4>
          <p>Um número de <strong>0 a 100</strong> que resume o quão vulnerável está um município hoje. <strong>Quanto maior, mais vulnerável.</strong> Não é nota de “cidade boa ou ruim” — é um sinal de onde a atenção pública é mais urgente.</p>
          <div className="formula">IVM = peso·Emprego + peso·Finanças + peso·Saúde<br />(cada parte normalizada 0–100)</div>
          <div className="pop-faixas">
            <div className="pop-faixa"><span className="leg-amostra sw-vermelho" aria-hidden="true" /> <strong style={{ color: "var(--vermelho)" }}>Vermelho</strong> = sua cidade está entre as mais vulneráveis — vale cobrar ação.</div>
            <div className="pop-faixa"><span className="leg-amostra sw-amarelo" aria-hidden="true" /> <strong style={{ color: "var(--amarelo)" }}>Amarelo</strong> = sinais de atenção, acompanhe a tendência.</div>
            <div className="pop-faixa"><span className="leg-amostra sw-verde" aria-hidden="true" /> <strong style={{ color: "var(--verde)" }}>Verde</strong> = menos vulnerável neste momento.</div>
          </div>
        </div>
      )}
    </span>
  );
}

/* ---------- Série temporal (SVG, com pontos suprimidos marcados, não omitidos) ---------- */
function SerieTemporal({ serie }) {
  const W = 560, H = 200, P = 30;
  const n = serie.length;
  const x = (i) => P + (i * (W - 2 * P)) / Math.max(1, n - 1);
  const y = (v) => H - P - (v / 100) * (H - 2 * P);
  const cor = (v) => (v < 33 ? "var(--verde)" : v <= 66 ? "var(--amarelo)" : "var(--vermelho)");
  const pts = serie.map((d, i) => x(i) + "," + y(d.ivm)).join(" ");
  const linhas = [33, 66];
  const passo = Math.ceil(n / 7);
  return (
    <div className="serie-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} className="serie-svg" role="img" aria-label={"Série temporal do IVM, de " + serie[0].periodo + " a " + serie[n - 1].periodo}>
        {linhas.map((l) => (
          <g key={l}>
            <line x1={P} y1={y(l)} x2={W - P} y2={y(l)} stroke="var(--border)" strokeDasharray="3 4" />
            <text x={W - P + 2} y={y(l) + 3} fontSize="9" fill="var(--faint)" fontFamily="var(--mono)">{l}</text>
          </g>
        ))}
        <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="var(--border-strong)" />
        {n > 1 && <polyline points={pts} fill="none" stroke="var(--marca)" strokeWidth="2.5" strokeLinejoin="round" />}
        {serie.map((d, i) => (
          <circle key={d.periodo} cx={x(i)} cy={y(d.ivm)} r={i === n - 1 ? 5.5 : 3.5} fill={cor(d.ivm)} stroke="#fff" strokeWidth="1.5">
            <title>{d.periodo}: IVM {d.ivm.toFixed(1)}</title>
          </circle>
        ))}
      </svg>
      <ol className="serie-rotulos" aria-hidden="true">
        {serie.filter((_, i) => i % passo === 0 || i === n - 1).map((d) => (<li key={d.periodo}>{d.periodo.slice(2)}</li>))}
      </ol>
    </div>
  );
}

Object.assign(window, { Icon, SemPill, SeloConfianca, Legenda, Comparador, LinhaBarra, OQueEhIVM, SerieTemporal, ROTULO_SEM, PALAVRA_SEM, intensidade });
