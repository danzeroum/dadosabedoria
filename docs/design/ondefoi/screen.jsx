/* OndeFoi — telas. Reusa SeloConfianca (primitivo), Modal/Icon e o tratamento de supressão. */
const { useState: useOF, useMemo: useOFM, useRef: useOFR, useEffect: useOFE } = React;

function fmtBRL(milhoes) {
  if (milhoes >= 1000) return "R$ " + (milhoes / 1000).toFixed(1).replace(".", ",") + " bi";
  return "R$ " + Math.round(milhoes) + " mi";
}
const BANDA_ROTULO = {
  alta: "executou quase tudo",
  parcial: "execução parcial",
  baixa: "executou pouco",
};

/* ---------- ExecPill (honesto: número + palavra) ---------- */
function ExecPill({ banda, pct }) {
  return (
    <span className={"exec-pill exec-" + banda}>
      <span>executou {pct}%</span>
      <span className="sr-only"> — {BANDA_ROTULO[banda]} do que recebeu</span>
    </span>
  );
}

/* ---------- Donut de execução ---------- */
function Donut({ pct, banda }) {
  const cor = banda === "baixa" ? "var(--exec-baixa)" : banda === "parcial" ? "var(--exec-parcial)" : "var(--exec-alta)";
  const r = 56, c = 2 * Math.PI * r;
  return (
    <div className="donut" role="img" aria-label={`Executou ${pct}% do recebido`}>
      <svg viewBox="0 0 132 132" width="132" height="132">
        <circle cx="66" cy="66" r={r} fill="none" stroke="var(--border)" strokeWidth="14" />
        <circle cx="66" cy="66" r={r} fill="none" stroke={cor} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={`${(c * pct) / 100} ${c}`} transform="rotate(-90 66 66)" />
      </svg>
      <span className="num"><b className="tnum">{pct}%</b><span>do divulgado</span></span>
    </div>
  );
}

/* ---------- InfoPop genérico (honesto "o que é execução") ---------- */
function InfoPop({ titulo, children }) {
  const [a, setA] = useOF(false);
  const ref = useOFR(null);
  useOFE(() => {
    if (!a) return;
    const fora = (e) => { if (ref.current && !ref.current.contains(e.target)) setA(false); };
    const esc = (e) => { if (e.key === "Escape") setA(false); };
    document.addEventListener("mousedown", fora); document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", fora); document.removeEventListener("keydown", esc); };
  }, [a]);
  return (
    <span style={{ position: "relative", display: "inline-block" }} ref={ref}>
      <button className="info-btn" aria-expanded={a} onClick={() => setA(!a)}><i className="info-i" aria-hidden="true">?</i> {titulo}</button>
      {a && <div className="pop" role="dialog" aria-label={titulo} style={{ top: "calc(100% + 8px)", right: 0 }}>{children}</div>}
    </span>
  );
}

/* ---------- Linha de função (recebido vs executado, com supressão) ---------- */
function FuncaoLinha({ fn }) {
  if (fn.estado !== "valor") {
    const sup = fn.estado === "suprimido";
    return (
      <div className="funcao">
        <div className="funcao-nome">{fn.f}<small>recebeu {fmtBRL(fn.rec)}</small></div>
        <div className={"funcao-sup " + (sup ? "suprimido" : "semcob")}>
          {sup ? <><Icon.cadeado aria-hidden="true" style={{ marginRight: 6 }} /> execução protegida (privacidade)</> : "sem cobertura no SICONFI deste exercício"}
        </div>
        <div className="funcao-pct mono" style={{ color: "var(--faint)", fontSize: ".8rem" }}>—</div>
      </div>
    );
  }
  return (
    <div className="funcao">
      <div className="funcao-nome">{fn.f}<small>recebeu {fmtBRL(fn.rec)}</small></div>
      <div className="funcao-trilha" aria-hidden="true">
        <div className={"funcao-exe " + window.ONDEFOI.banda(fn.pct)} style={{ width: Math.max(8, fn.pct) + "%" }}>
          <span>{fmtBRL(fn.exe)}</span>
        </div>
      </div>
      <div className="funcao-pct"><ExecPill banda={window.ONDEFOI.banda(fn.pct)} pct={fn.pct} /></div>
    </div>
  );
}

