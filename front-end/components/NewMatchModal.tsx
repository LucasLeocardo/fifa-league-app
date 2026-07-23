"use client";

import { useEffect, useRef, useState } from "react";

import { Select, type SelectOption } from "@/components/Select";
import {
  ApiError,
  createMatch,
  getMatchTypes,
  type MatchType,
} from "@/lib/api";
import { useFlashStore } from "@/store/flash";

const fieldClass =
  "w-full rounded-lg border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-3.5 py-2.5 text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

const labelClass =
  "mb-1.5 block text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]";

type NewMatchModalProps = {
  open: boolean;
  accessToken: string;
  /** Mesmas opções de time já carregadas na tela de resultados. */
  teamOptions: SelectOption[];
  onClose: () => void;
  onCreated: () => void;
};

export function NewMatchModal({
  open,
  accessToken,
  teamOptions,
  onClose,
  onCreated,
}: Readonly<NewMatchModalProps>) {
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const [matchTypes, setMatchTypes] = useState<MatchType[]>([]);
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const [matchTypeId, setMatchTypeId] = useState("");
  const [homeScore, setHomeScore] = useState("0");
  const [awayScore, setAwayScore] = useState("0");
  const [loadingTypes, setLoadingTypes] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;

    setHomeTeamId("");
    setAwayTeamId("");
    setMatchTypeId("");
    setHomeScore("0");
    setAwayScore("0");

    let active = true;
    setLoadingTypes(true);
    queueMicrotask(() => {
      void (async () => {
        try {
          const types = await getMatchTypes(accessToken);
          if (active) setMatchTypes(types);
        } catch (err) {
          if (!active) return;
          if (err instanceof ApiError) {
            flashError(err.message);
          } else {
            flashError("Nao foi possivel carregar os tipos de partida.");
          }
        } finally {
          if (active) setLoadingTypes(false);
        }
      })();
    });

    return () => {
      active = false;
    };
  }, [open, accessToken, flashError]);

  const matchTypeOptions: SelectOption[] = matchTypes.map((type) => ({
    value: type.matchTypeId,
    label: type.name,
  }));

  async function handleSubmit(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!homeTeamId || !awayTeamId || !matchTypeId) {
      flashError("Preencha times e o tipo da partida.");
      return;
    }
    if (homeTeamId === awayTeamId) {
      flashError("Mandante e visitante precisam ser times diferentes.");
      return;
    }

    const parsedHome = Number(homeScore);
    const parsedAway = Number(awayScore);
    if (
      !Number.isInteger(parsedHome) ||
      parsedHome < 0 ||
      !Number.isInteger(parsedAway) ||
      parsedAway < 0
    ) {
      flashError("Informe placares inteiros maiores ou iguais a zero.");
      return;
    }

    setSaving(true);
    try {
      await createMatch(accessToken, {
        homeTeamId,
        awayTeamId,
        matchTypeId,
        homeScore: parsedHome,
        awayScore: parsedAway,
      });
      flashSuccess("Partida registrada com sucesso.");
      onCreated();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel salvar a partida.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="fixed inset-0 z-50 m-auto w-[calc(100%-2rem)] max-w-xl border border-[var(--stroke)] bg-[rgba(6,22,42,0.98)] p-6 text-[var(--ink)] shadow-2xl backdrop:bg-black/60 backdrop:backdrop-blur-sm"
      onClose={onClose}
      onCancel={onClose}
    >
      <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-wide text-[var(--ink)]">
        Nova partida
      </h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Registre o resultado de uma nova partida.
      </p>

      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
        <div>
          <span className={labelClass}>Time da casa</span>
          <Select
            aria-label="Time da casa"
            options={teamOptions}
            value={homeTeamId}
            onChange={setHomeTeamId}
            disabled={saving || teamOptions.length === 0}
            placeholder="Selecione o mandante"
            className="w-full"
            portal={false}
          />
        </div>

        <div>
          <span className={labelClass}>Time de fora</span>
          <Select
            aria-label="Time de fora"
            options={teamOptions}
            value={awayTeamId}
            onChange={setAwayTeamId}
            disabled={saving || teamOptions.length === 0}
            placeholder="Selecione o visitante"
            className="w-full"
            portal={false}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass} htmlFor="home-score">
              Gols mandante
            </label>
            <input
              id="home-score"
              type="number"
              min={0}
              value={homeScore}
              onChange={(e) => setHomeScore(e.target.value)}
              className={fieldClass}
              disabled={saving}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="away-score">
              Gols visitante
            </label>
            <input
              id="away-score"
              type="number"
              min={0}
              value={awayScore}
              onChange={(e) => setAwayScore(e.target.value)}
              className={fieldClass}
              disabled={saving}
            />
          </div>
        </div>

        <div>
          <span className={labelClass}>Tipo da partida</span>
          <Select
            aria-label="Tipo da partida"
            options={matchTypeOptions}
            value={matchTypeId}
            onChange={setMatchTypeId}
            disabled={saving || loadingTypes || matchTypeOptions.length === 0}
            placeholder={
              loadingTypes ? "Carregando tipos..." : "Selecione o tipo"
            }
            className="w-full"
            portal={false}
          />
        </div>

        <div className="mt-2 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="cursor-pointer rounded-md border border-[var(--stroke)] px-4 py-2 text-sm text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saving || loadingTypes}
            className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
