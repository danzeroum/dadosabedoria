import { buscarCoberturaSnis } from "../lib/api";

/**
 * Banner de modo demonstração da família SNIS (AguaViva, EsgotoInvisível).
 *
 * Renderizado server-side; retorna null quando a cobertura for nacional (≥50 municípios).
 * Não requer JS no cliente. O aviso cai automaticamente após a ingestão nacional.
 */
export async function DemoAvisoSnis() {
  const cob = await buscarCoberturaSnis();
  if (!cob?.demo) return null;
  return (
    <aside className="demo-aviso" role="note" aria-label="Dados de demonstração">
      <strong>Demonstração</strong> —{" "}
      {cob.aviso ??
        "Dados de seed (teste). O aviso cai automaticamente após a ingestão nacional do SNIS."}
    </aside>
  );
}