/* ========================= LISTA ========================= */
function OFLista({ onAbrir }) {
  const { MUNICIPIOS, META } = window.ONDEFOI;
  const [q, setQ] = useOF("");
  const filtrados = useOFM(() => {
    const t = q.trim().toLowerCase();
    return MUNICIPIOS.filter((m) => !t || m.nome.toLowerCase().includes(t) || m.codigo_ibge.includes(t));
  }, [q, MUNICIPIOS]);

  return (
    <main>
      <div className="cabecalho">
        <div>
          <div className="sub-eyebrow">Painel cívico · execução orçamentária · SICONFI</div>
          <h1 className="titulo-h1">Onde foi o dinheiro?</h1>
          <p className="dek">Quanto cada município <b>recebeu</b> e quanto <b>executou</b> por área, no último exercício. Execução mostra que o recurso saiu do orçamento — não que virou serviço na ponta.</p>
        </div>
        <div style={{ marginTop: 6 }}>
          <InfoPop titulo="O que é “execução”?">
            <h4>Execução ≠ serviço entregue</h4>
            <p>“Executar” é <b>empenhar e liquidar</b> a despesa — o recurso saiu do orçamento e foi pago. Isso <b>não garante</b> hospital funcionando ou obra entregue.</p>
            <p style={{ margin: 0 }}><b>Um % alto</b> ainda merece a pergunta “virou serviço?”. <b>Um % baixo</b> merece a pergunta “por que não saiu?”.</p>
          </InfoPop>
        </div>
      </div>

      <SeloConfianca meta={META} />

      <div className="controles">
        <div className="busca">
          <span className="lupa" aria-hidden="true"><Icon.lupa /></span>
          <input type="search" value={q} placeholder="Buscar município ou código IBGE…" aria-label="Buscar município" onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <ul className="of-legenda" aria-label="Legenda de execução">
        <li><span className="exec-pill exec-alta">≥80%</span> executou quase tudo — confira se virou serviço</li>
        <li><span className="exec-pill exec-parcial">55–79%</span> execução parcial</li>
        <li><span className="exec-pill exec-baixa">&lt;55%</span> executou pouco — merece a pergunta</li>
        <li><span className="leg-amostra sw-protegido" aria-hidden="true" /> protegido · <span className="leg-amostra sw-semcob" aria-hidden="true" /> sem cobertura</li>
      </ul>
      <p className="contagem">{filtrados.length} municípios · ordenados do menor ao maior % de execução</p>

      <ul className="of-grade">
        {filtrados.map((m) => (
          <li key={m.codigo_ibge} className="of-card">
            <a className="of-card-link" href={"#/of/" + m.codigo_ibge} onClick={(e) => { e.preventDefault(); onAbrir("painel", m.codigo_ibge); }}>
              <div className="of-top">
                <div><div className="of-nome">{m.nome}</div><div className="of-uf mono">{m.uf} · {m.codigo_ibge}</div></div>
                <ExecPill banda={m.banda} pct={m.pctGeral} />
              </div>
              <div className="of-bar" aria-hidden="true"><i className={m.banda} style={{ width: m.pctGeral + "%" }} /></div>
              <div className="of-meta"><span>executou {fmtBRL(m.executado)}</span><span>de {fmtBRL(m.recDivulgado)} divulgados</span></div>
              <div className="of-fora">+ {fmtBRL(m.recForaCalculo)} do recebido não detalhado / protegido — fora do %</div>
            </a>
          </li>
        ))}
      </ul>

      <p className="mono" style={{ fontSize: ".74rem", color: "var(--faint)", marginTop: 22, maxWidth: "80ch" }}>{META.metodologia} {META.licenca}</p>
    </main>
  );
}

