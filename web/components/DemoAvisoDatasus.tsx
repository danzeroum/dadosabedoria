import { buscarCoberturaDatasus } from "../lib/api";

/**
 * Banner de modo demonstração da família DATASUS/SIH (Sentinela Respiratória).
 *
 * Renderizado server-side; retorna null quando a cobertura for nacional (≥50 municípios).
 * Não requer JS no cliente. O aviso cai automaticamente após a ingestão nacional.
 */
export async function DemoAvisoDatasus() {
  const cob = await buscarCoberturaDatasus();
  if (!cob?.demo) return null;
  return (
    <aside className="demo-aviso" role="note" aria-label="Dados de demonstração">
      <strong>Demonstração</strong> —{" "}
      {cob.aviso ??
        "Dados de seed (teste). O aviso cai automaticamente após a ingestão nacional do DATASUS/SIH."}
    </aside>
  );
}
