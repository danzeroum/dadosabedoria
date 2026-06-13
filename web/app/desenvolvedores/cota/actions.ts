"use server";

import { consultarQuota } from "../../../lib/api";
import type { EstadoCota } from "./estado";

// Server Action: recebe a chave pelo corpo do POST (nunca pela URL), consulta /v1/quota no servidor
// e devolve só os números agregados. A chave não persiste e jamais chega ao bundle do cliente.
export async function consultarCota(_prev: EstadoCota, formData: FormData): Promise<EstadoCota> {
  const chave = String(formData.get("chave") ?? "").trim();
  if (!chave) return { status: "sem_chave" };
  try {
    const q = await consultarQuota(chave);
    return q ? { status: "ok", quota: q } : { status: "sem_chave" };
  } catch {
    return { status: "erro" };
  }
}
