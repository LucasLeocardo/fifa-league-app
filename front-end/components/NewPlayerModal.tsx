"use client";

import { useEffect, useRef, useState } from "react";

import { MultiSelect } from "@/components/MultiSelect";
import { type SelectOption } from "@/components/Select";
import {
  ApiError,
  createPlayer,
  getPositions,
  type Position,
} from "@/lib/api";
import { useFlashStore } from "@/store/flash";

const fieldClass =
  "w-full rounded-lg border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-3.5 py-2.5 text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

const labelClass =
  "mb-1.5 block text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]";

type NewPlayerModalProps = {
  open: boolean;
  accessToken: string;
  onClose: () => void;
  onCreated: () => void;
};

export function NewPlayerModal({
  open,
  accessToken,
  onClose,
  onCreated,
}: Readonly<NewPlayerModalProps>) {
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const [positions, setPositions] = useState<Position[]>([]);
  const [playerName, setPlayerName] = useState("");
  const [overall, setOverall] = useState("");
  const [positionIds, setPositionIds] = useState<string[]>([]);
  const [loadingPositions, setLoadingPositions] = useState(false);
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

    setPlayerName("");
    setOverall("");
    setPositionIds([]);

    let active = true;
    setLoadingPositions(true);
    queueMicrotask(() => {
      void (async () => {
        try {
          const list = await getPositions(accessToken);
          if (active) setPositions(list);
        } catch (err) {
          if (!active) return;
          if (err instanceof ApiError) {
            flashError(err.message);
          } else {
            flashError("Nao foi possivel carregar as posicoes.");
          }
        } finally {
          if (active) setLoadingPositions(false);
        }
      })();
    });

    return () => {
      active = false;
    };
  }, [open, accessToken, flashError]);

  const positionOptions: SelectOption[] = positions.map((position) => ({
    value: position.id,
    label: position.code,
  }));

  const trimmedName = playerName.trim();
  const parsedOverall = Number(overall);
  const canSave =
    trimmedName.length > 0 &&
    Number.isInteger(parsedOverall) &&
    parsedOverall >= 1 &&
    parsedOverall <= 99 &&
    positionIds.length > 0 &&
    !loadingPositions &&
    !saving;

  async function handleSubmit(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSave) return;

    setSaving(true);
    try {
      await createPlayer(accessToken, {
        name: trimmedName,
        overall: parsedOverall,
        positionIds,
      });
      flashSuccess("Jogador cadastrado com sucesso.");
      onCreated();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel cadastrar o jogador.");
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
        Novo jogador
      </h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Cadastre nome, overall e posições.
      </p>

      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
        <div>
          <label className={labelClass} htmlFor="new-player-name">
            Nome
          </label>
          <input
            id="new-player-name"
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className={fieldClass}
            disabled={saving}
            placeholder="Nome do jogador"
            autoComplete="off"
          />
        </div>

        <div>
          <label className={labelClass} htmlFor="new-player-overall">
            Overall
          </label>
          <input
            id="new-player-overall"
            type="number"
            min={1}
            max={99}
            value={overall}
            onChange={(e) => setOverall(e.target.value)}
            className={fieldClass}
            disabled={saving}
            placeholder="Ex.: 85"
          />
        </div>

        <div>
          <span className={labelClass}>Posições</span>
          <MultiSelect
            aria-label="Posicoes do jogador"
            options={positionOptions}
            value={positionIds}
            onChange={setPositionIds}
            disabled={saving || loadingPositions || positionOptions.length === 0}
            placeholder={
              loadingPositions
                ? "Carregando posicoes..."
                : "Selecione uma ou mais"
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
            disabled={!canSave}
            className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
