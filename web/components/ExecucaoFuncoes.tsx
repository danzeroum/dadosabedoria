import { formatarPct, formatarReais } from "../lib/onde-foi";
import type { FuncaoOut } from "../lib/types";
import { EstadoSupressao } from "./EstadoSupressao";

// Recebido × executado por função. Onde não há valor, reusa o primitivo EstadoSupressao (o mesmo
// do IVM) — no OndeFoi só aparece "sem cobertura" (orçamento público não tem cadeado). Tabela
// semântica (th/scope) para acessibilidade.
export function ExecucaoFuncoes({ funcoes }: { funcoes: FuncaoOut[] }) {
  return (
    <table className="funcoes">
      <caption className="sr-only">Recebido e executado por função</caption>
      <thead>
        <tr>
          <th scope="col">Função</th>
          <th scope="col">Recebido</th>
          <th scope="col">Executado</th>
          <th scope="col">% do recebido</th>
        </tr>
      </thead>
      <tbody>
        {funcoes.map((f) => (
          <tr key={f.funcao}>
            <th scope="row">{f.funcao}</th>
            <td className="num">{formatarReais(f.recebido)}</td>
            <td className="num">
              {f.exe_estado === "valor" ? (
                f.exe != null ? (
                  formatarReais(f.exe)
                ) : (
                  "—"
                )
              ) : (
                <EstadoSupressao estado={f.exe_estado} rotulo="Execução" />
              )}
            </td>
            <td className="num">
              {f.pct != null ? (
                <span className="funcao-pct">
                  <span className="funcao-barra" aria-hidden="true">
                    <span
                      className="funcao-preenchida"
                      style={{ width: `${Math.min(100, f.pct)}%` }}
                    />
                  </span>
                  <span className="funcao-pct-num">{formatarPct(f.pct)}</span>
                </span>
              ) : (
                <span className="funcao-pct-num">{formatarPct(f.pct)}</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
