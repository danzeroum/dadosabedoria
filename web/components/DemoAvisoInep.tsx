import { buscarCoberturaInep } from "../lib/api";

/**
 * Banner de modo demonstração da família INEP (Radar de Evasão Escolar).
 *
 * Renderizado server-side; retorna null quando a cobertura for nacional (≥50 municípios).
 * Não requer JS no cliente. O aviso cai automaticamente após a ingestão nacional.
 */
export async function DemoAvisoInep() {
  const cob = await buscarCoberturaInep();
  if (!cob?.demo) return null;
  return (
    <aside className="demo-aviso" role="note" aria-label="Dados de demonstração">
      <strong>Demonstração</strong> —{" "}
      {cob.aviso ??
        "Dados de seed (teste). O aviso cai automaticamente após a ingestão nacional do INEP/Censo Escolar."}
    </aside>
  );
}
