import { COR_SEM_DADO, ESTADOS, corSemaforo, rotuloSemaforo } from "../lib/semaforo";

// Legenda do semáforo — acessível: a bolinha de cor é decorativa (aria-hidden); o estado e a
// descrição são texto. Inclui a faixa numérica (meta) e a célula "sem dado".
export function Legenda({ faixas }: { faixas: Record<string, string> }) {
  return (
    <ul className="legenda" aria-label="Legenda do semáforo de vulnerabilidade">
      {ESTADOS.map((s) => (
        <li key={s}>
          <span
            className="semaforo-dot"
            style={{ backgroundColor: corSemaforo(s) }}
            aria-hidden="true"
          />
          <strong>{s}</strong>: {rotuloSemaforo(s)}
          {faixas[s] ? ` (${faixas[s]})` : null}
        </li>
      ))}
      <li>
        <span className="semaforo-dot" style={{ backgroundColor: COR_SEM_DADO }} aria-hidden="true" />
        sem dado
      </li>
    </ul>
  );
}
