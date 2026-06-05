import { corSemaforo, rotuloSemaforo } from "../lib/semaforo";
import type { Semaforo as EstadoSemaforo } from "../lib/types";

// Acessibilidade: a cor é redundante com o texto (nunca só cor).
export function Semaforo({ estado }: { estado: EstadoSemaforo }) {
  return (
    <span className="semaforo" title={rotuloSemaforo(estado)}>
      <span
        className="semaforo-dot"
        style={{ backgroundColor: corSemaforo(estado) }}
        aria-hidden="true"
      />
      <span className="semaforo-rotulo">{estado}</span>
      <span className="sr-only"> — {rotuloSemaforo(estado)}</span>
    </span>
  );
}
