"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Loading } from "@/components/Loading";
import { NewMatchModal } from "@/components/NewMatchModal";
import { Select, type SelectOption } from "@/components/Select";
import { UploadMatchPhotosModal } from "@/components/UploadMatchPhotosModal";
import {
  ApiError,
  getCycleSeasons,
  getMatches,
  getTeamCycleSeasons,
  type CycleSeason,
  type MatchResult,
  type TeamCycleSeason,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

type PhaseKey = "first" | "second" | "semi" | "third" | "final" | "other";

type PhaseDef = {
  key: PhaseKey;
  title: string;
  subtitle: string;
  match: (typeName: string) => boolean;
};

const PHASES: PhaseDef[] = [
  {
    key: "final",
    title: "Final",
    subtitle: "Decisão do título",
    match: (name) => /^final$|final\b/i.test(name) && !/semi/i.test(name),
  },
  {
    key: "third",
    title: "Terceiro Lugar",
    subtitle: "Disputa de bronze",
    match: (name) => /terceiro|3[oº]?\s*lugar|bronze/i.test(name),
  },
  {
    key: "semi",
    title: "Semifinais",
    subtitle: "Mata-mata",
    match: (name) => /semi/i.test(name),
  },
  {
    key: "second",
    title: "Segundo Turno",
    subtitle: "Fase de liga · volta",
    match: (name) => /segundo|2[oº]?\s*turno|second/i.test(name),
  },
  {
    key: "first",
    title: "Primeiro Turno",
    subtitle: "Fase de liga · ida",
    match: (name) => /primeiro|1[oº]?\s*turno|first/i.test(name),
  },
];

function resolvePhase(matchTypeName: string | null): PhaseKey {
  const name = (matchTypeName ?? "").trim();
  if (!name) return "other";
  for (const phase of PHASES) {
    if (phase.match(name)) return phase.key;
  }
  return "other";
}

function formatScore(value: number | null): string {
  return value === null ? "-" : String(value);
}

function MatchScoreboard({
  match,
  focusTeamName,
  index,
  canUploadPhotos,
  onUploadClick,
}: Readonly<{
  match: MatchResult;
  focusTeamName: string;
  index: number;
  canUploadPhotos: boolean;
  onUploadClick: (match: MatchResult) => void;
}>) {
  const homeScore = match.homeScore;
  const awayScore = match.awayScore;
  const decided = homeScore !== null && awayScore !== null;
  const homeWins = decided && homeScore > awayScore;
  const awayWins = decided && awayScore > homeScore;
  const draw = decided && homeScore === awayScore;
  const showUpload = canUploadPhotos && !match.fileWasUploaded;

  const homeIsFocus =
    focusTeamName.length > 0 &&
    match.homeTeamName.toLowerCase() === focusTeamName.toLowerCase();
  const awayIsFocus =
    focusTeamName.length > 0 &&
    match.awayTeamName.toLowerCase() === focusTeamName.toLowerCase();

  return (
    <article
      className={[
        "results-match relative grid grid-cols-[1fr_auto_1fr] items-center gap-3 border-b border-[var(--stroke)]/40 px-2 py-4 last:border-b-0 md:gap-6 md:px-4",
        canUploadPhotos ? "pr-[7.75rem] md:pr-[8.5rem]" : "",
      ]
        .join(" ")
        .trim()}
      style={{ animationDelay: `${index * 45}ms` }}
    >
      <p
        className={[
          "truncate text-right text-sm font-medium md:text-base",
          homeIsFocus ? "text-[var(--lime)]" : "text-[var(--ink)]",
          homeWins ? "font-semibold" : "",
        ]
          .join(" ")
          .trim()}
      >
        {match.homeTeamName || "Mandante"}
      </p>

      <div className="flex min-w-[7.5rem] items-center justify-center gap-2">
        <span
          className={[
            "inline-flex min-w-[2rem] justify-center font-[family-name:var(--font-display)] text-2xl tracking-wide md:text-3xl",
            homeWins ? "text-[var(--lime)]" : "text-[var(--ink)]",
          ]
            .join(" ")
            .trim()}
        >
          {formatScore(homeScore)}
        </span>
        <span className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">
          {draw ? "x" : "–"}
        </span>
        <span
          className={[
            "inline-flex min-w-[2rem] justify-center font-[family-name:var(--font-display)] text-2xl tracking-wide md:text-3xl",
            awayWins ? "text-[var(--lime)]" : "text-[var(--ink)]",
          ]
            .join(" ")
            .trim()}
        >
          {formatScore(awayScore)}
        </span>
      </div>

      <p
        className={[
          "truncate text-left text-sm font-medium md:text-base",
          awayIsFocus ? "text-[var(--lime)]" : "text-[var(--ink)]",
          awayWins ? "font-semibold" : "",
        ]
          .join(" ")
          .trim()}
      >
        {match.awayTeamName || "Visitante"}
      </p>

      {showUpload ? (
        <button
          type="button"
          onClick={() => onUploadClick(match)}
          aria-label="Enviar fotos da partida"
          title="Enviar fotos"
          className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer whitespace-nowrap rounded-md border border-[var(--stroke)] px-2.5 py-1.5 text-xs font-medium text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] md:right-4"
        >
          Upload de Fotos
        </button>
      ) : null}
    </article>
  );
}

