"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { Select, type SelectOption } from "@/components/Select";
import {
  ApiError,
  getCycleSeasons,
  getSquad,
  getTeamCycleSeasons,
  updateShirtNumber,
  type CycleSeason,
  type SquadPlayer,
  type TeamCycleSeason,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

const euroFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

function formatEuro(value: number | null): string {
  return value === null ? "-" : euroFormatter.format(value);
}

// Prioridade de posicoes na ordem: goleiros, zagueiros, laterais direitos,
// laterais esquerdos, volantes, meio-centrais/meio-campistas, pontas e
// atacantes. Cobre codigos em PT e EN; codigos desconhecidos vao para o fim.
const POSITION_ORDER = [
  // Goleiros
  "GOL", "GK",
  // Zagueiros
  "ZAG", "CB",
  // Laterais direitos
  "LD", "RB", "RWB",
  // Laterais esquerdos
  "LE", "LB", "LWB",
  // Volantes
  "VOL", "CDM",
  // Meio-centrais e meio-campistas
  "MC", "CM", "MEI", "MEC", "CAM", "MD", "RM", "ME", "LM",
  // Pontas
  "PD", "RW", "PE", "LW",
  // Atacantes
  "SA", "SS", "CF", "ATA", "CA", "ST",
];

function positionRank(code: string): number {
  const index = POSITION_ORDER.indexOf(code.toUpperCase());
  return index === -1 ? POSITION_ORDER.length : index;
}

function playerRank(player: SquadPlayer): number {
  if (player.positions.length === 0) {
    return Number.POSITIVE_INFINITY;
  }
  return Math.min(...player.positions.map(positionRank));
}

function comparePlayers(a: SquadPlayer, b: SquadPlayer): number {
  const rankDiff = playerRank(a) - playerRank(b);
  if (rankDiff !== 0) {
    return rankDiff;
  }
  // Empate: desempata pela string de posicoes e depois pelo nome.
  const positionsDiff = a.positions
    .join("/")
    .localeCompare(b.positions.join("/"));
  if (positionsDiff !== 0) {
    return positionsDiff;
  }
  return a.playerName.localeCompare(b.playerName);
}

export function SquadClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const name = useAuthStore((s) => s.name);
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);

  const [hydrated, setHydrated] = useState(false);
  const [cycleSeasons, setCycleSeasons] = useState<CycleSeason[]>([]);
  const [selectedCycleSeasonId, setSelectedCycleSeasonId] = useState("");
  const [teams, setTeams] = useState<TeamCycleSeason[]>([]);
  const [selectedTeamCycleSeasonId, setSelectedTeamCycleSeasonId] = useState("");
  const [players, setPlayers] = useState<SquadPlayer[]>([]);
  const [loading, setLoading] = useState(true);
  // Rascunhos de numero de camisa por teamSquadId (apenas linhas editadas).
  const [shirtDrafts, setShirtDrafts] = useState<Record<string, string>>({});
  const [savingShirts, setSavingShirts] = useState(false);

  useEffect(() => {
    const markHydrated = () => setHydrated(true);
    const unsubscribe = useAuthStore.persist.onFinishHydration(markHydrated);
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(markHydrated);
    }
    return unsubscribe;
  }, []);

  const loadSquad = useCallback(
    async (token: string, teamCycleSeasonId?: string) => {
      setLoading(true);
      setShirtDrafts({});
      try {
        const response = await getSquad(token, teamCycleSeasonId);
        setPlayers(response.players);
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar o elenco.");
        }
      } finally {
        setLoading(false);
      }
    },
    [flashError],
  );

  const loadTeamsAndSquad = useCallback(
    async (token: string, cycleSeasonId?: string) => {
      // Time selecionado por padrao: o que tem isMyTeam = true.
      let initialTeamId: string | undefined;
      try {
        const teamCycleSeasons = await getTeamCycleSeasons(token, cycleSeasonId);
        setTeams(teamCycleSeasons);
        const myTeam = teamCycleSeasons.find((team) => team.isMyTeam);
        initialTeamId =
          myTeam?.teamCycleSeasonId ?? teamCycleSeasons[0]?.teamCycleSeasonId;
        setSelectedTeamCycleSeasonId(initialTeamId ?? "");
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar os times.");
        }
        setTeams([]);
        setSelectedTeamCycleSeasonId("");
        setPlayers([]);
        setLoading(false);
        return;
      }
      await loadSquad(token, initialTeamId);
    },
    [flashError, loadSquad],
  );

  const loadSeasonsTeamsAndSquad = useCallback(
    async (token: string) => {
      // Temporada selecionada por padrao: a que tem isCurrentSeason = true.
      let initialSeasonId: string | undefined;
      try {
        const seasons = await getCycleSeasons(token);
        setCycleSeasons(seasons);
        const current = seasons.find((season) => season.isCurrentSeason);
        initialSeasonId = current?.cycleSeasonId ?? seasons[0]?.cycleSeasonId;
        setSelectedCycleSeasonId(initialSeasonId ?? "");
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar as temporadas.");
        }
      }
      await loadTeamsAndSquad(token, initialSeasonId);
    },
    [flashError, loadTeamsAndSquad],
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
      if (active) void loadSeasonsTeamsAndSquad(token);
    });

    return () => {
      active = false;
    };
  }, [hydrated, accessToken, router, loadSeasonsTeamsAndSquad]);

  function handleSeasonChange(id: string) {
    setSelectedCycleSeasonId(id);
    if (accessToken) {
      void loadTeamsAndSquad(accessToken, id || undefined);
    }
  }

  function handleTeamChange(id: string) {
    setSelectedTeamCycleSeasonId(id);
    if (accessToken) {
      void loadSquad(accessToken, id || undefined);
    }
  }

  const seasonOptions: SelectOption[] = cycleSeasons.map((season) => ({
    value: season.cycleSeasonId,
    label: `${season.cycleName} - ${season.seasonName}`,
  }));

  const teamOptions: SelectOption[] = teams.map((team) => ({
    value: team.teamCycleSeasonId,
    label: team.teamName,
  }));

  const sortedPlayers = useMemo(
    () => [...players].sort(comparePlayers),
    [players],
  );

  const totalSquadValue = useMemo(
    () =>
      players.reduce(
        (sum, player) => sum + (player.playerCost ?? 0),
        0,
      ),
    [players],
  );

  // A coluna de numero de camisa so e editavel quando o time selecionado
  // e o do usuario (isMyTeam).
  const editable = useMemo(
    () =>
      teams.some(
        (team) =>
          team.teamCycleSeasonId === selectedTeamCycleSeasonId && team.isMyTeam,
      ),
    [teams, selectedTeamCycleSeasonId],
  );

  const playersById = useMemo(() => {
    const map = new Map<string, SquadPlayer>();
    for (const player of players) {
      map.set(player.teamSquadId, player);
    }
    return map;
  }, [players]);

  const handleShirtDraft = useCallback((teamSquadId: string, value: string) => {
    setShirtDrafts((prev) => ({ ...prev, [teamSquadId]: value }));
  }, []);

  // Somente rascunhos validos e diferentes do valor original entram como update.
  const pendingUpdates = useMemo(() => {
    return Object.entries(shirtDrafts)
      .map(([teamSquadId, raw]) => ({ teamSquadId, raw: raw.trim() }))
      .filter(({ teamSquadId, raw }) => {
        if (raw === "") return false;
        const parsed = Number(raw);
        if (!Number.isInteger(parsed) || parsed < 0) return false;
        const original = playersById.get(teamSquadId)?.shirtNumber ?? null;
        return parsed !== original;
      })
      .map(({ teamSquadId, raw }) => ({
        teamSquadId,
        shirtNumber: Number(raw),
      }));
  }, [shirtDrafts, playersById]);

  const handleSaveShirts = useCallback(async () => {
    if (!accessToken || pendingUpdates.length === 0) return;
    setSavingShirts(true);
    try {
      await Promise.all(
        pendingUpdates.map((update) =>
          updateShirtNumber(accessToken, update.teamSquadId, update.shirtNumber),
        ),
      );
      flashSuccess("Numeros de camisa atualizados com sucesso.");
      await loadSquad(accessToken, selectedTeamCycleSeasonId || undefined);
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel salvar os numeros de camisa.");
      }
    } finally {
      setSavingShirts(false);
    }
  }, [
    accessToken,
    pendingUpdates,
    selectedTeamCycleSeasonId,
    loadSquad,
    flashSuccess,
    flashError,
  ]);

  const columns: DataTableColumn<SquadPlayer>[] = useMemo(
    () => [
      {
        key: "shirtNumber",
        header: "#",
        align: "center",
        width: "4rem",
        cellClassName: "font-semibold text-[var(--lime)]",
        render: (row) =>
          editable ? (
            <input
              key={`${row.teamSquadId}:${row.shirtNumber ?? ""}`}
              type="number"
              min={0}
              defaultValue={row.shirtNumber ?? ""}
              onChange={(e) => handleShirtDraft(row.teamSquadId, e.target.value)}
              aria-label={`Numero da camisa de ${row.playerName}`}
              className="w-16 rounded-md border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-2 py-1 text-center text-[var(--ink)] focus:border-[var(--lime)] focus:outline-none"
            />
          ) : (
            (row.shirtNumber ?? "-")
          ),
      },
      {
        key: "playerName",
        header: "Jogador",
        cellClassName: "font-medium text-[var(--ink)]",
        render: (row) => row.playerName,
      },
      {
        key: "overall",
        header: "Overall",
        align: "center",
        render: (row) => row.overall ?? "-",
      },
      {
        key: "positions",
        header: "Posições",
        render: (row) =>
          row.positions.length > 0 ? row.positions.join("/") : "-",
      },
      {
        key: "gamesPlayed",
        header: "J",
        align: "center",
        render: (row) => row.gamesPlayed,
      },
      {
        key: "totalGoals",
        header: "G",
        align: "center",
        render: (row) => row.totalGoals,
      },
      {
        key: "totalAssists",
        header: "A",
        align: "center",
        render: (row) => row.totalAssists,
      },
      {
        key: "averageRating",
        header: "Nota",
        align: "center",
        render: (row) =>
          row.averageRating === null
            ? "-"
            : row.averageRating.toFixed(2).replace(".", ","),
      },
      {
        key: "playerCost",
        header: "Valor",
        align: "right",
        render: (row) => formatEuro(row.playerCost),
      },
    ],
    [editable, handleShirtDraft],
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
      <div className="mx-auto w-full max-w-6xl">
        <header>
          <h1 className="font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
            Meu elenco
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Ola, {name} · temporada atual
          </p>
        </header>

        <div className="mt-8 flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-col gap-3">
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
            <div className="grid grid-cols-[6.5rem_16rem] items-center gap-3">
              <span className="text-sm font-medium text-[var(--muted)]">Time</span>
              <Select
                aria-label="Selecionar time"
                options={teamOptions}
                value={selectedTeamCycleSeasonId}
                onChange={handleTeamChange}
                disabled={loading || teamOptions.length === 0}
                placeholder="Selecione o time"
                className="w-64"
              />
            </div>
          </div>
          {editable && pendingUpdates.length > 0 ? (
            <button
              type="button"
              onClick={() => void handleSaveShirts()}
              disabled={savingShirts}
              className="rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {savingShirts ? "Salvando..." : "Salvar Atualizações"}
            </button>
          ) : null}
        </div>

        <div className="mt-4 flex items-end justify-end">
          <p className="text-sm text-[var(--muted)]">
            Valor total do elenco{" "}
            <span className="font-semibold text-[var(--lime)]">
              {formatEuro(totalSquadValue)}
            </span>
          </p>
        </div>

        <div className="mt-2">
          <DataTable
            columns={columns}
            data={sortedPlayers}
            getRowKey={(row) => row.teamSquadId}
            isLoading={loading}
            loadingLabel="Carregando elenco..."
            emptyMessage="Nenhum jogador no elenco ainda."
          />
        </div>

        <p className="mt-4 text-xs text-[var(--muted)]">
          J: jogos · G: gols · A: assistencias · Nota: media das notas
        </p>
      </div>
    </div>
  );
}
