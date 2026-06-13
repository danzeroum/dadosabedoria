"use client";

import Link from "next/link";
import { useFormState } from "react-dom";

import { BarraQuota } from "../../../components/BarraQuota";
import { consultarCota } from "./actions";
import type { EstadoCota } from "./estado";

const INICIAL: EstadoCota = { status: "inicial" };

// Formulário do painel de cota. Única ilha de cliente do tier profundo: a chave é digitada aqui,
// enviada por POST à Server Action e processada no servidor — o cliente só recebe de volta os
// números de consumo. Degrada com honestidade (sem chave / cota lida / erro de rede).
export function CotaForm() {
  const [estado, formAction] = useFormState(consultarCota, INICIAL);
  return (
    <>
      <form className="cota-form" action={formAction}>
        <div>
          <label htmlFor="chave">Chave de API</label>
          <input
            id="chave"
            name="chave"
            type="password"
            placeholder="Bearer ••••••••••••"
            autoComplete="off"
          />
        </div>
        <button className="botao botao-primario" type="submit">
          Consultar cota
        </button>
      </form>

      {estado.status === "ok" ? (
        <div className="cota-painel">
          <BarraQuota q={estado.quota} />
          <dl className="cota-meta">
            <div>
              <dt>Limite (janela)</dt>
              <dd>{estado.quota.limite.toLocaleString("pt-BR")} req</dd>
            </div>
            <div>
              <dt>Usado</dt>
              <dd>
                {estado.quota.usado.toLocaleString("pt-BR")} req{" "}
                <span style={{ fontWeight: 400, color: "var(--cor-texto-suave)" }}>
                  ({Math.round((estado.quota.usado / Math.max(1, estado.quota.limite)) * 100)}%)
                </span>
              </dd>
            </div>
            <div>
              <dt>Restante</dt>
              <dd>{estado.quota.restante.toLocaleString("pt-BR")} req</dd>
            </div>
            <div>
              <dt>Reinicia em</dt>
              <dd>
                {new Date(estado.quota.reset * 1000).toLocaleTimeString("pt-BR", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </dd>
            </div>
          </dl>
        </div>
      ) : null}

      {estado.status === "sem_chave" ? (
        <aside className="portao" role="note" aria-label="Chave necessária">
          <span className="portao-icone" aria-hidden="true">
            🔑
          </span>
          <div>
            <strong>Informe uma chave válida do tier profundo.</strong> Sem chave (ou com chave
            inválida), o painel não tem o que mostrar — peça a sua em{" "}
            <Link href="/desenvolvedores/planos">Planos &amp; preços</Link>.
          </div>
        </aside>
      ) : null}

      {estado.status === "erro" ? (
        <p className="erro">
          Não consegui consultar a cota agora — pode ser uma falha de rede. Tente de novo em
          instantes (não invento número quando não consigo ler).
        </p>
      ) : null}
    </>
  );
}
