/* Telas — DadoSabedoria IVM. Topo (/ivm) e Drill-down (/ivm/[codigo]). */
const { useState: useS, useMemo, useRef: useR, useEffect: useE } = React;

/* ============================================================ TOPO (/ivm) */
function TelaTopo({ modoMapa, vazio, onAbrir, onCompartilhar }) {
  const { MUNICIPIOS, META } = window.DADOS;
  const [q, setQ] = useS("");
  const [uf, setUf] = useS("todos");
  const [periodo, setPeriodo] = useS(META.periodo);
  const [foco, setFoco] = useS(false);
  const buscaRef = useR(null);

  const ufs = useMemo(() => ["todos", ...Array.from(new Set(MUNICIPIOS.map((m) => m.uf)))], [MUNICIPIOS]);

  const filtrados = useMemo(() => {
    const t = q.trim().toLowerCase();
    return MUNICIPIOS.filter((m) => {
      if (uf !== "todos" && m.uf !== uf) return false;
      if (!t) return true;
      return m.nome.toLowerCase().includes(t) || m.codigo_ibge.includes(t);
    });
  }, [q, uf, MUNICIPIOS]);

  const sugestoes = q.trim() ? filtrados.slice(0, 6) : [];

  if (vazio) {
    return (
      <main>
        <Cabecalho />
        <SeloConfianca meta={META} />
        <div className="vazio-humano" style={{ marginTop: 22 }}>
          <span className="ve-icone" aria-hidden="true"><Icon.mapa style={{ width: 26, height: 26 }} /></span>
          <h3>Ainda não há dados deste período para esta região</h3>
          <p style={{ maxWidth: "44ch", margin: "0 auto" }}>O índice é atualizado mensalmente, à medida que as fontes oficiais publicam. Tente outro período ou volte em breve.</p>
          <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16, flexWrap: "wrap" }}>
            <button className="btn btn-primario" onClick={() => onAbrir("topo")}>Ver período mais recente</button>
            <button className="btn" onClick={() => onAbrir("avise")}>Avisar quando houver dado</button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main>
      <Cabecalho />
      <SeloConfianca meta={META} />

      <div className="controles">
        <div className="busca" ref={buscaRef}>
          <span className="lupa" aria-hidden="true"><Icon.lupa /></span>
          <input
            type="search" value={q} placeholder="Buscar sua cidade ou código IBGE…"
            aria-label="Buscar município por nome ou código IBGE"
            onChange={(e) => setQ(e.target.value)} onFocus={() => setFoco(true)}
            onBlur={() => setTimeout(() => setFoco(false), 150)}
          />
          {foco && sugestoes.length > 0 && (
            <div className="busca-sugestoes" role="listbox">
              {sugestoes.map((m) => (
                <button key={m.codigo_ibge} className="busca-item" role="option" onMouseDown={() => onAbrir("drill", m.codigo_ibge)}>
                  <SemPill estado={m.semaforo} />
                  <span className="bi-nome">{m.nome}</span>
                  <span className="bi-cod mono">{m.uf} · {m.codigo_ibge}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="seletor">
          <label htmlFor="uf">UF</label>
          <select id="uf" value={uf} onChange={(e) => setUf(e.target.value)}>
            {ufs.map((u) => (<option key={u} value={u}>{u === "todos" ? "Todas" : u}</option>))}
          </select>
        </div>
        <div className="seletor">
          <label htmlFor="per">Período</label>
          <select id="per" value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
            {META.periodos.map((p) => (<option key={p} value={p}>{p}</option>))}
          </select>
        </div>
        <div className="seg" role="group" aria-label="Forma de visualização">
          <button aria-pressed={modoMapa === "cartograma"} onClick={() => onAbrir("modo", "cartograma")}><Icon.mapa /> Mapa</button>
          <button aria-pressed={modoMapa === "cartoes"} onClick={() => onAbrir("modo", "cartoes")}><Icon.grade /> Cartões</button>
        </div>
      </div>

      <Legenda />
      <p className="contagem">{filtrados.length} {filtrados.length === 1 ? "município" : "municípios"}{uf !== "todos" ? " em " + uf : ""}{q.trim() ? ` para “${q.trim()}”` : ""} · ordenados do mais ao menos vulnerável</p>

      {filtrados.length === 0 ? (
        <div className="nenhum">
          <p style={{ margin: "0 0 4px", fontWeight: 600, color: "var(--ink)" }}>Nenhuma cidade encontrada para “{q.trim()}”.</p>
          <p style={{ margin: 0 }}>Confira a grafia ou tente o código IBGE. <button className="btn-fantasma" onClick={() => { setQ(""); setUf("todos"); }}>limpar busca</button></p>
        </div>
      ) : modoMapa === "cartograma" ? (
        <Cartograma itens={filtrados} onAbrir={onAbrir} />
      ) : (
        <GradeCartoes itens={filtrados} onAbrir={onAbrir} onCompartilhar={onCompartilhar} />
      )}

      <p id="metodologia" className="mono" style={{ fontSize: "0.74rem", color: "var(--faint)", marginTop: 24, maxWidth: "80ch" }}>
        {META.metodologia} {META.licenca}
      </p>
    </main>
  );
}

function Cabecalho() {
  return (
    <div className="cabecalho">
      <div>
        <div className="sub-eyebrow">Painel cívico · dado público</div>
        <h1 className="titulo-h1">Vulnerabilidade dos municípios</h1>
        <p className="dek">Onde a atenção pública é mais urgente agora — combinando emprego, finanças e saúde num só índice, com a fonte sempre à vista.</p>
      </div>
      <div style={{ marginTop: 6 }}><OQueEhIVM /></div>
    </div>
  );
}

/* ---------- Cartograma (tile map por UF) ---------- */
function Cartograma({ itens, onAbrir }) {
  const porUf = useMemo(() => {
    const g = {};
    itens.forEach((m) => { (g[m.uf] = g[m.uf] || []).push(m); });
    return g;
  }, [itens]);
  return (
    <div className="cartograma">
      {Object.entries(porUf).map(([uf, ms]) => {
        const cols = Math.max(...ms.map((m) => m.col)) + 1;
        const lins = Math.max(...ms.map((m) => m.lin)) + 1;
        return (
          <div className="cartograma-uf" key={uf}>
            <h3>{uf} <span className="qt">· {ms.length} municípios</span></h3>
            <div className="tiles" style={{ gridTemplateColumns: `repeat(${cols}, minmax(76px, 116px))`, gridTemplateRows: `repeat(${lins}, auto)` }}>
              {ms.map((m) => (
                <button key={m.codigo_ibge} className="tile" data-sem={m.semaforo}
                  style={{ gridColumn: m.col + 1, gridRow: m.lin + 1 }}
                  onClick={() => onAbrir("drill", m.codigo_ibge)}
                  aria-label={`${m.nome}: IVM ${m.ivm.toFixed(1)}, ${ROTULO_SEM[m.semaforo]}`}>
                  {(m.v_saude === "suprimido") && <span className="t-icone" aria-hidden="true"><Icon.cadeado style={{ width: 11, height: 11 }} /></span>}
                  <span className="t-nome">{m.nome}</span>
                  <span className="t-ivm tnum">{m.ivm.toFixed(0)}</span>
                </button>
              ))}
            </div>
          </div>
        );
      })}
      <p className="mono" style={{ fontSize: "0.72rem", color: "var(--faint)", margin: 0 }}>
        Cartograma: cada quadro é um município (posição aproximada, não geografia exata). A coropleta geográfica entra quando as malhas do IBGE forem ingeridas — os cartões seguem como alternativa acessível.
      </p>
    </div>
  );
}

/* ---------- Grade de cartões ---------- */
function GradeCartoes({ itens, onAbrir, onCompartilhar }) {
  return (
    <ul className="grade">
      {itens.map((m) => (
        <li key={m.codigo_ibge} className="cartao" data-sem={m.semaforo}>
          <a className="cartao-link" href={"#/ivm/" + m.codigo_ibge} onClick={(e) => { e.preventDefault(); onAbrir("drill", m.codigo_ibge); }}>
            <div className="cartao-topo">
              <div>
                <div className="cartao-nome">{m.nome}</div>
                <div className="cartao-uf mono">{m.uf} · {m.codigo_ibge}</div>
              </div>
              <SemPill estado={m.semaforo} />
            </div>
            <div className="cartao-ivm">
              <span className="valor tnum">{m.ivm.toFixed(1)}</span>
              <span className="un">IVM</span>
              <span className="rotulo">{m.populacao} hab.</span>
            </div>
            <Comparador item={m} />
          </a>
          <div className="cartao-acoes">
            <button className="btn btn-sm btn-fantasma" onClick={() => onCompartilhar(m)}><Icon.compartilhar /> Compartilhar</button>
            <a className="btn btn-sm btn-fantasma" href={"#/ivm/" + m.codigo_ibge} onClick={(e) => { e.preventDefault(); onAbrir("drill", m.codigo_ibge); }} style={{ marginLeft: "auto" }}>Ver detalhe →</a>
          </div>
        </li>
      ))}
    </ul>
  );
}

/* ============================================================ DRILL-DOWN */
function TelaDrill({ codigo, onAbrir, onAcao }) {
  const { MUNICIPIOS, META, SUBINDICES } = window.DADOS;
  const item = MUNICIPIOS.find((m) => m.codigo_ibge === codigo);
  const [comparaCom, setComparaCom] = useS(null);

  const parecidas = useMemo(() => {
    if (!item) return [];
    return MUNICIPIOS.filter((m) => m.codigo_ibge !== item.codigo_ibge && m.uf === item.uf)
      .sort((a, b) => Math.abs(a.ivm - item.ivm) - Math.abs(b.ivm - item.ivm));
  }, [item, MUNICIPIOS]);

  useE(() => { setComparaCom(parecidas[0] ? parecidas[0].codigo_ibge : null); }, [codigo]);
  if (!item) return <main><p>Município não encontrado. <a href="#/ivm" onClick={(e) => { e.preventDefault(); onAbrir("topo"); }}>Voltar</a></p></main>;

  const outra = MUNICIPIOS.find((m) => m.codigo_ibge === comparaCom);
  const significado = {
    verde: `${item.nome} está entre as menos vulneráveis hoje. Vale acompanhar a tendência para não perder terreno.`,
    amarelo: `${item.nome} mostra sinais de atenção. Não é emergência, mas a vulnerabilidade está acima da média — acompanhe de perto.`,
    vermelho: `${item.nome} está entre as mais vulneráveis. Há razão concreta para cobrar prioridade de quem decide.`,
  }[item.semaforo];

  return (
    <main>
      <a className="voltar" href="#/ivm" onClick={(e) => { e.preventDefault(); onAbrir("topo"); }}><Icon.seta /> Voltar ao mapa</a>

      <div className="dd-hero">
        <div>
          <div className="sub-eyebrow">{item.uf} · {item.codigo_ibge} · {item.populacao} hab.</div>
          <h1 className="titulo-h1" style={{ fontSize: "2rem", marginTop: 2 }}>{item.nome}</h1>
          <div className="dd-ivm-bloco" style={{ marginTop: 10 }}>
            <span className="num tnum" style={{ color: "var(--ink)" }}>{item.ivm.toFixed(1)}</span>
            <span className="un">/ 100 IVM</span>
            <SemPill estado={item.semaforo} />
          </div>
        </div>
        <div style={{ alignSelf: "center" }}><OQueEhIVM /></div>
      </div>

      <div className="dd-significado" data-sem={item.semaforo}>{significado}</div>

      <div className="acoes-barra">
        <button className="btn btn-primario" onClick={() => onAcao("compartilhar", item)}><Icon.compartilhar /> Compartilhar</button>
        <button className="btn" onClick={() => onAcao("exportar", item)}><Icon.baixar /> Exportar com citação</button>
        <button className="btn" onClick={() => onAcao("alerta", item)}><Icon.sino /> Avise-me se piorar</button>
        <a className="btn btn-fantasma" href="#ouvidoria" style={{ marginLeft: "auto", whiteSpace: "nowrap" }}><Icon.megafone /> A quem cobrar <Icon.externo /></a>
      </div>

      <div className="dd-grid">
        <div style={{ display: "grid", gap: 18 }}>
          <section className="painel">
            <h2>Subíndices de vulnerabilidade</h2>
            <p className="painel-sub">{item.periodo} · maior = mais vulnerável · uma célula 🔒 é dado protegido, não zero</p>
            <Comparador item={item} detalhado />
            <div style={{ display: "grid", gap: 6, marginTop: 14, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
              {SUBINDICES.map((s) => (
                <p key={s.chave} style={{ margin: 0, fontSize: "0.78rem", color: "var(--faint)" }}>
                  <strong className="mono" style={{ color: "var(--muted)" }}>{s.rotulo}</strong> · {s.fonte} — {s.desc}
                </p>
              ))}
            </div>
          </section>

          <section className="painel">
            <h2>Comparar com cidade parecida</h2>
            <p className="painel-sub">Mesma UF, IVM próximo — para enxergar se o problema é local ou regional.</p>
            <div className="comparar-row">
              <div className="mini-cidade" style={{ borderColor: "var(--marca)" }}>
                <div className="mc-nome">{item.nome} <SemPill estado={item.semaforo} /></div>
                <div className="mc-ivm tnum">{item.ivm.toFixed(1)}</div>
                <Comparador item={item} />
              </div>
              <div className="comparar-vs">vs</div>
              <div className="mini-cidade">
                <div className="mc-nome" style={{ marginBottom: 6 }}>
                  <select value={comparaCom || ""} onChange={(e) => setComparaCom(e.target.value)} aria-label="Escolher cidade para comparar" style={{ font: "inherit", border: "1px solid var(--border-strong)", borderRadius: 8, padding: "4px 8px", maxWidth: "100%" }}>
                    {parecidas.map((p) => (<option key={p.codigo_ibge} value={p.codigo_ibge}>{p.nome}</option>))}
                  </select>
                </div>
                {outra && <><div className="mc-ivm tnum">{outra.ivm.toFixed(1)} <SemPill estado={outra.semaforo} /></div><Comparador item={outra} /></>}
              </div>
            </div>
          </section>
        </div>

        <div style={{ display: "grid", gap: 18 }}>
          <section className="painel">
            <h2>Evolução do IVM</h2>
            <p className="painel-sub">14 meses · cada ponto é um mês de dado oficial</p>
            <SerieTemporal serie={item.serie} />
            <p style={{ fontSize: "0.78rem", color: "var(--muted)", margin: "10px 0 0" }}>
              {item.serie[item.serie.length - 1].ivm > item.serie[0].ivm
                ? <>Tendência de <strong style={{ color: "var(--vermelho)" }}>piora</strong> no período. </>
                : <>Tendência de <strong style={{ color: "var(--verde)" }}>melhora</strong> no período. </>}
              Pontos suprimidos por privacidade seriam marcados, nunca omitidos.
            </p>
          </section>

          <section className="painel" style={{ background: "var(--surface-2)" }}>
            <h2 style={{ display: "flex", alignItems: "center", gap: 8 }}><Icon.escudo /> De onde vem este número</h2>
            <div style={{ marginTop: 10 }}><SeloConfianca meta={META} /></div>
          </section>
        </div>
      </div>
    </main>
  );
}

Object.assign(window, { TelaTopo, TelaDrill });
