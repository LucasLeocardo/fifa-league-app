"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const fieldClass =
  "w-full border border-[var(--stroke)] bg-[rgba(4,17,12,0.55)] px-3.5 py-3 text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

const labelClass = "mb-1.5 block text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]";

export function RegisterForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!name.trim() || !email.trim() || password.length < 8) {
      setError("Informe nome, email e senha com pelo menos 8 caracteres.");
      return;
    }

    // Integração com POST /api/v1/auth/register virá na próxima etapa.
    setError("API de cadastro ainda não conectada. Em breve.");
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <div>
        <label htmlFor="register-name" className={labelClass}>
          Nome
        </label>
        <input
          id="register-name"
          name="name"
          type="text"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={fieldClass}
          placeholder="Seu nome na liga"
        />
      </div>

      <div>
        <label htmlFor="register-email" className={labelClass}>
          Email
        </label>
        <input
          id="register-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={fieldClass}
          placeholder="voce@email.com"
        />
      </div>

      <div>
        <label htmlFor="register-password" className={labelClass}>
          Senha
        </label>
        <input
          id="register-password"
          name="password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={fieldClass}
          placeholder="Mínimo 8 caracteres"
        />
      </div>

      {error ? (
        <p className="text-sm text-[var(--danger)]" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        className="mt-1 w-full bg-[var(--lime)] px-4 py-3.5 font-[family-name:var(--font-display)] text-xl tracking-wide text-[var(--pitch-deep)] transition-[transform,background-color] hover:bg-[var(--lime-dim)] active:scale-[0.99]"
      >
        Criar conta
      </button>

      <Link
        href="/login"
        className="inline-flex w-full items-center justify-center border border-[var(--stroke)] px-4 py-3 text-sm font-medium text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)]"
      >
        Já tenho conta · Entrar
      </Link>
    </form>
  );
}
