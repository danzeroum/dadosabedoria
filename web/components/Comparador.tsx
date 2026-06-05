function Barra({ rotulo, valor }: { rotulo: string; valor: number }) {
  const pct = Math.max(0, Math.min(100, valor));
  return (
    <div className="barra-linha">
      <span className="barra-rotulo">{rotulo}</span>
      <span className="barra-trilha" aria-hidden="true">
        <span className="barra-preenchida" style={{ width: `${pct}%` }} />
      </span>
      <span className="barra-valor">{valor.toFixed(0)}</span>
    </div>
  );
}

// Compara os subíndices de vulnerabilidade (maior = mais vulnerável).
export function Comparador({ vEmprego, vFinancas }: { vEmprego: number; vFinancas: number }) {
  return (
    <div className="comparador" role="group" aria-label="Subíndices de vulnerabilidade">
      <Barra rotulo="Emprego" valor={vEmprego} />
      <Barra rotulo="Finanças" valor={vFinancas} />
    </div>
  );
}
