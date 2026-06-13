// Sessão do cidadão (gate OIDC gov.br). Hoje é um MOCK honesto: o provedor OIDC ainda não foi
// liberado (gate externo do dono), então não há ninguém autenticado. Quando o gate abrir, SÓ a
// função `sessaoAtual()` muda (passa a ler o cookie de sessão emitido pelo fluxo OIDC) — as telas
// de /cidadao e /entrar não mudam. SSR puro: nada disso roda no cliente.

export const AUTH_HABILITADO = process.env.AUTH_HABILITADO === "true";

export interface AlertaResumo {
  id: string;
  titulo: string;
  criadoEm: string; // ISO
}

export interface Consentimento {
  id: string;
  finalidade: string;
  concedido: boolean;
}

export interface SessaoCidadao {
  sub: string;
  nome: string;
  alertas: AlertaResumo[];
  consentimentos: Consentimento[];
}

// Mock: ninguém logado enquanto o OIDC não está no ar. Retorna null até o gate liberar.
export async function sessaoAtual(): Promise<SessaoCidadao | null> {
  return null;
}
