import { buscarCoberturaPncp } from "../lib/api";

/**
 * Banner de modo demonstração da família PNCP (ObraViva).
 *
 * Renderizado server-side; retorna null quando a cobertura for nacional (≥50 municípios).
 * Não requer JS no cliente. O aviso cai automaticamente após a ingestão nacional.
 */
export async function DemoAvisoPncp() {
  const cob = await buscarCoberturaPncp();
  if (!cob?.demo) return null;
  return (
    <aside className="demo-aviso" role="note" aria-label="Dados de demonstração">
      <strong>Demonstração</strong> —{" "}
      {cob.aviso ??
        "Dados de seed (teste). O aviso cai automaticamente após a ingestão nacional do PNCP."}
    </aside>
  );
}
