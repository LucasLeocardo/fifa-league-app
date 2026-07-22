"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import {
  ApiError,
  getStandings,
  logout as logoutRequest,
  type TeamStanding,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

const columns: DataTableColumn<TeamStanding>[] = [
  {
    key: "position",
    header: "#",
    align: "center",
    width: "3rem",
    headerClassName: "text-[var(--lime)]",
    cellClassName: "font-semibold text-[var(--lime)]",
    render: (_row, index) => index + 1,
  },
  {
    key: "teamName",
    header: "Time",
    render: (row) => (
      <div className="flex flex-col">
        <span className="font-medium text-[var(--ink)]">{row.teamName}</span>
        {row.coachName ? (
          <span className="text-xs text-[var(--muted)]">{row.coachName}</span>
        ) : null}
      </div>
    ),
  },
  { key: "points", header: "P", align: "center", cellClassName: "font-semibold" },
  {
    key: "games",
    header: "J",
    align: "center",
    render: (row) => row.wins + row.draws + row.losses,
  },
  { key: "wins", header: "V", align: "center" },
  { key: "draws", header: "E", align: "center" },
  { key: "losses", header: "D", align: "center" },
  { key: "goalsFor", header: "GP", align: "center" },
  { key: "goalsAgainst", header: "GC", align: "center" },
  {
    key: "goalDifference",
    header: "SG",
    align: "center",
    render: (row) =>
      row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference,
  },
];

export function StandingsClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const name = useAuthStore((s) => s.name);
  const clearSession = useAuthStore((s) => s.clearSession);
  const flashSuccess = useFlashStore((s) => s.success);
  const flashError = useFlashStore((s) => s.error);

  const [hydrated, setHydrated] = useState(false);
  const [standings, setStandings] = useState<TeamStanding[]>([]);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    const markHydrated = () => setHydrated(true);
    // setState so em callback (assincrono), evitando cascata de renders no effect.
    const unsubscribe = useAuthStore.persist.onFinishHydration(markHydrated);
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(markHydrated);
    }
    return unsubscribe;
  }, []);

  const loadStandings = useCallback(
    async (token: string) => {
      try {
        const response = await getStandings(token);
        setStandings(response.standings);
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar a classificacao.");
        }
      } finally {
        setLoading(false);
      }
    },
    [flashError],
  );

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      router.replace("/login");
      return;
    }

    let active = true;
    const token = accessToken;
    // Defere para um callback: evita setState sincrono no corpo do effect.
    queueMicrotask(() => {
      if (active) void loadStandings(token);
    });

    return () => {
      active = false;
    };
  }, [hydrated, accessToken, router, loadStandings]);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      if (accessToken) {
        await logoutRequest(accessToken);
      }
      flashSuccess("Sessao encerrada.");
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel encerrar no servidor. Sessao local limpa.");
      }
    } finally {
      clearSession();
      setLoggingOut(false);
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
    <main className="pitch-atmosphere min-h-dvh px-6 py-10 md:px-10">
      <div className="mx-auto w-full max-w-4xl">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-[family-name:var(--font-display)] text-sm tracking-[0.3em] text-[var(--lime)]">
              FIFA LEAGUE
            </p>
            <h1 className="mt-2 font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
              Classificação
            </h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Ola, {name} · temporada atual
            </p>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="border border-[var(--stroke)] px-4 py-2.5 text-sm font-medium text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:opacity-60"
          >
            {loggingOut ? "Saindo..." : "Sair"}
          </button>
        </header>

        <div className="mt-8">
          <DataTable
            columns={columns}
            data={standings}
            getRowKey={(row) => row.teamCycleSeasonId}
            isLoading={loading}
            loadingLabel="Carregando classificacao..."
            emptyMessage="Nenhum time na classificacao ainda."
          />
        </div>

        <p className="mt-4 text-xs text-[var(--muted)]">
          P: pontos · J: jogos · V: vitorias · E: empates · D: derrotas ·
          GP: gols pro · GC: gols contra · SG: saldo de gols
        </p>
      </div>
    </main>
  );
}
