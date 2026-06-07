// Abre as telas do IVM num Chromium headless e salva PNGs (artefato de CI + smoke visual).
// Captura SEMPRE (mesmo em erro, para o artefato mostrar o estado); falha o processo se
// alguma página não responder 2xx — assim a tela quebrada reprova o job, mas o PNG fica disponível.
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";

const BASE = process.env.WEB_URL ?? "http://localhost:3000";
const OUT = process.env.OUT_DIR ?? "capturas";

const paginas = [
  { nome: "home", url: `${BASE}/` }, // porta de entrada: os produtos como perguntas
  { nome: "ivm-mapa", url: `${BASE}/ivm` }, // cartões semafóricos + subíndices
  { nome: "ivm-municipio-sp", url: `${BASE}/ivm/3550308` }, // drill-down: série + proveniência
  { nome: "pulso-sp", url: `${BASE}/pulso/3550308` }, // TRAB-01: saldo de emprego formal
  { nome: "onde-foi-rio", url: `${BASE}/onde-foi/3304557` }, // TRANSP-06: execução + sem cobertura
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1800 } });

let falhas = 0;
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
  console.log(`capturado ${OUT}/${p.nome}.png — ${p.url} (status ${status})`);
}

await browser.close();
if (falhas > 0) {
  console.error(`::error::${falhas} página(s) não retornaram 2xx — ver o artefato telas-ivm.`);
  process.exit(1);
}
