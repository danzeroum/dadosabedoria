// Fonte única do catálogo de produtos (home + /produtos). Cada produto é uma PERGUNTA com tela.
//
// Honestidade/proveniência: a copy aqui foi conciliada com a semântica REAL do backend
// (api/app/produtos/*), não com inferência de slug. O handoff de design trazia copy provisória
// para os produtos órfãos — aqui ela está corrigida (ex.: LuzNoMapa = ANEEL DEC/FEC, não Censo;
// PressãoSUS = SICONFI Função 10, não CNES; PratoFrio = IBGE/PAM, não PNAE; EscolaViva = SICONFI
// Função 12). Só entram produtos que possuem PÁGINA (`web/app/<slug>/[codigo]`), para nenhum link
// cair em 404. São 29 produtos temáticos (o handoff congelou em "24"; a main cresceu desde então,
// somando AssisViva/CulturaViva/CidadeViva/SegurançaViva — SICONFI por função — e o
// Perfil Orçamentário, da fatia de analytics inferencial).

export type DominioId =
  | "sintese"
  | "trabalho"
  | "educacao"
  | "saude"
  | "saneamento"
  | "alimentacao"
  | "financas"
  | "cidade"
  | "social";

export interface ProdutoCatalogo {
  titulo: string;
  pergunta: string;
  descricao: string;
  href: string; // link de exemplo (rota real) — ex.: "/pulso/3550308" ou "/ivm"
  cta: string;
  fonte: string; // chip de proveniência — ex.: "trabalho · Novo CAGED"
  dominio: DominioId;
  destaque?: boolean; // aparece na grade da home (subconjunto curado)
}

// Domínios na ordem de exibição do catálogo, com a ressalva-mãe de cada grupo.
export const DOMINIOS: { id: DominioId; titulo: string; descricao: string }[] = [
  {
    id: "sintese",
    titulo: "Síntese & navegação",
    descricao:
      "Os pontos de partida: o sinal único, o retrato completo, a comparação e a pergunta livre.",
  },
  {
    id: "trabalho",
    titulo: "Trabalho & renda",
    descricao: "Emprego formal, salário e dinamismo econômico — Novo CAGED e crédito ESTBAN.",
  },
  {
    id: "educacao",
    titulo: "Educação",
    descricao:
      "Matrículas, cobertura escolar e investimento em educação — INEP/Censo Escolar e SICONFI.",
  },
  {
    id: "saude",
    titulo: "Saúde",
    descricao:
      "Internações, arboviroses, saúde materna e financiamento do SUS — DATASUS/SIH, SINAN, SISVAN e SICONFI. Células com menos de 5 são suprimidas (k-anonimato).",
  },
  {
    id: "saneamento",
    titulo: "Saneamento, água & energia",
    descricao:
      "Água, esgoto, seca, energia e investimento em saneamento — SNIS/MDR, ANA, ANEEL e SICONFI. Ausência de dado ≠ ausência de serviço.",
  },
  {
    id: "alimentacao",
    titulo: "Alimentação & produção",
    descricao:
      "Produção agrícola, nutrição infantil e fomento à agricultura — IBGE/PAM, SISVAN e SICONFI.",
  },
  {
    id: "financas",
    titulo: "Finanças & contratos",
    descricao:
      "Execução orçamentária e compras públicas — SICONFI/STN e PNCP. Empenhar não é liquidar, liquidar não é entregar.",
  },
  {
    id: "cidade",
    titulo: "Cidade, moradia & ambiente",
    descricao:
      "Investimento municipal por função — habitação, transporte, urbanismo e gestão ambiental (SICONFI por habitante).",
  },
  {
    id: "social",
    titulo: "Cultura, assistência & segurança",
    descricao:
      "Investimento municipal por função — cultura, assistência social e segurança pública (SICONFI por habitante).",
  },
];

// Município de exemplo para os links da grade (São Paulo / SP), igual à home.
const EX = "3550308";

