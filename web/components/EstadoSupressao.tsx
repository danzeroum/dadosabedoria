import type { ExeEstado } from "../lib/types";

// Chip honesto do estado de uma célula/subíndice (padrão *_estado, ADR-0026), compartilhado
// IVM↔OndeFoi. Distingue "suprimido" (cadeado de privacidade: há PII por baixo, k-anonimato) de
// "sem_cobertura" (não há dado). Acessível: a cor nunca carrega sentido sozinha — o texto diz.
const ROTULO: Record<Exclude<ExeEstado, "valor">, { curto: string; descricao: string }> = {
  suprimido: {
    curto: "protegido",
    descricao: "valor suprimido por privacidade (k-anonimato) — há dado pessoal por baixo",
  },
  sem_cobertura: { curto: "sem cobertura", descricao: "não há dado para este período" },
};

export function EstadoSupressao({
  estado,
  rotulo,
}: {
  estado: Exclude<ExeEstado, "valor">;
  rotulo: string;
}) {
  const { curto, descricao } = ROTULO[estado];
  return (
    <span className={`estado-supressao estado-${estado}`} title={`${rotulo}: ${descricao}`}>
      <span className="estado-icone" aria-hidden="true">
        {estado === "suprimido" ? "🔒" : "—"}
      </span>
      <span className="estado-rotulo">
        {rotulo}: {curto}
      </span>
      <span className="sr-only"> — {descricao}</span>
    </span>
  );
}