/* ========================= PAINEL ========================= */
function OFPainel({ codigo, onAbrir, onAcao }) {
  const { MUNICIPIOS, META } = window.ONDEFOI;
  const m = MUNICIPIOS.find((x) => x.codigo_ibge === codigo);
  if (!m) return <main><p>Município não encontrado. <a href="#/of" onClick={(e) => { e.preventDefault(); onAbrir("lista"); }}>Voltar</a></p></main>;
  const nProtegidas = m.funcoes.filter((f) => f.estado !== "valor").length;

  return (
    <main>
      <a className="voltar" href="#/of" onClick={(e) => { e.preventDefault(); onAbrir("lista"); }}><Icon.seta /> Voltar à lista</a>

      <div className="cabecalho">
        <div>
          <div className="sub-eyebrow">{m.uf} · {m.codigo_ibge} · {META.periodo_rotulo}</div>
          <h1 className="titulo-h1" style={{ fontSize: "2rem", marginTop: 2 }}>Onde foi o dinheiro de {m.nome}?</h1>
        </div>
        <div style={{ alignSelf: "center" }}>
          <InfoPop titulo="O que é “execução”?">
            <h4>Execução ≠ serviço entregue</h4>
            <p>“Executar” é <b>empenhar e liquidar</b> — o recurso saiu do orçamento. Não garante o serviço na ponta.</p>
            <p style={{ margin: 0 }}>SICONFI é contábil/fiscal. Para o serviço, cruze com os painéis de saúde, educação etc.</p>
          </InfoPop>
        </div>
      </div>

      <div className="enquadra">
        <Donut pct={m.pctGeral} banda={m.banda} />
        <div className="enquadra-txt">
          <h2><b>Executou {m.pctGeral}%</b> do que foi divulgado por função — e isso merece a pergunta.</h2>
          <p>De cada R$ 100 <b>divulgados por função</b>, <b>R$ {m.pctGeral}</b> foram executados. {m.banda === "baixa" ? "Executar pouco pode significar recurso parado — vale cobrar por quê." : m.banda === "alta" ? "Executou quase tudo — o próximo passo é checar se virou serviço na ponta." : "Execução parcial — acompanhe onde o recurso travou."}</p>
          <div className="recebido">
            <span>Divulgado por função <b className="tnum">{fmtBRL(m.recDivulgado)}</b></span>
            <span>Executou <b className="tnum">{fmtBRL(m.executado)}</b></span>
            <span style={{ color: "var(--faint)" }}>Fora do cálculo <b className="tnum">{fmtBRL(m.recForaCalculo)}</b></span>
          </div>
        </div>
      </div>

      <div className="honesto">
        <span className="ic" aria-hidden="true"><Icon.alerta /></span>
        <span><b>Atenção honesta:</b> o % usa a <b>mesma base</b> (executado ÷ recebido das funções divulgadas). Do total recebido — <b>{fmtBRL(m.recebido)}</b> — há <b>{fmtBRL(m.recForaCalculo)}</b> não detalhados por função ou protegidos, <b>fora deste cálculo</b> (não no denominador). E isto é <b>execução orçamentária</b> (SICONFI), não serviço entregue: um % alto não prova hospital funcionando; um % baixo é sinal para perguntar, não sentença.</span>
      </div>

      <div className="acoes-barra">
        <button className="btn btn-primario" onClick={() => onAcao("compartilhar", m)}><Icon.compartilhar /> Compartilhar</button>
        <button className="btn" onClick={() => onAcao("exportar", m)}><Icon.baixar /> Exportar com citação</button>
        <button className="btn" onClick={() => onAcao("alerta", m)}><Icon.sino /> Avise-me se travar</button>
        <a className="btn btn-fantasma" href="#cobrar" style={{ marginLeft: "auto", whiteSpace: "nowrap" }}><Icon.megafone /> A quem cobrar <Icon.externo /></a>
      </div>

      <section className="painel" style={{ marginTop: 8 }}>
        <h2>Execução por função orçamentária</h2>
        <p className="painel-sub">{META.periodo_rotulo} · barra = quanto do recebido foi executado · {nProtegidas > 0 ? `${nProtegidas} função(ões) com dado protegido ou sem cobertura — não é zero` : "todas as funções com dado"}</p>
        <div className="funcoes">
          {m.funcoes.map((fn) => (<FuncaoLinha key={fn.f} fn={fn} />))}
        </div>
      </section>

      <section className="painel" style={{ background: "var(--surface-2)", marginTop: 16 }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: 8 }}><Icon.escudo /> De onde vem este número</h2>
        <div style={{ marginTop: 10 }}><SeloConfianca meta={META} /></div>
      </section>
    </main>
  );
}

Object.assign(window, { OFLista, OFPainel, fmtBRL, ExecPill, BANDA_ROTULO });
