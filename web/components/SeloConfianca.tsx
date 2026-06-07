import type { SeloMeta } from "../lib/types";

// Selo de confiança (frescor + proveniência) — primitivo COMPARTILHADO (OndeFoi ↔ IVM), portado do
// handoff de design. Usa <details> nativo: o "ver fontes" é acessível e sem JS no cliente. A cor do
// ponto de frescor é redundante com o texto ("atraso típico ~N dias" + sr-only), nunca só cor.
export function SeloConfianca({ meta }: { meta: SeloMeta }) {
  const fresco = meta.atraso_dias <= 60;
  return (
    <details className="selo">
      <summary className="selo-cabeca">
        <span className="selo-shield" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        </span>
        <span className="selo-meta">
          <span className="selo-linha1">
            <strong>Fonte verificada</strong>
            <span className="selo-fontes">
              {meta.fontes.map((f) => (
                <span key={f.sigla} className="chip-fonte">
                  {f.sigla}
                </span>
              ))}
            </span>
          </span>
          <span className="selo-frescor">
            <span className={`frescor-dot ${fresco ? "fresco" : "atencao"}`} aria-hidden="true" />
            <span>
              Dado até <strong>{meta.periodo_rotulo}</strong> · atraso típico ~{meta.atraso_dias}{" "}
              dias · metodologia {meta.versao_metodologia}
            </span>
            <span className="sr-only">
              {" "}
              — {fresco ? "dado recente" : "atenção: dado com atraso típico maior"}
            </span>
          </span>
        </span>
        <span className="selo-toggle">ver fontes</span>
      </summary>
      <div className="selo-detalhe">
        {meta.fontes.map((f) => (
          <div key={f.sigla} className="selo-fonte-row">
            <span className="selo-sig">{f.sigla}</span>
            <span className="selo-org">
              {f.nome} · <span className="selo-faint">{f.orgao}</span> · domínio {f.dominio}
            </span>
            <span className="selo-ate">
              até {f.ate} · {f.atraso}
            </span>
          </div>
        ))}
        <p className="selo-rodape">{meta.licenca}</p>
      </div>
    </details>
  );
}