export function ResultsClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const name = useAuthStore((s) => s.name);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const flashError = useFlashStore((s) => s.error);

  const [hydrated, setHydrated] = useState(false);
  const [cycleSeasons, setCycleSeasons] = useState<CycleSeason[]>([]);
  const [selectedCycleSeasonId, setSelectedCycleSeasonId] = useState("");
  const [teams, setTeams] = useState<TeamCycleSeason[]>([]);
  const [selectedTeamCycleSeasonId, setSelectedTeamCycleSeasonId] = useState("");
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [uploadMatch, setUploadMatch] = useState<MatchResult | null>(null);

  useEffect(() => {
    const markHydrated = () => setHydrated(true);
    const unsubscribe = useAuthStore.persist.onFinishHydration(markHydrated);
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(markHydrated);
    }
    return unsubscribe;
  }, []);

  const loadMatches = useCallback(
    async (token: string, teamCycleSeasonId?: string) => {
      setLoading(true);
      try {
        const response = await getMatches(token, teamCycleSeasonId);
        setMatches(response);
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar os resultados.");
        }
        setMatches([]);
      } finally {
        setLoading(false);
      }
    },
    [flashError],
  );

  const loadTeamsAndMatches = useCallback(
    async (token: string, cycleSeasonId?: string) => {
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
        setMatches([]);
        setLoading(false);
        return;
      }
      await loadMatches(token, initialTeamId);
    },
    [flashError, loadMatches],
  );

  const loadSeasonsTeamsAndMatches = useCallback(
    async (token: string) => {
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
      await loadTeamsAndMatches(token, initialSeasonId);
    },
    [flashError, loadTeamsAndMatches],
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
      if (active) void loadSeasonsTeamsAndMatches(token);
    });

    return () => {
      active = false;
    };
  }, [hydrated, accessToken, router, loadSeasonsTeamsAndMatches]);

  function handleSeasonChange(id: string) {
    setSelectedCycleSeasonId(id);
    if (accessToken) {
      void loadTeamsAndMatches(accessToken, id || undefined);
    }
  }

  function handleTeamChange(id: string) {
    setSelectedTeamCycleSeasonId(id);
    if (accessToken) {
      void loadMatches(accessToken, id || undefined);
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

  const focusTeamName =
    teams.find((team) => team.teamCycleSeasonId === selectedTeamCycleSeasonId)
      ?.teamName ?? "";

  const canCreateMatch = useMemo(() => {
    if (!isAdmin) return false;
    const selectedSeason = cycleSeasons.find(
      (season) => season.cycleSeasonId === selectedCycleSeasonId,
    );
    return selectedSeason?.isCurrentSeason === true;
  }, [isAdmin, cycleSeasons, selectedCycleSeasonId]);

  const phasesWithMatches = useMemo(() => {
    const buckets = new Map<PhaseKey, MatchResult[]>();
    for (const phase of PHASES) {
      buckets.set(phase.key, []);
    }
    buckets.set("other", []);

    for (const match of matches) {
      const key = resolvePhase(match.matchTypeName);
      buckets.get(key)?.push(match);
    }

    const known = PHASES.map((phase) => ({
      ...phase,
      matches: buckets.get(phase.key) ?? [],
    })).filter((phase) => phase.matches.length > 0);

    const otherMatches = buckets.get("other") ?? [];
    if (otherMatches.length > 0) {
      known.push({
        key: "other",
        title: "Outros jogos",
        subtitle: "Tipos nao classificados",
        match: () => true,
        matches: otherMatches,
      });
    }
    return known;
  }, [matches]);

  if (!hydrated || !accessToken) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="px-6 py-10 md:px-10">
      <div className="mx-auto w-full max-w-3xl">
        <header>
          <h1 className="font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
            Resultados
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Ola, {name} · placares por fase do campeonato
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
          {canCreateMatch ? (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110"
            >
              Nova partida
            </button>
          ) : null}
        </div>

        <div className="mt-8">
          {loading ? (
            <div className="flex min-h-[40vh] items-center justify-center border border-[var(--stroke)] bg-[var(--panel)] backdrop-blur-md">
              <Loading label="Carregando resultados..." />
            </div>
          ) : null}
          {!loading && phasesWithMatches.length === 0 ? (
            <p className="border border-[var(--stroke)] bg-[var(--panel)] px-4 py-10 text-center text-sm text-[var(--muted)] backdrop-blur-md">
              Nenhuma partida encontrada para este time.
            </p>
          ) : null}
          {!loading && phasesWithMatches.length > 0 ? (
            <div className="flex flex-col gap-8">
              {phasesWithMatches.map((phase, phaseIndex) => (
                <section
                  key={phase.key}
                  className="results-phase"
                  style={{ animationDelay: `${phaseIndex * 80}ms` }}
                >
                  <div className="mb-3 flex items-end justify-between gap-3 border-b border-[var(--stroke)] pb-3">
                    <div>
                      <p className="font-[family-name:var(--font-display)] text-xs tracking-[0.28em] text-[var(--lime)]">
                        {String(phaseIndex + 1).padStart(2, "0")}
                      </p>
                      <h2 className="mt-1 font-[family-name:var(--font-display)] text-2xl tracking-wide text-[var(--ink)] md:text-3xl">
                        {phase.title}
                      </h2>
                      <p className="mt-0.5 text-xs text-[var(--muted)]">
                        {phase.subtitle}
                      </p>
                    </div>
                    <p className="text-xs text-[var(--muted)]">
                      {phase.matches.length}{" "}
                      {phase.matches.length === 1 ? "jogo" : "jogos"}
                    </p>
                  </div>

                  <div className="border border-[var(--stroke)] bg-[var(--panel)] backdrop-blur-md">
                    {phase.matches.map((match, index) => (
                      <MatchScoreboard
                        key={match.matchId}
                        match={match}
                        focusTeamName={focusTeamName}
                        index={index}
                        canUploadPhotos={canCreateMatch}
                        onUploadClick={setUploadMatch}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {accessToken ? (
        <NewMatchModal
          open={modalOpen}
          accessToken={accessToken}
          teamOptions={teamOptions}
          onClose={() => setModalOpen(false)}
          onCreated={() => {
            void loadMatches(accessToken, selectedTeamCycleSeasonId || undefined);
          }}
        />
      ) : null}

      {accessToken && isAdmin ? (
        <UploadMatchPhotosModal
          open={uploadMatch !== null}
          accessToken={accessToken}
          match={uploadMatch}
          onClose={() => setUploadMatch(null)}
          onUploaded={() => {
            void loadMatches(accessToken, selectedTeamCycleSeasonId || undefined);
          }}
        />
      ) : null}
    </div>
  );
}
