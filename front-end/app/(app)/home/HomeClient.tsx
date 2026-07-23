"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuthStore } from "@/store/auth";

export function HomeClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const name = useAuthStore((s) => s.name);
  const coachName = useAuthStore((s) => s.coachName);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const numberOfTitles = useAuthStore((s) => s.numberOfTitles);

  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const markHydrated = () => setHydrated(true);
    const unsubscribe = useAuthStore.persist.onFinishHydration(markHydrated);
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(markHydrated);
    }
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (hydrated && !accessToken) {
      router.replace("/login");
    }
  }, [hydrated, accessToken, router]);

  if (!hydrated || !accessToken) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="px-6 py-10 md:px-10">
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
        <p className="mt-2 text-sm text-[var(--ink)]">
          <span className="text-[var(--lime)] font-semibold">{numberOfTitles}</span>
          {numberOfTitles > 1 ? " títulos" : " título"}
        </p>
      </div>
    </div>
  );
}
