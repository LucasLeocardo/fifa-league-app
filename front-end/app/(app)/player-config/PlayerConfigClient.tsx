"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { DeletePlayerModal } from "@/components/DeletePlayerModal";
import { NewPlayerModal } from "@/components/NewPlayerModal";
import {
  ApiError,
  searchPlayers,
  type PlayerSearchResult,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

const fieldClass =
  "w-full rounded-lg border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-3.5 py-2.5 text-[var(--ink)] outline-none transition-[border-color,box-shadow] placeholder:text-[var(--muted)] focus:border-[var(--lime)] focus:shadow-[0_0_0_3px_rgba(200,245,66,0.12)]";

const PLAYER_DELETE_ALLOWED_NAME = "Leocardo";

export function PlayerConfigClient() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const name = useAuthStore((s) => s.name);
  const flashError = useFlashStore((s) => s.error);

  const [hydrated, setHydrated] = useState(false);
  const [query, setQuery] = useState("");
  const [players, setPlayers] = useState<PlayerSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [playerToDelete, setPlayerToDelete] =
    useState<PlayerSearchResult | null>(null);

  const canDeletePlayers = name === PLAYER_DELETE_ALLOWED_NAME;

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

  const trimmedQuery = query.trim();
  const showSearchButton = trimmedQuery.length > 0;

  async function handleSearch() {
    if (!accessToken || !trimmedQuery) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const results = await searchPlayers(accessToken, trimmedQuery);
      setPlayers(results);
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel buscar jogadores.");
      }
      setPlayers([]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (showSearchButton) {
      void handleSearch();
    }
  }

  const columns = useMemo<DataTableColumn<PlayerSearchResult>[]>(
    () => [
      {
        key: "playerName",
        header: "Jogador",
        render: (row) => (
          <span className="font-medium text-[var(--ink)]">{row.playerName}</span>
        ),
      },
      {
        key: "positions",
        header: "Posição",
        render: (row) =>
          row.positions.length > 0 ? row.positions.join(", ") : "—",
      },
      {
        key: "overall",
        header: "Overall",
        align: "center",
        render: (row) => row.overall ?? "—",
      },
      {
        key: "teamName",
        header: "Time atual",
        render: (row) => row.teamName ?? "Sem time",
      },
      {
        key: "actions",
        header: "",
        align: "right",
        width: canDeletePlayers ? "10rem" : "6rem",
        render: (row) => (
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() =>
                router.push(`/player-config/${row.playerId}/edit`)
              }
              className="cursor-pointer rounded-md border border-[var(--stroke)] px-3 py-1.5 text-xs font-medium text-[var(--ink)] transition-colors hover:border-[var(--lime)] hover:text-[var(--lime)]"
            >
              Editar
            </button>
            {canDeletePlayers ? (
              <button
                type="button"
                onClick={() => setPlayerToDelete(row)}
                className="cursor-pointer rounded-md border border-red-400/50 px-3 py-1.5 text-xs font-medium text-red-300 transition-colors hover:border-red-300 hover:bg-red-500/10"
              >
                Deletar
              </button>
            ) : null}
          </div>
        ),
      },
    ],
    [router, canDeletePlayers],
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
      <div className="mx-auto w-full max-w-4xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <header>
            <h1 className="font-[family-name:var(--font-display)] text-4xl tracking-wide text-[var(--ink)] md:text-5xl">
              Configuração de jogadores
            </h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Ola, {name} · busca por nome
            </p>
          </header>
          <button
            type="button"
            onClick={() => setCreateModalOpen(true)}
            className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110"
          >
            Novo jogador
          </button>
        </div>

        <form
          className="mt-8 flex flex-wrap items-center gap-3"
          onSubmit={handleSubmit}
        >
          <div className="min-w-[16rem] flex-1">
            <label className="sr-only" htmlFor="player-search">
              Buscar jogador
            </label>
            <input
              id="player-search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Digite o nome do jogador..."
              className={fieldClass}
              disabled={loading}
              autoComplete="off"
            />
          </div>
          {showSearchButton ? (
            <button
              type="submit"
              disabled={loading}
              className="cursor-pointer rounded-md bg-[var(--lime)] px-4 py-2.5 text-sm font-semibold text-[#052e16] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Pesquisando..." : "Pesquisar"}
            </button>
          ) : null}
        </form>

        <div className="mt-4">
          <DataTable
            columns={columns}
            data={players}
            getRowKey={(row) => row.playerId}
            isLoading={loading}
            loadingLabel="Buscando jogadores..."
            emptyMessage={
              hasSearched
                ? "Nenhum jogador encontrado para essa busca."
                : "Digite um nome e clique em Pesquisar para listar jogadores."
            }
          />
        </div>
      </div>

      <NewPlayerModal
        open={createModalOpen}
        accessToken={accessToken}
        onClose={() => setCreateModalOpen(false)}
        onCreated={() => {
          if (trimmedQuery) {
            void handleSearch();
          }
        }}
      />

      {playerToDelete ? (
        <DeletePlayerModal
          open
          accessToken={accessToken}
          playerId={playerToDelete.playerId}
          playerName={playerToDelete.playerName}
          onClose={() => setPlayerToDelete(null)}
          onDeleted={() => {
            setPlayers((current) =>
              current.filter((p) => p.playerId !== playerToDelete.playerId),
            );
          }}
        />
      ) : null}
    </div>
  );
}
