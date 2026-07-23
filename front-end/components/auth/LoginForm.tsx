"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, login } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

const fieldClass =
  "w-full border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-3.5 py-3 text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

const labelClass =
  "mb-1.5 block text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]";

export function LoginForm() {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const flashSuccess = useFlashStore((s) => s.success);
  const flashError = useFlashStore((s) => s.error);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim() || !password) {
      flashError("Preencha email e senha para entrar.");
      return;
    }

    setLoading(true);
    try {
      const session = await login(email.trim(), password);
      setSession({
        accessToken: session.accessToken,
        refreshToken: session.refreshToken,
        name: session.name,
        isAdmin: session.isAdmin,
        coachName: session.coachName,
        numberOfTitles: session.numberOfTitles,
      });
      flashSuccess("Login realizado com sucesso.");
      router.push("/standings");
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel entrar. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <div>
        <label htmlFor="login-email" className={labelClass}>
          Email
        </label>
        <input
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={fieldClass}
          placeholder="voce@email.com"
          disabled={loading}
        />
      </div>

      <div>
        <label htmlFor="login-password" className={labelClass}>
          Senha
        </label>
        <input
          id="login-password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={fieldClass}
          placeholder="••••••••"
          disabled={loading}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-1 w-full bg-[var(--lime)] px-4 py-3.5 font-[family-name:var(--font-display)] text-xl tracking-wide text-[var(--pitch-deep)] transition-[transform,background-color,opacity] hover:bg-[var(--lime-dim)] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Entrando..." : "Entrar"}
      </button>

      <Link
        href="/register"
        className="inline-flex w-full items-center justify-center border border-[var(--stroke)] px-4 py-3 text-sm font-medium text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)]"
      >
        Criar conta · Sign up
      </Link>
    </form>
  );
}
