"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { MultiSelect } from "@/components/MultiSelect";
import { Select, type SelectOption } from "@/components/Select";
import {
  ApiError,
  getCycleSeasons,
  getLeaderboard,
  getPositions,
  type CycleSeason,
  type LeaderboardAssistsEntry,
  type LeaderboardGoalsEntry,
  type LeaderboardRatingsEntry,
  type LeaderboardResponse,
  type Position,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

type StatsTab = "goals" | "assists" | "ratings";

const PAGE_SIZE = 10;

const TABS: { id: StatsTab; label: string }[] = [
  { id: "goals", label: "Goleadores" },
  { id: "assists", label: "Líderes em Assistências" },
  { id: "ratings", label: "MVP's" },
];

const emptyLeaderboard: LeaderboardResponse = {
  cycleSeasonId: "",
  goals: [],
  assists: [],
  ratings: [],
};

function buildGoalsColumns(
  pageOffset: number,
): DataTableColumn<LeaderboardGoalsEntry>[] {
  return [
    {
      key: "position",
      header: "#",
      align: "center",
      width: "3rem",
      cellClassName: "font-semibold text-[var(--lime)]",
      render: (_row, index) => pageOffset + index + 1,
    },
    {
      key: "playerName",
      header: "Jogador",
      cellClassName: "font-medium text-[var(--ink)]",
      render: (row) => row.playerName,
    },
    {
      key: "teamName",
      header: "Time",
      render: (row) => row.teamName || "-",
    },
    {
      key: "totalGoals",
      header: "Gols",
      align: "center",
      cellClassName: "font-semibold",
      render: (row) => row.totalGoals,
    },
  ];
}

function buildAssistsColumns(
  pageOffset: number,
): DataTableColumn<LeaderboardAssistsEntry>[] {
  return [
    {
      key: "position",
      header: "#",
      align: "center",
      width: "3rem",
      cellClassName: "font-semibold text-[var(--lime)]",
      render: (_row, index) => pageOffset + index + 1,
    },
    {
      key: "playerName",
      header: "Jogador",
      cellClassName: "font-medium text-[var(--ink)]",
      render: (row) => row.playerName,
    },
    {
      key: "teamName",
      header: "Time",
      render: (row) => row.teamName || "-",
    },
    {
      key: "totalAssists",
      header: "Assistências",
      align: "center",
      cellClassName: "font-semibold",
      render: (row) => row.totalAssists,
    },
  ];
}

function buildRatingsColumns(
  pageOffset: number,
): DataTableColumn<LeaderboardRatingsEntry>[] {
  return [
    {
      key: "position",
      header: "#",
      align: "center",
      width: "3rem",
      cellClassName: "font-semibold text-[var(--lime)]",
      render: (_row, index) => pageOffset + index + 1,
    },
    {
      key: "playerName",
      header: "Jogador",
      cellClassName: "font-medium text-[var(--ink)]",
      render: (row) => row.playerName,
    },
    {
      key: "teamName",
      header: "Time",
      render: (row) => row.teamName || "-",
    },
    {
      key: "averageRating",
      header: "Nota",
      align: "center",
      cellClassName: "font-semibold",
      render: (row) => row.averageRating.toFixed(2).replace(".", ","),
    },
    {
      key: "gamesPlayed",
      header: "J",
      align: "center",
      render: (row) => row.gamesPlayed,
    },
  ];
}

export function StatsClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const name = useAuthStore((s) => s.name);
  const flashError = useFlashStore((s) => s.error);

  const [hydrated, setHydrated] = useState(false);
  const [cycleSeasons, setCycleSeasons] = useState<CycleSeason[]>([]);
  const [selectedCycleSeasonId, setSelectedCycleSeasonId] = useState("");
  const [positions, setPositions] = useState<Position[]>([]);
  const [selectedPositionIds, setSelectedPositionIds] = useState<string[]>([]);
  const [leaderboard, setLeaderboard] =
    useState<LeaderboardResponse>(emptyLeaderboard);
  const [activeTab, setActiveTab] = useState<StatsTab>("goals");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const markHydrated = () => setHydrated(true);
    const unsubscribe = useAuthStore.persist.onFinishHydration(markHydrated);
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(markHydrated);
    }
    return unsubscribe;
  }, []);

  const loadLeaderboard = useCallback(
    async (
      token: string,
      cycleSeasonId?: string,
      positionIds?: string[],
    ) => {
      setLoading(true);
      setPage(0);
      try {
        const response = await getLeaderboard(
          token,
          cycleSeasonId,
          positionIds && positionIds.length > 0 ? positionIds : undefined,
        );
        setLeaderboard(response);
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar as estatisticas.");
        }
        setLeaderboard(emptyLeaderboard);
      } finally {
        setLoading(false);
      }
    },
    [flashError],
  );

  const loadSeasonsPositionsAndLeaderboard = useCallback(
    async (token: string) => {
      let initialId: string | undefined;
      try {
        const [seasons, positionList] = await Promise.all([
          getCycleSeasons(token),
          getPositions(token),
        ]);
        setCycleSeasons(seasons);
        setPositions(positionList);
        setSelectedPositionIds([]);
        const current = seasons.find((season) => season.isCurrentSeason);
        initialId = current?.cycleSeasonId ?? seasons[0]?.cycleSeasonId;
        setSelectedCycleSeasonId(initialId ?? "");
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar temporadas ou posicoes.");
        }
      }
      await loadLeaderboard(token, initialId);
    },
    [flashError, loadLeaderboard],
  );

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      router.replace("/login");
      return;
    }

    let active = true;
    const token = accessToken;
    queueMicrotask(() => {
      if (active) void loadSeasonsPositionsAndLeaderboard(token);
    });

    return () => {
      active = false;
    };
  }, [hydrated, accessToken, router, loadSeasonsPositionsAndLeaderboard]);

  function handleSeasonChange(id: string) {
    setSelectedCycleSeasonId(id);
    setSelectedPositionIds([]);
    if (accessToken) {
      void loadLeaderboard(accessToken, id || undefined);
    }
  }

  function handlePositionsChange(ids: string[]) {
    const hadSelection = selectedPositionIds.length > 0;
    setSelectedPositionIds(ids);
    // Se limpar todas as posicoes apos ter filtrado, volta ao leaderboard completo.
    if (ids.length === 0 && hadSelection && accessToken) {
      void loadLeaderboard(accessToken, selectedCycleSeasonId || undefined);
    }
  }

  function handleSearchByPositions() {
    if (!accessToken || selectedPositionIds.length === 0) return;
    void loadLeaderboard(
      accessToken,
      selectedCycleSeasonId || undefined,
      selectedPositionIds,
    );
  }

  function handleTabChange(tab: StatsTab) {
    setActiveTab(tab);
    setPage(0);
  }

  const seasonOptions: SelectOption[] = cycleSeasons.map((season) => ({
    value: season.cycleSeasonId,
    label: `${season.cycleName} - ${season.seasonName}`,
  }));

  const positionOptions: SelectOption[] = positions.map((position) => ({
    value: position.id,
    label: position.code,
  }));

  let activeRows:
    | LeaderboardGoalsEntry[]
    | LeaderboardAssistsEntry[]
    | LeaderboardRatingsEntry[] = leaderboard.ratings;
  if (activeTab === "goals") {
    activeRows = leaderboard.goals;
  } else if (activeTab === "assists") {
    activeRows = leaderboard.assists;
  }

  const totalPages = Math.max(1, Math.ceil(activeRows.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);
  const pageOffset = currentPage * PAGE_SIZE;
  const pagedRows = activeRows.slice(pageOffset, pageOffset + PAGE_SIZE);

  const goalsColumns = useMemo(
    () => buildGoalsColumns(pageOffset),
    [pageOffset],
  );
  const assistsColumns = useMemo(
    () => buildAssistsColumns(pageOffset),
    [pageOffset],
  );
  const ratingsColumns = useMemo(
    () => buildRatingsColumns(pageOffset),
    [pageOffset],
  );

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
            Estatísticas
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Ola, {name} · ranking de jogadores
          </p>
        </header>

        <div className="mt-8 flex flex-col gap-3">
          <div className="grid grid-cols-[6.5rem_16rem] items-center gap-3">
            <span className="text-sm font-medium text-[var(--muted)]">
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
          <div className="flex flex-wrap items-center gap-3">
            <div className="grid grid-cols-[6.5rem_16rem] items-center gap-3">
              <span className="text-sm font-medium text-[var(--muted)]">
                Posições
              </span>
              <MultiSelect
                aria-label="Filtrar por posicoes"
                options={positionOptions}
                value={selectedPositionIds}
                onChange={handlePositionsChange}
                disabled={loading || positionOptions.length === 0}
                placeholder="Todas as posicoes"
                className="w-64"
              />
            </div>
            {selectedPositionIds.length > 0 ? (
              <button
                type="button"
                onClick={handleSearchByPositions}
                disabled={loading}
                className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Buscar
              </button>
            ) : null}
          </div>
        </div>

        <div
          role="tablist"
          aria-label="Categorias de estatisticas"
          className="mt-8 flex flex-wrap gap-1 border-b border-[var(--stroke)]"
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => handleTabChange(tab.id)}
                className={
                  isActive
                    ? "-mb-px cursor-pointer border-b-2 border-[var(--lime)] bg-[rgba(200,245,66,0.08)] px-4 py-2.5 text-sm font-semibold text-[var(--lime)] transition-colors hover:bg-[rgba(200,245,66,0.14)]"
                    : "-mb-px cursor-pointer border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-[var(--muted)] transition-colors hover:bg-[rgba(200,245,66,0.08)] hover:text-[var(--ink)]"
                }
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="mt-4" role="tabpanel">
          {activeTab === "goals" ? (
            <DataTable
              columns={goalsColumns}
              data={pagedRows as LeaderboardGoalsEntry[]}
              getRowKey={(row, index) =>
                `${row.playerName}-${row.teamName}-g-${pageOffset + index}`
              }
              isLoading={loading}
              loadingLabel="Carregando estatisticas..."
              emptyMessage="Nenhum goleador nesta temporada."
            />
          ) : null}
          {activeTab === "assists" ? (
            <DataTable
              columns={assistsColumns}
              data={pagedRows as LeaderboardAssistsEntry[]}
              getRowKey={(row, index) =>
                `${row.playerName}-${row.teamName}-a-${pageOffset + index}`
              }
              isLoading={loading}
              loadingLabel="Carregando estatisticas..."
              emptyMessage="Nenhum lider de assistencias nesta temporada."
            />
          ) : null}
          {activeTab === "ratings" ? (
            <DataTable
              columns={ratingsColumns}
              data={pagedRows as LeaderboardRatingsEntry[]}
              getRowKey={(row, index) =>
                `${row.playerName}-${row.teamName}-r-${pageOffset + index}`
              }
              isLoading={loading}
              loadingLabel="Carregando estatisticas..."
              emptyMessage="Nenhum MVP elegivel nesta temporada."
            />
          ) : null}

          {!loading && activeRows.length > PAGE_SIZE ? (
            <div className="mt-4 flex items-center justify-between gap-3">
              <p className="text-sm text-[var(--muted)]">
                Pagina {currentPage + 1} de {totalPages}
                {" · "}
                {activeRows.length} registros
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((prev) => Math.max(0, prev - 1))}
                  disabled={currentPage === 0}
                  className="rounded-md border border-[var(--stroke)] px-3 py-1.5 text-sm text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Anterior
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setPage((prev) => Math.min(totalPages - 1, prev + 1))
                  }
                  disabled={currentPage >= totalPages - 1}
                  className="rounded-md border border-[var(--stroke)] px-3 py-1.5 text-sm text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Proxima
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
