"use client";

import { useEffect, useRef, useState } from "react";

import { Select, type SelectOption } from "@/components/Select";
import { ApiError, uploadMatchPhotos, type MatchResult } from "@/lib/api";
import { useFlashStore } from "@/store/flash";

const labelClass =
  "mb-1.5 block text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]";

type UploadMatchPhotosModalProps = {
  open: boolean;
  accessToken: string;
  match: MatchResult | null;
  onClose: () => void;
  onUploaded: () => void;
};

export function UploadMatchPhotosModal({
  open,
  accessToken,
  match,
  onClose,
  onUploaded,
}: Readonly<UploadMatchPhotosModalProps>) {
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [side, setSide] = useState<"home" | "away" | "">("");
  const [files, setFiles] = useState<File[]>([]);
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
    setSide("");
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [open, match?.matchId]);

  const teamOptions: SelectOption[] = match
    ? [
        {
          value: "home",
          label: match.homeTeamName || "Time da casa",
        },
        {
          value: "away",
          label: match.awayTeamName || "Visitante",
        },
      ]
    : [];

  async function handleSubmit(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!match) return;

    if (!side) {
      flashError("Selecione de qual time sao as imagens.");
      return;
    }
    if (files.length === 0) {
      flashError("Selecione ao menos uma imagem.");
      return;
    }

    const teamCycleSeasonId =
      side === "home" ? match.homeTeamId : match.awayTeamId;

    if (!teamCycleSeasonId) {
      flashError("Nao foi possivel identificar o time selecionado.");
      return;
    }

    setSaving(true);
    try {
      await uploadMatchPhotos(accessToken, {
        photos: files,
        sourceGameId: match.matchId,
        teamCycleSeasonId,
      });
      flashSuccess(
        files.length === 1
          ? "Foto enviada com sucesso."
          : `${files.length} fotos enviadas com sucesso.`,
      );
      onUploaded();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel enviar as fotos.");
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
        Upload de fotos
      </h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        {match
          ? `${match.homeTeamName || "Mandante"} × ${match.awayTeamName || "Visitante"}`
          : "Selecione as imagens da partida."}
      </p>

      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
        <div>
          <span className={labelClass}>Time das imagens</span>
          <Select
            aria-label="Time das imagens"
            options={teamOptions}
            value={side}
            onChange={(value) => {
              if (value === "home" || value === "away") {
                setSide(value);
              } else {
                setSide("");
              }
            }}
            disabled={saving || !match}
            placeholder="Casa ou visitante"
            className="w-full"
            portal={false}
          />
        </div>

        <div>
          <label className={labelClass} htmlFor="match-photos">
            Imagens
          </label>
          <input
            id="match-photos"
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            disabled={saving}
            onChange={(e) => {
              const selected = e.target.files
                ? Array.from(e.target.files)
                : [];
              setFiles(selected);
            }}
            className="block w-full cursor-pointer text-sm text-[var(--muted)] file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-[var(--stroke)] file:bg-transparent file:px-3 file:py-2 file:text-sm file:font-medium file:text-[var(--ink)] hover:file:border-[var(--lime)] hover:file:text-[var(--lime)]"
          />
          {files.length > 0 ? (
            <p className="mt-2 text-xs text-[var(--muted)]">
              {files.length}{" "}
              {files.length === 1 ? "arquivo selecionado" : "arquivos selecionados"}
            </p>
          ) : null}
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
            disabled={saving || !match}
            className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "Enviando..." : "Fazer upload"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
