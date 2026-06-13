import type { RespostaQuota } from "../../../lib/types";

// Estado do painel de cota (compartilhado entre a Server Action e o formulário client).
export type EstadoCota =
  | { status: "inicial" }
  | { status: "ok"; quota: RespostaQuota }
  | { status: "sem_chave" }
  | { status: "erro" };
