"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError, deletePlayer } from "@/lib/api";
import { useFlashStore } from "@/store/flash";

type DeletePlayerModalProps = {
  open: boolean;
  accessToken: string;
  playerId: string;
  playerName: string;
  onClose: () => void;
  onDeleted: () => void;
};

export function DeletePlayerModal({
  open,
  accessToken,
  playerId,
  playerName,
  onClose,
  onDeleted,
}: Readonly<DeletePlayerModalProps>) {
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  async function handleConfirm() {
    setDeleting(true);
    try {
      await deletePlayer(accessToken, playerId);
      flashSuccess(`Jogador "${playerName}" removido.`);
      onDeleted();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel deletar o jogador.");
      }
    } finally {
      setDeleting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="fixed inset-0 z-50 m-auto w-[calc(100%-2rem)] max-w-md border border-[var(--stroke)] bg-[rgba(6,22,42,0.98)] p-6 text-[var(--ink)] shadow-2xl backdrop:bg-black/60 backdrop:backdrop-blur-sm"
      onClose={onClose}
      onCancel={onClose}
    >
      <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-wide text-[var(--ink)]">
        Deletar jogador
      </h2>
      <p className="mt-3 text-sm text-[var(--muted)]">
        Tem certeza que deseja deletar o jogador{" "}
        <span className="font-semibold text-[var(--ink)]">{playerName}</span>?
        Essa ação não pode ser desfeita.
      </p>

      <div className="mt-6 flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          disabled={deleting}
          className="cursor-pointer rounded-md border border-[var(--stroke)] px-4 py-2 text-sm text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={() => void handleConfirm()}
          disabled={deleting}
          className="cursor-pointer rounded-md border border-red-400/60 bg-red-500/15 px-4 py-2 text-sm font-semibold text-red-300 transition-colors hover:bg-red-500/25 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {deleting ? "Deletando..." : "Deletar"}
        </button>
      </div>
    </dialog>
  );
}
