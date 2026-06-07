/* DadoSabedoria — dados mock do IVM (protótipo de UX).
   Honestidade do dado: v_saude pode ser número, "suprimido" (privacidade, k-anonimato)
   ou "sem_cobertura" (não há ingestão de SIH p/ o território). Nunca tratar como 0.
   IVM 0..100, maior = mais vulnerável. Classificação ADR-0008: <33 verde, 33-66 amarelo, >66 vermelho. */
(function () {
  function classificar(ivm) {
    if (ivm < 33) return "verde";
    if (ivm <= 66) return "amarelo";
    return "vermelho";
  }

  // Gera uma série mensal plausível terminando no período atual, com leve tendência + ruído.
  function serie(base, tendencia, n, seed) {
    let s = seed || 1;
    const rnd = () => {
      s = (s * 9301 + 49297) % 233280;
      return s / 233280;
    };
    const meses = [];
    const fim = { ano: 2026, mes: 4 }; // dado até abr/2026
    for (let i = n - 1; i >= 0; i--) {
      let m = fim.mes - i,
        a = fim.ano;
      while (m <= 0) {
        m += 12;
        a -= 1;
      }
      const periodo = a + "-" + String(m).padStart(2, "0");
      const drift = tendencia * (n - 1 - i);
      const noise = (rnd() - 0.5) * 6;
      let v = Math.max(2, Math.min(98, base - tendencia * (n - 1) + drift + noise));
      meses.push({ periodo, ivm: Math.round(v * 10) / 10 });
    }
    return meses;
  }

  // uf, col/lin = posição no cartograma (grade aproximada por UF, honestamente um cartograma, não geografia).
  const RAW = [
    // ——— São Paulo ———
    { c: "3550308", n: "São Paulo", uf: "SP", ivm: 28.4, emp: 24, fin: 31, sau: 30, col: 2, lin: 2, pop: "11,4 mi", tend: -0.4 },
    { c: "3509502", n: "Campinas", uf: "SP", ivm: 31.9, emp: 29, fin: 34, sau: 33, col: 1, lin: 1, pop: "1,2 mi", tend: -0.2 },
    { c: "3548708", n: "Santos", uf: "SP", ivm: 37.2, emp: 35, fin: 39, sau: 38, col: 3, lin: 3, pop: "433 mil", tend: 0.3 },
    { c: "3543402", n: "Ribeirão Preto", uf: "SP", ivm: 34.0, emp: 30, fin: 37, sau: "suprimido", col: 1, lin: 0, pop: "720 mil", tend: 0.1 },
    { c: "3552205", n: "Sorocaba", uf: "SP", ivm: 41.6, emp: 44, fin: 40, sau: 41, col: 0, lin: 2, pop: "695 mil", tend: 0.5 },
    { c: "3547809", n: "Santo André", uf: "SP", ivm: 39.1, emp: 38, fin: 41, sau: 38, col: 3, lin: 2, pop: "722 mil", tend: 0.2 },
    { c: "3534401", n: "Osasco", uf: "SP", ivm: 46.8, emp: 49, fin: 45, sau: "suprimido", col: 1, lin: 2, pop: "699 mil", tend: 0.6 },
    { c: "3525904", n: "Jundiaí", uf: "SP", ivm: 29.7, emp: 26, fin: 32, sau: 31, col: 2, lin: 1, pop: "424 mil", tend: -0.3 },
    { c: "3548906", n: "São Vicente", uf: "SP", ivm: 58.3, emp: 61, fin: 55, sau: 59, col: 3, lin: 4, pop: "368 mil", tend: 1.1 },
    { c: "3513801", n: "Cubatão", uf: "SP", ivm: 67.9, emp: 71, fin: 64, sau: "sem_cobertura", col: 2, lin: 4, pop: "133 mil", tend: 1.4 },
    { c: "3506003", n: "Bauru", uf: "SP", ivm: 42.1, emp: 40, fin: 44, sau: 43, col: 0, lin: 1, pop: "379 mil", tend: 0.3 },
    { c: "3530607", n: "Mauá", uf: "SP", ivm: 61.5, emp: 64, fin: 58, sau: 62, col: 4, lin: 3, pop: "477 mil", tend: 0.9 },

    // ——— Rio de Janeiro ———
    { c: "3304557", n: "Rio de Janeiro", uf: "RJ", ivm: 44.2, emp: 47, fin: 41, sau: 45, col: 2, lin: 2, pop: "6,2 mi", tend: 0.4 },
    { c: "3303302", n: "Niterói", uf: "RJ", ivm: 33.5, emp: 30, fin: 36, sau: 34, col: 3, lin: 2, pop: "513 mil", tend: -0.1 },
    { c: "3301702", n: "Duque de Caxias", uf: "RJ", ivm: 64.8, emp: 68, fin: 61, sau: "suprimido", col: 2, lin: 1, pop: "924 mil", tend: 1.2 },
    { c: "3304904", n: "São Gonçalo", uf: "RJ", ivm: 59.0, emp: 62, fin: 56, sau: 60, col: 3, lin: 1, pop: "1,1 mi", tend: 0.8 },
    { c: "3303500", n: "Nova Iguaçu", uf: "RJ", ivm: 68.7, emp: 72, fin: 64, sau: 70, col: 1, lin: 1, pop: "823 mil", tend: 1.5 },
    { c: "3300456", n: "Belford Roxo", uf: "RJ", ivm: 73.4, emp: 77, fin: 68, sau: "sem_cobertura", col: 1, lin: 0, pop: "511 mil", tend: 1.7 },
    { c: "3301009", n: "Campos dos Goytacazes", uf: "RJ", ivm: 49.3, emp: 51, fin: 47, sau: 50, col: 4, lin: 0, pop: "511 mil", tend: 0.5 },
    { c: "3304144", n: "Petrópolis", uf: "RJ", ivm: 38.6, emp: 36, fin: 40, sau: "suprimido", col: 1, lin: 2, pop: "306 mil", tend: 0.0 },

    // ——— Minas Gerais ———
    { c: "3106200", n: "Belo Horizonte", uf: "MG", ivm: 32.7, emp: 29, fin: 35, sau: 34, col: 2, lin: 2, pop: "2,3 mi", tend: -0.2 },
    { c: "3170206", n: "Uberlândia", uf: "MG", ivm: 30.1, emp: 27, fin: 33, sau: 31, col: 0, lin: 1, pop: "713 mil", tend: -0.3 },
    { c: "3118601", n: "Contagem", uf: "MG", ivm: 48.5, emp: 51, fin: 46, sau: 48, col: 2, lin: 1, pop: "673 mil", tend: 0.6 },
    { c: "3136702", n: "Juiz de Fora", uf: "MG", ivm: 40.0, emp: 38, fin: 42, sau: "suprimido", col: 4, lin: 2, pop: "573 mil", tend: 0.2 },
    { c: "3143302", n: "Montes Claros", uf: "MG", ivm: 55.7, emp: 58, fin: 53, sau: 55, col: 3, lin: 0, pop: "414 mil", tend: 0.9 },
    { c: "3154606", n: "Ribeirão das Neves", uf: "MG", ivm: 70.2, emp: 74, fin: 66, sau: "sem_cobertura", col: 1, lin: 1, pop: "338 mil", tend: 1.6 },
    { c: "3127701", n: "Governador Valadares", uf: "MG", ivm: 52.4, emp: 55, fin: 50, sau: 52, col: 4, lin: 1, pop: "281 mil", tend: 0.7 },
    { c: "3171204", n: "Uberaba", uf: "MG", ivm: 35.8, emp: 33, fin: 38, sau: 36, col: 0, lin: 0, pop: "340 mil", tend: 0.1 },
  ];

  const MUNICIPIOS = RAW.map((m, i) => {
    const s = serie(m.ivm, m.tend, 14, i + 7);
    // garante que o último ponto bate com o ivm declarado
    s[s.length - 1].ivm = m.ivm;
    return {
      codigo_ibge: m.c,
      nome: m.n,
      uf: m.uf,
      periodo: "2026-04",
      ivm: m.ivm,
      semaforo: classificar(m.ivm),
      v_emprego: m.emp,
      v_financas: m.fin,
      v_saude: m.sau, // number | "suprimido" | "sem_cobertura"
      populacao: m.pop,
      col: m.col,
      lin: m.lin,
      serie: s,
    };
  }).sort((a, b) => b.ivm - a.ivm);

  const META = {
    indicador: "ivm.composto",
    nome: "Índice de Vulnerabilidade Municipal",
    versao_metodologia: "v1.1",
    periodo: "2026-04",
    periodo_rotulo: "abr/2026",
    atraso_dias: 45,
    fontes: [
      { sigla: "CAGED", nome: "Novo CAGED — saldo de emprego formal", orgao: "MTE / PDET", dominio: "Emprego", ate: "abr/2026", atraso: "~45 dias" },
      { sigla: "ESTBAN", nome: "Estatística Bancária Mensal", orgao: "Banco Central do Brasil", dominio: "Finanças", ate: "mar/2026", atraso: "~60 dias" },
      { sigla: "SIH/SUS", nome: "Sistema de Informações Hospitalares", orgao: "Ministério da Saúde / DATASUS", dominio: "Saúde", ate: "fev/2026", atraso: "~90 dias" },
    ],
    metodologia:
      "Índice composto 0–100 por município/mês. Combina subíndices normalizados de emprego (CAGED), finanças (ESTBAN) e saúde (SIH), ponderados e reescalados. Maior = mais vulnerável.",
    licenca: "Dados públicos · Licença aberta (ODbL). Atribuição: DadoSabedoria.",
    semaforo: { verde: "0–32", amarelo: "33–66", vermelho: "67–100" },
    periodos: ["2026-04", "2026-03", "2026-02", "2026-01", "2025-12"],
  };

  const SUBINDICES = [
    { chave: "v_emprego", rotulo: "Emprego", fonte: "CAGED", desc: "Perda de postos formais e rotatividade elevam o subíndice." },
    { chave: "v_financas", rotulo: "Finanças", fonte: "ESTBAN", desc: "Retração de crédito e depósitos por habitante elevam o subíndice." },
    { chave: "v_saude", rotulo: "Saúde", fonte: "SIH/SUS", desc: "Internações sensíveis à atenção básica elevam o subíndice." },
  ];

  window.DADOS = { MUNICIPIOS, META, SUBINDICES, classificar };
})();