export const CATALOGO: ProdutoCatalogo[] = [
  // ----------------------------------------------------------------- Síntese & navegação
  {
    titulo: "IVM — mapa semafórico",
    pergunta: "Quão vulnerável é o meu município?",
    descricao:
      "Emprego, finanças e saúde num só sinal, do verde ao vermelho — o que é protegido aparece como protegido.",
    href: "/ivm",
    cta: "Abrir o mapa",
    fonte: "síntese · CAGED · ESTBAN · SIH",
    dominio: "sintese",
    destaque: true,
  },
  {
    titulo: "Panorama do município",
    pergunta: "O que sabemos sobre o meu município?",
    descricao: "Todos os indicadores do acervo num só lugar, com a fonte de cada número.",
    href: `/municipio/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "síntese · todas as fontes",
    dominio: "sintese",
    destaque: true,
  },
  {
    titulo: "Comparar municípios",
    pergunta: "Como meu município se compara a outro?",
    descricao:
      "Dois municípios lado a lado, indicador por indicador. Contexto para perguntar, não um ranking.",
    href: "/comparar",
    cta: "Comparar",
    fonte: "síntese · descritivo",
    dominio: "sintese",
    destaque: true,
  },
  {
    titulo: "Pergunte aos dados",
    pergunta: "Posso perguntar em vez de procurar?",
    descricao:
      "A IA responde só com o que recupera do acervo, sempre com citação. Sem dado, abstém-se.",
    href: "/perguntar",
    cta: "Fazer uma pergunta",
    fonte: "IA ancorada · cita a fonte",
    dominio: "sintese",
    destaque: true,
  },

  // ----------------------------------------------------------------- Trabalho & renda
  {
    titulo: "Pulso Produtivo",
    pergunta: "Como está o emprego formal no meu município?",
    descricao:
      "O saldo do Novo CAGED mês a mês, com a tendência honesta — o fluxo é volátil; merece a pergunta.",
    href: `/pulso/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "trabalho · Novo CAGED",
    dominio: "trabalho",
    destaque: true,
  },
  {
    titulo: "Salário Radar",
    pergunta: "Qual o salário médio das novas contratações?",
    descricao:
      "Média salarial das admissões do Novo CAGED — quem entrou no mercado formal, não quem já estava lá.",
    href: `/salario-radar/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "trabalho · Novo CAGED",
    dominio: "trabalho",
    destaque: true,
  },
  {
    titulo: "Giro Local",
    pergunta: "Qual o dinamismo econômico do meu município?",
    descricao: "Emprego formal (CAGED) e crédito bancário (ESTBAN) per capita num só retrato.",
    href: `/giro-local/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "trabalho · crédito · CAGED · ESTBAN",
    dominio: "trabalho",
    destaque: true,
  },
  {
    titulo: "Região Emprega",
    pergunta: "Como está o emprego formal na minha UF?",
    descricao:
      "Retrato regional do CAGED: saldo total e quantos municípios criam, estabilizam ou reduzem vagas.",
    href: "/regiao-emprega/35",
    cta: "Ver exemplo (SP)",
    fonte: "trabalho · Novo CAGED",
    dominio: "trabalho",
  },

  // ----------------------------------------------------------------- Educação
  {
    titulo: "Bússola Educação-Trabalho",
    pergunta: "Como se cruzam base educacional e emprego?",
    descricao:
      "Matrículas no fundamental (INEP) + saldo de emprego + salário das admissões (CAGED). Contexto, não causalidade.",
    href: `/bussola-edu-trabalho/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "educação · trabalho · INEP · CAGED",
    dominio: "educacao",
    destaque: true,
  },
  {
    titulo: "Radar de Evasão Escolar",
    pergunta: "Quantas crianças em idade escolar estão fora do fundamental?",
    descricao:
      "Matrículas do EF (INEP) ÷ estimativa de população em idade escolar. Acima de 100% indica polo de atração, não erro.",
    href: `/radar-evasao/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "educação · INEP/Censo Escolar",
    dominio: "educacao",
    destaque: true,
  },
  {
    titulo: "EscolaViva",
    pergunta: "Quanto o município investe em educação?",
    descricao:
      "Despesa liquidada na Função 12 (Educação) por habitante (SICONFI). O orçamento como espelho da prioridade.",
    href: `/escola-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "educação · finanças · SICONFI F.12",
    dominio: "educacao",
  },

  // ----------------------------------------------------------------- Saúde
  {
    titulo: "Sentinela Respiratória",
    pergunta: "Como estão as internações respiratórias?",
    descricao:
      "AIH no grupo J do CID-10 no SIH/SUS por mês. Cobre só o SUS; células com menos de 5 viram 'Protegido', nunca zero.",
    href: `/sentinela-resp/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saúde · DATASUS/SIH",
    dominio: "saude",
    destaque: true,
  },
  {
    titulo: "Caçador de Arboviroses",
    pergunta: "Qual a incidência de dengue confirmada?",
    descricao:
      "Casos de dengue confirmados por 100 mil hab. (SINAN). Há subnotificação; menos de 5 casos são suprimidos por privacidade.",
    href: `/cacador-arboviroses/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saúde · SINAN/DATASUS",
    dominio: "saude",
  },
  {
    titulo: "Sentinela Materna",
    pergunta: "Qual o risco nutricional de gestantes acompanhadas?",
    descricao:
      "% de gestantes com baixo peso no SISVAN. Agregado por município — não identifica gestantes.",
    href: `/sentinela-materna/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saúde · SISVAN/MS",
    dominio: "saude",
  },
  {
    titulo: "Pressão no SUS",
    pergunta: "Qual o esforço de financiamento do SUS local?",
    descricao:
      "Despesa liquidada na Função 10 (Saúde) por habitante (SICONFI) — proxy do investimento municipal no SUS.",
    href: `/pressao-sus/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saúde · finanças · SICONFI F.10",
    dominio: "saude",
  },

  // ----------------------------------------------------------------- Saneamento, água & energia
  {
    titulo: "AguaViva",
    pergunta: "Como está o saneamento básico?",
    descricao:
      "Cobertura de água tratada e coleta de esgoto (SNIS). Classificados por ODS 6 (adequado/atenção/alerta).",
    href: `/agua-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saneamento · SNIS/MDR",
    dominio: "saneamento",
    destaque: true,
  },
  {
    titulo: "EsgotoInvisível",
    pergunta: "Onde a água chega mas o esgoto some?",
    descricao:
      "Gap entre cobertura de água e coleta de esgoto (SNIS). Quanto maior, mais domicílios com água mas sem rede.",
    href: `/esgoto-invisivel/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saneamento · SNIS/MDR",
    dominio: "saneamento",
    destaque: true,
  },
  {
    titulo: "SaneFundo",
    pergunta: "Quanto o município investe em saneamento?",
    descricao:
      "Despesa liquidada na Função 17 (Saneamento) por habitante (SICONFI). Investir é o passo antes de cobrir.",
    href: `/sane-fundo/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "saneamento · finanças · SICONFI F.17",
    dominio: "saneamento",
  },
  {
    titulo: "Rio em Risco",
    pergunta: "Qual o risco hídrico de seca?",
    descricao:
      "Índice de seca (ANA Monitor de Secas, 0–5) no pior mês do exercício. Onde não há monitoramento, é 'sem cobertura', não 'tudo bem'.",
    href: `/rio-em-risco/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "água · ANA/Monitor de Secas",
    dominio: "saneamento",
  },
  {
    titulo: "Luz no Mapa",
    pergunta: "Qual a qualidade do fornecimento de energia?",
    descricao:
      "Horas (DEC) e número (FEC) de interrupções por consumidor/ano (ANEEL). A confiabilidade da energia, medida.",
    href: `/luz-no-mapa/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "energia · ANEEL",
    dominio: "saneamento",
  },

  // ----------------------------------------------------------------- Alimentação & produção
  {
    titulo: "Prato Frio",
    pergunta: "Qual a produção agrícola do município?",
    descricao:
      "Valor da produção agrícola municipal por habitante (IBGE/PAM). A base alimentar produzida no território.",
    href: `/prato-frio/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "alimentação · IBGE/PAM",
    dominio: "alimentacao",
  },
  {
    titulo: "Fome Oculta",
    pergunta: "Há insegurança nutricional infantil?",
    descricao:
      "Prevalência de baixo peso em crianças menores de 5 anos (SISVAN). O que o prato não mostra, a balança revela; menos de 5 é suprimido.",
    href: `/fome-oculta/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "alimentação · SISVAN/MS",
    dominio: "alimentacao",
  },
  {
    titulo: "Semeando Transparência",
    pergunta: "Quanto se investe em agricultura?",
    descricao:
      "Despesa liquidada na Função 20 (Agricultura) por habitante (SICONFI). A política agrícola municipal visível.",
    href: `/semeando-transparencia/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "agricultura · finanças · SICONFI F.20",
    dominio: "alimentacao",
  },

  // ----------------------------------------------------------------- Finanças & contratos
  {
    titulo: "OndeFoi",
    pergunta: "Do que foi empenhado por função, quanto saiu do papel?",
    descricao:
      "Liquidado × empenhado por função do orçamento (SICONFI). O número que merece a pergunta, nunca o veredito.",
    href: "/onde-foi/3304557",
    cta: "Explorar municípios",
    fonte: "finanças · SICONFI/STN",
    dominio: "financas",
    destaque: true,
  },
  {
    titulo: "ObraViva",
    pergunta: "Quanto o município contrata via PNCP?",
    descricao:
      "Soma do valor global de contratos no PNCP no exercício, per capita. Ausência de dado ≠ ausência de contratação.",
    href: `/obra-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "compras · PNCP",
    dominio: "financas",
    destaque: true,
  },
  {
    titulo: "Perfil Orçamentário",
    pergunta: "Onde o orçamento do município destoa do resto do país?",
    descricao:
      "Cada função do orçamento (SICONFI) com o percentil nacional per capita — comparativo, não veredito.",
    href: `/perfil-orcamentario/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "finanças · SICONFI/STN",
    dominio: "financas",
  },

  // ----------------------------------------------------------------- Cidade, moradia & ambiente
  {
    titulo: "CasaViva",
    pergunta: "Quanto se investe em habitação?",
    descricao:
      "Despesa liquidada na Função 16 (Habitação) por habitante (SICONFI). O direito à moradia no orçamento.",
    href: `/casa-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "habitação · finanças · SICONFI F.16",
    dominio: "cidade",
  },
  {
    titulo: "ViaViva",
    pergunta: "Quanto se investe em mobilidade e vias?",
    descricao:
      "Despesa liquidada na Função 26 (Transporte) por habitante (SICONFI). O quanto a cidade investe em circular.",
    href: `/via-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "mobilidade · finanças · SICONFI F.26",
    dominio: "cidade",
  },
  {
    titulo: "CidadeViva",
    pergunta: "Quanto se investe em urbanismo?",
    descricao:
      "Despesa liquidada na Função 15 (Urbanismo) por habitante (SICONFI). Calçadas, praças e ordenamento — a cidade como política.",
    href: `/cidade-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "urbanismo · finanças · SICONFI F.15",
    dominio: "cidade",
  },
  {
    titulo: "EcoVivo",
    pergunta: "Quanto o município investe em meio ambiente?",
    descricao:
      "Despesa liquidada na Função 18 (Gestão Ambiental) por habitante (SICONFI). O orçamento revela a prioridade ambiental.",
    href: `/eco-vivo/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "ambiente · finanças · SICONFI F.18",
    dominio: "cidade",
  },

  // ----------------------------------------------------------------- Cultura, assistência & segurança
  {
    titulo: "CulturaViva",
    pergunta: "Quanto se investe em cultura?",
    descricao:
      "Despesa liquidada na Função 13 (Cultura) por habitante (SICONFI). Cultura como política pública, em números.",
    href: `/cultura-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "cultura · finanças · SICONFI F.13",
    dominio: "social",
  },
  {
    titulo: "AssisViva",
    pergunta: "Quanto se investe em assistência social?",
    descricao:
      "Despesa liquidada na Função 08 (Assistência Social) por habitante (SICONFI). A rede de proteção no orçamento.",
    href: `/assis-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "assistência · finanças · SICONFI F.08",
    dominio: "social",
  },
  {
    titulo: "SegurançaViva",
    pergunta: "Quanto se investe em segurança pública?",
    descricao:
      "Despesa liquidada na Função 06 (Segurança Pública) por habitante (SICONFI). O esforço municipal em segurança, no orçamento.",
    href: `/seguranca-viva/${EX}`,
    cta: "Ver exemplo (São Paulo)",
    fonte: "segurança · finanças · SICONFI F.06",
    dominio: "social",
  },
];

// Produtos em destaque na home (subconjunto curado, na ordem do catálogo).
export const DESTAQUES: ProdutoCatalogo[] = CATALOGO.filter((p) => p.destaque);

// Produtos de um domínio, na ordem do catálogo.
export function produtosDoDominio(dominio: DominioId): ProdutoCatalogo[] {
  return CATALOGO.filter((p) => p.dominio === dominio);
}
