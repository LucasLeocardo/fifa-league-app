"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { Select, type SelectOption } from "@/components/Select";
import {
  ApiError,
  confirmFileRatings,
  getFileRatings,
  getPendingChildFiles,
  type MatchPlayerRatingRow,
  type PendingChildFile,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

const fieldClass =
  "w-full rounded-md border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-2.5 py-1.5 text-sm text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

type EditableRatingRow = MatchPlayerRatingRow & {
  rowKey: string;
};

export function StatsValidatorClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const name = useAuthStore((s) => s.name);
  const flashError = useFlashStore((s) => s.error);
  const flashSuccess = useFlashStore((s) => s.success);

  const [hydrated, setHydrated] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<PendingChildFile[]>([]);
  const [selectedFileId, setSelectedFileId] = useState("");
  const [rows, setRows] = useState<EditableRatingRow[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [loadingRatings, setLoadingRatings] = useState(false);
  const [saving, setSaving] = useState(false);

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

  const loadPendingFiles = useCallback(
    async (token: string) => {
      setLoadingFiles(true);
      try {
        const files = await getPendingChildFiles(token);
        setPendingFiles(files);
      } catch (err) {
        if (err instanceof ApiError) {
          flashError(err.message);
        } else {
          flashError("Nao foi possivel carregar os arquivos pendentes.");
        }
        setPendingFiles([]);
      } finally {
        setLoadingFiles(false);
      }
    },
    [flashError],
  );

  useEffect(() => {
    if (!hydrated || !accessToken || !isAdmin) return;
    void loadPendingFiles(accessToken);
  }, [hydrated, accessToken, isAdmin, loadPendingFiles]);

  const fileOptions: SelectOption[] = useMemo(
    () =>
      pendingFiles.map((file) => ({
        value: file.fileId,
        label: file.name,
      })),
    [pendingFiles],
  );

  async function handleFileChange(fileId: string) {
    setSelectedFileId(fileId);
    setRows([]);
    if (!fileId || !accessToken) return;

    setLoadingRatings(true);
    try {
      const ratings = await getFileRatings(accessToken, fileId);
      setRows(
        ratings.map((row, index) => ({
          ...row,
          rowKey: `${row.fileId}-${index}`,
        })),
      );
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel carregar as estatisticas do arquivo.");
      }
      setRows([]);
    } finally {
      setLoadingRatings(false);
    }
  }

  function updateRow(
    rowKey: string,
    patch: Partial<
      Pick<EditableRatingRow, "playerName" | "goals" | "assists" | "averageRating">
    >,
  ) {
    setRows((current) =>
      current.map((row) => (row.rowKey === rowKey ? { ...row, ...patch } : row)),
    );
  }

  async function handleSave() {
    if (!accessToken || !selectedFileId || rows.length === 0) return;

    const invalid = rows.find(
      (row) =>
        !row.playerName.trim() ||
        !row.sourceGameId ||
        !row.teamCycleSeasonId ||
        !Number.isFinite(row.goals) ||
        row.goals < 0 ||
        !Number.isFinite(row.assists) ||
        row.assists < 0,
    );
    if (invalid) {
      flashError(
        "Preencha nome, gols e assistencias validos. sourceGameId/teamCycleSeasonId sao obrigatorios.",
      );
      return;
    }

    setSaving(true);
    try {
      await confirmFileRatings(accessToken, {
        fileId: selectedFileId,
        players: rows.map((row) => ({
          playerName: row.playerName.trim(),
          goals: row.goals,
          assists: row.assists,
          averageRating: row.averageRating,
          sourceGameId: row.sourceGameId as string,
          teamCycleSeasonId: row.teamCycleSeasonId as string,
        })),
      });
      flashSuccess("Estatisticas salvas com sucesso.");
      setSelectedFileId("");
      setRows([]);
      await loadPendingFiles(accessToken);
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel salvar as estatisticas.");
      }
    } finally {
      setSaving(false);
    }
  }

  const columns = useMemo<DataTableColumn<EditableRatingRow>[]>(
    () => [
      {
        key: "position",
        header: "Posição",
        width: "5rem",
        render: (row) => (
          <span className="text-[var(--ink)]">{row.position || "—"}</span>
        ),
      },
      {
        key: "playerName",
        header: "Nome",
        render: (row) => (
          <input
            aria-label={`Nome do jogador ${row.position}`}
            value={row.playerName}
            disabled={saving}
            onChange={(e) =>
              updateRow(row.rowKey, { playerName: e.target.value })
            }
            className={fieldClass}
          />
        ),
      },
      {
        key: "goals",
        header: "Número de gols",
        align: "center",
        width: "8rem",
        render: (row) => (
          <input
            aria-label={`Gols de ${row.playerName}`}
            type="number"
            min={0}
            value={row.goals}
            disabled={saving}
            onChange={(e) => {
              const value = Number(e.target.value);
              updateRow(row.rowKey, {
                goals: Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0,
              });
            }}
            className={`${fieldClass} text-center`}
          />
        ),
      },
      {
        key: "assists",
        header: "Assistências",
        align: "center",
        width: "8rem",
        render: (row) => (
          <input
            aria-label={`Assistencias de ${row.playerName}`}
            type="number"
            min={0}
            value={row.assists}
            disabled={saving}
            onChange={(e) => {
              const value = Number(e.target.value);
              updateRow(row.rowKey, {
                assists: Number.isFinite(value)
                  ? Math.max(0, Math.trunc(value))
                  : 0,
              });
            }}
            className={`${fieldClass} text-center`}
          />
        ),
      },
      {
        key: "averageRating",
        header: "Média",
        align: "center",
        width: "7rem",
        render: (row) => (
          <input
            aria-label={`Media de ${row.playerName}`}
            type="number"
            min={0}
            max={10}
            step={0.1}
            value={row.averageRating ?? ""}
            disabled={saving}
            onChange={(e) => {
              const raw = e.target.value;
              if (raw === "") {
                updateRow(row.rowKey, { averageRating: null });
                return;
              }
              const value = Number(raw);
              updateRow(row.rowKey, {
                averageRating: Number.isFinite(value) ? value : null,
              });
            }}
            className={`${fieldClass} text-center`}
          />
        ),
      },
    ],
    [saving],
  );

  if (!hydrated || !accessToken || !isAdmin) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <p className="text-[var(--muted)]">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="px-6 py-10 md:px-10">
      <div className="mx-auto w-full max-w-5xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <header>
            <h1 className="font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
              Validador de estatísticas
            </h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Ola, {name} · revise e confirme os CSVs gerados pelo OCR
            </p>
          </header>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving || !selectedFileId || rows.length === 0}
            className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>

        <div className="mt-8 grid max-w-md grid-cols-[6.5rem_1fr] items-center gap-3">
          <span className="text-sm font-medium text-[var(--muted)]">Arquivo</span>
          <Select
            aria-label="Selecionar arquivo pendente"
            options={fileOptions}
            value={selectedFileId}
            onChange={(value) => void handleFileChange(value)}
            disabled={loadingFiles || saving || fileOptions.length === 0}
            placeholder={
              loadingFiles
                ? "Carregando arquivos..."
                : fileOptions.length === 0
                  ? "Nenhum arquivo pendente"
                  : "Selecione um arquivo"
            }
            className="w-full"
          />
        </div>

        <div className="mt-8">
          <DataTable
            columns={columns}
            data={rows}
            getRowKey={(row) => row.rowKey}
            isLoading={loadingRatings}
            loadingLabel="Carregando estatisticas..."
            emptyMessage={
              selectedFileId
                ? "Nenhuma linha encontrada neste arquivo."
                : "Selecione um arquivo para validar as estatisticas."
            }
          />
        </div>
      </div>
    </div>
  );
}
