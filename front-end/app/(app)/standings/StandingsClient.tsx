"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { Select, type SelectOption } from "@/components/Select";
import {
  ApiError,
  getCycleSeasons,
  getStandings,
  type CycleSeason,
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
  const flashError = useFlashStore((s) => s.error);

  const [hydrated, setHydrated] = useState(false);
  const [cycleSeasons, setCycleSeasons] = useState<CycleSeason[]>([]);
  const [selectedCycleSeasonId, setSelectedCycleSeasonId] = useState("");
  const [standings, setStandings] = useState<TeamStanding[]>([]);
  const [loading, setLoading] = useState(true);

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
    async (token: string, cycleSeasonId?: string) => {
      setLoading(true);
      try {
        const response = await getStandings(token, cycleSeasonId);
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

  const loadSeasonsAndStandings = useCallback(
    async (token: string) => {
      // Temporada selecionada por padrao: a que tem isCurrentSeason = true.
      let initialId: string | undefined;
      try {
        const seasons = await getCycleSeasons(token);
        setCycleSeasons(seasons);
        const current = seasons.find((season) => season.isCurrentSeason);
        initialId = current?.cycleSeasonId ?? seasons[0]?.cycleSeasonId;
        setSelectedCycleSeasonId(initialId ?? "");
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar as temporadas.");
        }
      }
      await loadStandings(token, initialId);
    },
    [flashError, loadStandings],
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
      if (active) void loadSeasonsAndStandings(token);
    });

    return () => {
      active = false;
    };
  }, [hydrated, accessToken, router, loadSeasonsAndStandings]);

  function handleSeasonChange(id: string) {
    setSelectedCycleSeasonId(id);
    if (accessToken) {
      void loadStandings(accessToken, id || undefined);
    }
  }

  const seasonOptions: SelectOption[] = cycleSeasons.map((season) => ({
    value: season.cycleSeasonId,
    label: `${season.cycleName} - ${season.seasonName}`,
  }));

  if (!hydrated || !accessToken) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="px-6 py-10 md:px-10">
      <div className="mx-auto w-full max-w-4xl">
        <header>
          <h1 className="font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
            Classificação
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Ola, {name} · temporada atual
          </p>
        </header>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <span
            id="cycleSeasonLabel"
            className="text-sm font-medium text-[var(--muted)]"
          >
            Temporada
          </span>
          <Select
            aria-label="Selecionar temporada"
            options={seasonOptions}
            value={selectedCycleSeasonId}
            onChange={handleSeasonChange}
            disabled={loading || seasonOptions.length === 0}
            placeholder="Selecione a temporada"
            className="w-64"
          />
        </div>

        <div className="mt-4">
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
    </div>
  );
}
