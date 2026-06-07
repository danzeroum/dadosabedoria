import { banda, formatarMilhoes } from "../lib/onde-foi";
import type { FuncaoOut } from "../lib/types";
import { EstadoSupressao } from "./EstadoSupressao";
import { ExecPill } from "./ExecPill";

// Recebido × executado por função (handoff de design): a trilha mostra quanto do recebido foi
// executado (valor dentro da barra), com a ExecPill ao lado. A barra é decorativa (aria-hidden);
// um sr-only diz o executado absoluto, então o leitor de tela não perde nada. Onde não há valor,
// reusa o primitivo EstadoSupressao (mesmo do IVM) — protegido (privacidade) ou sem cobertura.
export function ExecucaoFuncoes({ funcoes }: { funcoes: FuncaoOut[] }) {
  return (
    <ul className="funcoes" aria-label="Execução por função">
      {funcoes.map((f) => (
        <li key={f.funcao} className="funcao">
          <span className="funcao-nome">
            {f.funcao}
            <small>recebeu {formatarMilhoes(f.recebido)}</small>
          </span>
          {f.exe_estado !== "valor" ? (
            <>
              <span className="funcao-sup-wrap">
                <EstadoSupressao estado={f.exe_estado} rotulo="Execução" />
              </span>
              <span className="funcao-pct funcao-pct-vazio" aria-hidden="true">
                —
              </span>
            </>
          ) : f.exe != null && f.pct != null ? (
            <>
              <span className="funcao-trilha" aria-hidden="true">
                <span
                  className={`funcao-exe banda-${banda(f.pct)}`}
                  style={{ width: `${Math.max(8, Math.min(100, f.pct))}%` }}
                >
                  <span>{formatarMilhoes(f.exe)}</span>
                </span>
              </span>
              <span className="sr-only">executou {formatarMilhoes(f.exe)}</span>
              <span className="funcao-pct">
                <ExecPill banda={banda(f.pct)} pct={f.pct} />
              </span>
            </>
          ) : (
            <>
              <span className="funcao-sup-wrap" />
              <span className="funcao-pct funcao-pct-vazio" aria-hidden="true">
                —
              </span>
            </>
          )}
        </li>
      ))}
    </ul>
  );
}
