import Link from "next/link";

import { corSemaforo, formatarIVM } from "../lib/semaforo";
import type { IVMItem } from "../lib/types";
import { Comparador } from "./Comparador";
import { Semaforo } from "./Semaforo";

// Painel semafórico: um cartão por município, ordenado do mais ao menos vulnerável.
// (A coropleta geográfica chega quando as malhas do IBGE forem ingeridas — ver ADR-0009.)
export function MapaSemaforico({ itens }: { itens: IVMItem[] }) {
  if (itens.length === 0) {
    return (
      <p className="vazio">
        Sem dados de IVM para o período. Rode a ingestão (CAGED + ESTBAN) e o refresh do IVM.
      </p>
    );
  }
  return (
    <ul className="mapa-grid">
      {itens.map((it) => (
        <li
          key={it.codigo_ibge}
          className="card"
          style={{ borderInlineStartColor: corSemaforo(it.semaforo) }}
        >
          <Link href={`/ivm/${it.codigo_ibge}`} className="card-link">
            <div className="card-topo">
              <span className="card-nome">{it.nome}</span>
              <Semaforo estado={it.semaforo} />
            </div>
            <div className="card-ivm">
              <strong>{formatarIVM(it.ivm)}</strong>
              <span className="card-ivm-rotulo">IVM</span>
            </div>
            <Comparador
              vEmprego={it.v_emprego}
              vFinancas={it.v_financas}
              vSaude={it.v_saude}
              vSaudeEstado={it.v_saude_estado}
            />
          </Link>
        </li>
      ))}
    </ul>
  );
}
