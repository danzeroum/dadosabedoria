// Abre as telas num Chromium headless, salva PNGs (artefato de CI + smoke visual) E roda o axe
// (auditoria WCAG no DOM vivo — ADR-0009). Captura SEMPRE (mesmo em erro). Reprova o job se alguma
// página não responder 2xx OU se houver violação WCAG serious/critical — mas os PNGs ficam disponíveis.
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";

const BASE = process.env.WEB_URL ?? "http://localhost:3000";
const OUT = process.env.OUT_DIR ?? "capturas";
// Só as regras de conformidade WCAG (A/AA), sem as "best-practice" (ruído) — o gate é WCAG.
const TAGS_WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

const paginas = [
  { nome: "home", url: `${BASE}/` }, // porta de entrada: os produtos como perguntas
  { nome: "ivm-mapa", url: `${BASE}/ivm` }, // cartões semafóricos + subíndices
  { nome: "ivm-municipio-sp", url: `${BASE}/ivm/3550308` }, // drill-down: série + proveniência
  { nome: "pulso-sp", url: `${BASE}/pulso/3550308` }, // TRAB-01: saldo de emprego formal
  { nome: "onde-foi-rio", url: `${BASE}/onde-foi/3304557` }, // TRANSP-06: execução + sem cobertura
  { nome: "municipio-campinas", url: `${BASE}/municipio/3509502` }, // panorama: domínios + protegido
  {
    nome: "ia-perguntar",
    url: `${BASE}/perguntar?q=${encodeURIComponent("Como está o emprego formal em São Paulo?")}&indicador=trabalho.emprego.saldo_caged&territorio=3550308`,
  }, // IA ancorada: resposta + citações
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1800 } });

let falhas = 0;
let violacoesGraves = 0;
for (const p of paginas) {
  let status = "sem-resposta";
  try {
    const resp = await page.goto(p.url, { waitUntil: "networkidle", timeout: 60000 });
    status = resp ? String(resp.status()) : "sem-resposta";
    if (!resp || !resp.ok()) falhas++;
  } catch (e) {
    falhas++;
    console.error(`exceção em ${p.url}: ${e.message}`);
  }
  await page.screenshot({ path: `${OUT}/${p.nome}.png`, fullPage: true });

  // Axe: auditoria WCAG no DOM renderizado. Falha o job em violações serious/critical — exceto
  // `color-contrast`, que é REPORTADA (warning) até uma auditoria de tokens dedicada (precisa de
  // ferramenta visual; o gate de estrutura WCAG já reprova o resto).
  try {
    const { violations } = await new AxeBuilder({ page }).withTags(TAGS_WCAG).analyze();
    const graves = violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    for (const v of graves) {
      const bloqueia = v.id !== "color-contrast";
      if (bloqueia) violacoesGraves++;
      const alvos = v.nodes
        .slice(0, 3)
        .map((n) => n.target.join(" "))
        .join(" | ");
      const nivel = bloqueia ? "::error::" : "::warning::";
      console.error(`${nivel}axe [${p.nome}] ${v.impact} · ${v.id}: ${v.help} → ${alvos}`);
    }
    console.log(`axe ${p.nome}: ${graves.length} grave(s) de ${violations.length} violação(ões)`);
  } catch (e) {
    falhas++;
    console.error(`axe falhou em ${p.nome}: ${e.message}`);
  }
  console.log(`capturado ${OUT}/${p.nome}.png — ${p.url} (status ${status})`);
}

await browser.close();
if (falhas > 0) {
  console.error(`::error::${falhas} página(s) não retornaram 2xx (ou axe falhou) — ver o artefato.`);
  process.exit(1);
}
if (violacoesGraves > 0) {
  console.error(`::error::${violacoesGraves} violação(ões) WCAG serious/critical (axe) — corrigir.`);
  process.exit(1);
}
