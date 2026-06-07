import { corPulso, rotuloPulso } from "../lib/pulso";
import type { Pulso } from "../lib/types";

// Selo do NÍVEL do pulso (a batida do mês). Acessibilidade: a cor é redundante com o texto
// (nunca só cor) + descrição em sr-only — mesmo primitivo do Semaforo (ADR-0009).
export function PulsoSelo({ estado }: { estado: Pulso }) {
  const rotulo = rotuloPulso(estado);
  return (
    <span className={`pulso-selo pulso-${estado}`} title={rotulo}>
      <span className="pulso-dot" style={{ backgroundColor: corPulso(estado) }} aria-hidden="true" />
      <span className="pulso-rotulo">{rotulo}</span>
      <span className="sr-only"> — pulso do emprego formal: {rotulo}</span>
    </span>
  );
}
