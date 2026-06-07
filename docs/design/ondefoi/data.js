/* OndeFoi — execução orçamentária municipal (SICONFI). Mock para protótipo.
   HONESTIDADE: SICONFI mostra EXECUÇÃO (empenho/liquidação), NÃO serviço entregue.
   Estado de função: "valor" | "suprimido" | "sem_cobertura" (campo aditivo, não quebra contrato). */
(function () {
  // banda de execução é sinal de ATENÇÃO (merece pergunta), não juízo de "bom/ruim".
  function banda(pct) {
    if (pct == null) return "indef";
    if (pct >= 80) return "alta";     // executou quase tudo — confira se virou serviço
    if (pct >= 55) return "parcial";  // execução parcial
    return "baixa";                    // executou pouco do que recebeu — merece a pergunta
  }

  // recebido em milhões de R$; executado idem; pct derivado.
  const RAW = [
    { c: "3304557", n: "Rio de Janeiro", uf: "RJ", rec: 41200, funcoes: [
      { f: "Saúde", rec: 9800, exe: 8120 },
      { f: "Educação", rec: 8600, exe: 7310 },
      { f: "Assistência social", rec: 2400, exe: 1490 },
      { f: "Urbanismo", rec: 5200, exe: 2860 },
      { f: "Saneamento", rec: 1800, exe: "suprimido" },
      { f: "Cultura", rec: 700, exe: "sem_cobertura" },
    ] },
    { c: "3550308", n: "São Paulo", uf: "SP", rec: 78900, funcoes: [
      { f: "Saúde", rec: 18200, exe: 16930 },
      { f: "Educação", rec: 17400, exe: 16240 },
      { f: "Assistência social", rec: 4100, exe: 3360 },
      { f: "Urbanismo", rec: 9800, exe: 7250 },
      { f: "Saneamento", rec: 3200, exe: 2880 },
      { f: "Cultura", rec: 1500, exe: 1140 },
    ] },
    { c: "3106200", n: "Belo Horizonte", uf: "MG", rec: 15600, funcoes: [
      { f: "Saúde", rec: 4100, exe: 3650 },
      { f: "Educação", rec: 3800, exe: 3420 },
      { f: "Assistência social", rec: 980, exe: 690 },
      { f: "Urbanismo", rec: 2300, exe: 1240 },
      { f: "Saneamento", rec: 740, exe: "suprimido" },
      { f: "Cultura", rec: 320, exe: 210 },
    ] },
    { c: "3303500", n: "Nova Iguaçu", uf: "RJ", rec: 4900, funcoes: [
      { f: "Saúde", rec: 1320, exe: 760 },
      { f: "Educação", rec: 1180, exe: 880 },
      { f: "Assistência social", rec: 360, exe: 150 },
      { f: "Urbanismo", rec: 540, exe: 190 },
      { f: "Saneamento", rec: 210, exe: "sem_cobertura" },
      { f: "Cultura", rec: 90, exe: "suprimido" },
    ] },
    { c: "3543402", n: "Ribeirão Preto", uf: "SP", rec: 6300, funcoes: [
      { f: "Saúde", rec: 1640, exe: 1510 },
      { f: "Educação", rec: 1490, exe: 1360 },
      { f: "Assistência social", rec: 410, exe: 330 },
      { f: "Urbanismo", rec: 760, exe: 520 },
      { f: "Saneamento", rec: 280, exe: 240 },
      { f: "Cultura", rec: 120, exe: 80 },
    ] },
    { c: "3154606", n: "Ribeirão das Neves", uf: "MG", rec: 2100, funcoes: [
      { f: "Saúde", rec: 560, exe: 240 },
      { f: "Educação", rec: 520, exe: 360 },
      { f: "Assistência social", rec: 160, exe: 60 },
      { f: "Urbanismo", rec: 230, exe: 70 },
      { f: "Saneamento", rec: 90, exe: "sem_cobertura" },
      { f: "Cultura", rec: 40, exe: "suprimido" },
    ] },
  ];

  function pct(rec, exe) { return typeof exe === "number" ? Math.round((exe / rec) * 100) : null; }

  const MUNICIPIOS = RAW.map((m) => {
    const funcoes = m.funcoes.map((fn) => ({
      ...fn,
      estado: typeof fn.exe === "number" ? "valor" : fn.exe, // "valor" | "suprimido" | "sem_cobertura"
      pct: pct(fn.rec, fn.exe),
    }));
    // BASE ÚNICA DO % (definição do indicador, espelha o backend):
    //   numerador  = despesa executada das funções DIVULGADAS (estado="valor")
    //   denominador = recebido dessas MESMAS funções divulgadas (recDivulgado)
    // A parcela do recebido fora dessa base (protegida, sem cobertura ou não detalhada
    // por função) é EXPLÍCITA (recForaCalculo) — nunca tirada silenciosamente do denominador.
    const executado = funcoes.filter((f) => f.estado === "valor").reduce((s, f) => s + f.exe, 0);
    const recDivulgado = funcoes.filter((f) => f.estado === "valor").reduce((s, f) => s + f.rec, 0);
    const pctGeral = Math.round((executado / recDivulgado) * 100);
    const recForaCalculo = m.rec - recDivulgado; // total recebido − base divulgada
    return {
      codigo_ibge: m.c, nome: m.n, uf: m.uf,
      recebido: m.rec,            // total recebido (exibido como contexto, NUNCA como denominador do %)
      recDivulgado,               // denominador do % (mesma base do "executado")
      executado,                  // numerador do %
      recForaCalculo,             // parcela explícita fora do cálculo
      pctGeral, banda: banda(pctGeral), funcoes,
    };
  }).sort((a, b) => a.pctGeral - b.pctGeral);

  const META = {
    nome: "Execução orçamentária municipal",
    versao_metodologia: "v1",
    periodo_rotulo: "exercício 2025",
    atraso_dias: 75,
    fontes: [
      { sigla: "SICONFI", nome: "Sistema de Informações Contábeis e Fiscais — RREO/DCA", orgao: "Tesouro Nacional / STN", dominio: "Finanças públicas", ate: "2025 (anual)", atraso: "~75 dias após o bimestre" },
    ],
    metodologia:
      "Execução = razão entre despesa liquidada e dotação/receita recebida por função orçamentária, no exercício. Mede que o recurso saiu do orçamento — NÃO que o serviço chegou à ponta.",
    licenca: "Dados públicos (SICONFI) · Licença aberta. Atribuição: DadoSabedoria.",
  };

  window.ONDEFOI = { MUNICIPIOS, META, banda };
})();
