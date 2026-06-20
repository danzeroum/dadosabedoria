"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// Onboarding leve do primeiro acesso (Bloco 3.4 da auditoria): orienta o cidadão novo a começar
// pelo SEU município, em vez de encarar uma lista abstrata de 28 produtos. Anônimo (sem login):
// só um flag em localStorage para não repetir. Sem dependência de backend.

const CHAVE = "ds_onboarding_visto";

export function Onboarding() {
  const router = useRouter();
  const [hidratado, setHidratado] = useState(false);
  const [visto, setVisto] = useState(true); // assume "visto" até hidratar — evita flash no SSR
  const [q, setQ] = useState("");

  useEffect(() => {
    try {
      setVisto(window.localStorage.getItem(CHAVE) === "1");
    } catch {
      setVisto(false);
    }
    setHidratado(true);
  }, []);

  function marcarVisto() {
    try {
      window.localStorage.setItem(CHAVE, "1");
    } catch {
      /* localStorage indisponível — segue sem persistir */
    }
    setVisto(true);
  }

  function buscar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const v = q.trim();
    if (!v) return;
    marcarVisto();
    // Código IBGE (7 dígitos) → panorama direto; senão, leva à busca do IVM.
    if (/^\d{7}$/.test(v)) router.push(`/municipio/${v}`);
    else router.push(`/ivm?q=${encodeURIComponent(v)}`);
  }

  if (!hidratado || visto) return null;

  return (
    <section className="onboarding" aria-label="Comece por aqui">
      <button type="button" className="onboarding-fechar" onClick={marcarVisto} aria-label="Dispensar orientação">
        ×
      </button>
      <p className="onboarding-passo">Primeiro acesso · comece por aqui</p>
      <h2>Veja os dados do seu município</h2>
      <form className="onboarding-busca" onSubmit={buscar} role="search">
        <label htmlFor="onb-q">Município (nome ou código IBGE)</label>
        <input
          id="onb-q"
          value={q}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQ(e.target.value)}
          placeholder="ex.: São Paulo ou 3550308"
          autoComplete="off"
        />
        <button type="submit">Ver meu município →</button>
      </form>
      <p className="onboarding-dica">
        Ou explore por tema: <Link href="/produtos">todos os 28 produtos</Link>.
      </p>
    </section>
  );
}
