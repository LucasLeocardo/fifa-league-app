"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, logout as logoutRequest } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export function HomeClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const name = useAuthStore((s) => s.name);
  const coachName = useAuthStore((s) => s.coachName);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const clearSession = useAuthStore((s) => s.clearSession);

  const [hydrated, setHydrated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      router.replace("/login");
    }
  }, [hydrated, accessToken, router]);

  async function handleLogout() {
    setError(null);
    setLoading(true);
    try {
      if (accessToken) {
        await logoutRequest(accessToken);
      }
    } catch (err) {
      // Mesmo se a API falhar, limpa a sessao local.
      if (err instanceof ApiError) {
        setError(err.message);
      }
    } finally {
      clearSession();
      setLoading(false);
      router.replace("/login");
    }
  }

  if (!hydrated || !accessToken) {
    return (
      <main className="pitch-atmosphere flex min-h-dvh items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando...</p>
      </main>
    );
  }

  return (
    <main className="pitch-atmosphere flex min-h-dvh items-center justify-center px-6 py-12">
      <div className="w-full max-w-md border border-[var(--stroke)] bg-[var(--panel)] p-8 backdrop-blur-md">
        <p className="font-[family-name:var(--font-display)] text-sm tracking-[0.3em] text-[var(--lime)]">
          FIFA LEAGUE
        </p>
        <h1 className="mt-3 font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)]">
          Ola, {name}
        </h1>
        <p className="mt-3 text-sm text-[var(--muted)]">
          {coachName ? `Tecnico: ${coachName}` : "Sem tecnico definido"}
          {" · "}
          {isAdmin ? "Admin" : "Jogador"}
        </p>

        {error ? (
          <p className="mt-4 text-sm text-[var(--danger)]" role="alert">
            {error}
          </p>
        ) : null}

        <button
          type="button"
          onClick={handleLogout}
          disabled={loading}
          className="mt-8 w-full border border-[var(--stroke)] px-4 py-3 text-sm font-medium text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:opacity-60"
        >
          {loading ? "Saindo..." : "Sair"}
        </button>
      </div>
    </main>
  );
}
