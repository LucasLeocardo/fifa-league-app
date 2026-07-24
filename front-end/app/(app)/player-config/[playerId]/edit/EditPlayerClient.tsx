"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { MultiSelect } from "@/components/MultiSelect";
import { Select, type SelectOption } from "@/components/Select";
import {
  ApiError,
  getPlayer,
  getPositions,
  getTeamCycleSeasons,
  updatePlayer,
  type PlayerSearchResult,
  type Position,
  type TeamCycleSeason,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

const fieldClass =
  "w-full rounded-lg border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-3.5 py-2.5 text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

const labelClass =
  "mb-1.5 block text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]";

function sortedIds(ids: string[]): string {
  return [...ids].sort((a, b) => a.localeCompare(b)).join(",");
}

export function EditPlayerClient() {
  const router = useRouter();
  const params = useParams<{ playerId: string }>();
  const playerId = params.playerId;

  const accessToken = useAuthStore((s) => s.accessToken);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);

  const [hydrated, setHydrated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [initial, setInitial] = useState<PlayerSearchResult | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [teams, setTeams] = useState<TeamCycleSeason[]>([]);

  const [playerName, setPlayerName] = useState("");
  const [overall, setOverall] = useState("");
  const [positionIds, setPositionIds] = useState<string[]>([]);
  const [teamCycleSeasonId, setTeamCycleSeasonId] = useState("");

  useEffect(() => {
    const markHydrated = () => setHydrated(true);
    const unsubscribe = useAuthStore.persist.onFinishHydration(markHydrated);
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(markHydrated);
    }
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    if (!isAdmin) {
      router.replace("/standings");
    }
  }, [hydrated, accessToken, isAdmin, router]);

  useEffect(() => {
    if (!hydrated || !accessToken || !isAdmin || !playerId) return;

    let active = true;
    setLoading(true);
    queueMicrotask(() => {
      void (async () => {
        try {
          const [player, positionList, teamList] = await Promise.all([
            getPlayer(accessToken, playerId),
            getPositions(accessToken),
            getTeamCycleSeasons(accessToken),
          ]);
          if (!active) return;
          setInitial(player);
          setPositions(positionList);
          setTeams(teamList);
          setPlayerName(player.playerName);
          setOverall(
            player.overall === null || player.overall === undefined
              ? ""
              : String(player.overall),
          );
          setPositionIds(player.positionIds ?? []);
          setTeamCycleSeasonId(player.teamCycleSeasonId ?? "");
        } catch (err) {
          if (!active) return;
          if (err instanceof ApiError) {
            flashError(err.message);
          } else {
            flashError("Nao foi possivel carregar o jogador.");
          }
          router.replace("/player-config");
        } finally {
          if (active) setLoading(false);
        }
      })();
    });

    return () => {
      active = false;
    };
  }, [hydrated, accessToken, isAdmin, playerId, flashError, router]);

  const positionOptions: SelectOption[] = positions.map((position) => ({
    value: position.id,
    label: position.code,
  }));

  const teamOptions: SelectOption[] = [
    { value: "", label: "Sem time" },
    ...teams.map((team) => ({
      value: team.teamCycleSeasonId,
      label: team.teamName,
    })),
  ];

  const trimmedName = playerName.trim();
  const parsedOverall = Number(overall);
  const overallValid =
    Number.isInteger(parsedOverall) &&
    parsedOverall >= 1 &&
    parsedOverall <= 99;

  const isDirty = useMemo(() => {
    if (!initial) return false;
    const initialOverall =
      initial.overall === null || initial.overall === undefined
        ? ""
        : String(initial.overall);
    return (
      trimmedName !== initial.playerName.trim() ||
      overall !== initialOverall ||
      sortedIds(positionIds) !== sortedIds(initial.positionIds ?? []) ||
      teamCycleSeasonId !== (initial.teamCycleSeasonId ?? "")
    );
  }, [initial, trimmedName, overall, positionIds, teamCycleSeasonId]);

  const canSave =
    isDirty &&
    trimmedName.length > 0 &&
    overallValid &&
    positionIds.length > 0 &&
    !saving &&
    !loading;

  async function handleSave(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !playerId || !canSave) return;

    setSaving(true);
    try {
      const updated = await updatePlayer(accessToken, playerId, {
        name: trimmedName,
        overall: parsedOverall,
        positionIds,
        teamCycleSeasonId: teamCycleSeasonId || null,
      });
      setInitial(updated);
      setPlayerName(updated.playerName);
      setOverall(
        updated.overall === null || updated.overall === undefined
          ? ""
          : String(updated.overall),
      );
      setPositionIds(updated.positionIds ?? []);
      setTeamCycleSeasonId(updated.teamCycleSeasonId ?? "");
      flashSuccess("Jogador atualizado com sucesso.");
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel atualizar o jogador.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (!hydrated || !accessToken || !isAdmin) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando...</p>
      </div>
    );
  }

  if (loading || !initial) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando jogador...</p>
      </div>
    );
  }

  return (
    <div className="px-6 py-10 md:px-10">
      <div className="mx-auto w-full max-w-xl">
        <button
          type="button"
          onClick={() => router.push("/player-config")}
          className="cursor-pointer text-sm text-[var(--muted)] transition-colors hover:text-[var(--lime)]"
        >
          ← Voltar
        </button>

        <header className="mt-4">
          <h1 className="font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
            Editar jogador
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {initial.playerName}
          </p>
        </header>

        <form className="mt-8 flex flex-col gap-4" onSubmit={handleSave}>
          <div>
            <label className={labelClass} htmlFor="edit-player-name">
              Nome
            </label>
            <input
              id="edit-player-name"
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className={fieldClass}
              disabled={saving}
              autoComplete="off"
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="edit-player-overall">
              Overall
            </label>
            <input
              id="edit-player-overall"
              type="number"
              min={1}
              max={99}
              value={overall}
              onChange={(e) => setOverall(e.target.value)}
              className={fieldClass}
              disabled={saving}
            />
          </div>

          <div>
            <span className={labelClass}>Posições</span>
            <MultiSelect
              aria-label="Posicoes do jogador"
              options={positionOptions}
              value={positionIds}
              onChange={setPositionIds}
              disabled={saving || positionOptions.length === 0}
              placeholder="Selecione uma ou mais"
              className="w-full"
            />
          </div>

          <div>
            <span className={labelClass}>Time atual</span>
            <Select
              aria-label="Time do jogador"
              options={teamOptions}
              value={teamCycleSeasonId}
              onChange={setTeamCycleSeasonId}
              disabled={saving}
              placeholder="Selecione o time"
              className="w-full"
            />
          </div>

          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => router.push("/player-config")}
              disabled={saving}
              className="cursor-pointer rounded-md border border-[var(--stroke)] px-4 py-2 text-sm text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!canSave}
              className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
