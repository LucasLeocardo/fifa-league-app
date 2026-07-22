"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type RowData,
} from "@tanstack/react-table";
import { useMemo, type ReactNode } from "react";

import { Loading } from "@/components/Loading";

export type ColumnAlign = "left" | "center" | "right";

export type DataTableColumn<T> = {
  /** Identificador unico da coluna. */
  key: string;
  /** Cabecalho exibido (texto ou nó). */
  header: ReactNode;
  /** Conteudo da celula. Se ausente, tenta usar row[key]. */
  render?: (row: T, index: number) => ReactNode;
  /** Alinhamento horizontal do conteudo. */
  align?: ColumnAlign;
  /** Classe extra aplicada nas celulas do corpo. */
  cellClassName?: string;
  /** Classe extra aplicada na celula de cabecalho. */
  headerClassName?: string;
  /** Largura fixa opcional (ex.: "3rem", "20%"). */
  width?: string;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  /** Chave estavel de cada linha. */
  getRowKey: (row: T, index: number) => string | number;
  /** Texto/nó quando nao ha dados. */
  emptyMessage?: ReactNode;
  /** Estado de carregamento (exibe o componente Loading por padrao). */
  isLoading?: boolean;
  loadingMessage?: ReactNode;
  /** Rotulo do loading padrao (ignorado se loadingMessage for informado). */
  loadingLabel?: ReactNode;
  /** Callback ao clicar numa linha (torna a linha interativa). */
  onRowClick?: (row: T, index: number) => void;
  /** Classe extra no wrapper externo. */
  className?: string;
};

// Metadados por coluna repassados ao TanStack Table (estilo/visual).
declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    align?: ColumnAlign;
    cellClassName?: string;
    headerClassName?: string;
    width?: string;
  }
}

const alignClass: Record<ColumnAlign, string> = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
};

function resolveCell<T>(
  column: DataTableColumn<T>,
  row: T,
  index: number,
): ReactNode {
  if (column.render) {
    return column.render(row, index);
  }
  const value = (row as Record<string, unknown>)[column.key];
  return value as ReactNode;
}

/**
 * Tabela generica reutilizavel com o visual da FIFA League.
 * Usa TanStack Table (@tanstack/react-table) internamente, mantendo uma
 * API simples via `columns`/`data`.
 */
export function DataTable<T>({
  columns,
  data,
  getRowKey,
  emptyMessage = "Nenhum registro encontrado.",
  isLoading = false,
  loadingMessage,
  loadingLabel,
  onRowClick,
  className,
}: Readonly<DataTableProps<T>>) {
  const columnDefs = useMemo<ColumnDef<T>[]>(
    () =>
      columns.map((column) => ({
        id: column.key,
        header: () => column.header,
        cell: (info) =>
          resolveCell(column, info.row.original, info.row.index),
        meta: {
          align: column.align,
          cellClassName: column.cellClassName,
          headerClassName: column.headerClassName,
          width: column.width,
        },
      })),
    [columns],
  );

  const table = useReactTable({
    data,
    columns: columnDefs,
    getCoreRowModel: getCoreRowModel(),
    getRowId: (row, index) => String(getRowKey(row, index)),
  });

  const wrapperClass = [
    "w-full overflow-x-auto border border-[var(--stroke)] bg-[var(--panel)] backdrop-blur-md",
    className ?? "",
  ]
    .join(" ")
    .trim();

  function renderMessageRow(message: ReactNode) {
    return (
      <tr>
        <td
          colSpan={columns.length}
          className="px-3 py-8 text-center text-[var(--muted)]"
        >
          {message}
        </td>
      </tr>
    );
  }

  function renderBody() {
    if (isLoading) {
      return renderMessageRow(
        loadingMessage ?? <Loading label={loadingLabel ?? "Carregando..."} />,
      );
    }
    if (data.length === 0) {
      return renderMessageRow(emptyMessage);
    }

    const interactive = Boolean(onRowClick);
    return table.getRowModel().rows.map((row) => (
      <tr
        key={row.id}
        onClick={
          interactive
            ? () => onRowClick?.(row.original, row.index)
            : undefined
        }
        className={[
          "border-b border-[var(--stroke)]/50 transition-colors last:border-b-0",
          interactive ? "cursor-pointer hover:bg-[rgba(200,245,66,0.06)]" : "",
        ]
          .join(" ")
          .trim()}
      >
        {row.getVisibleCells().map((cell) => {
          const meta = cell.column.columnDef.meta;
          return (
            <td
              key={cell.id}
              className={[
                "px-3 py-3 text-[var(--ink)]",
                alignClass[meta?.align ?? "left"],
                meta?.cellClassName ?? "",
              ]
                .join(" ")
                .trim()}
            >
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </td>
          );
        })}
      </tr>
    ));
  }

  return (
    <div className={wrapperClass}>
      <table className="w-full border-collapse text-sm">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr
              key={headerGroup.id}
              className="border-b border-[var(--stroke)]"
            >
              {headerGroup.headers.map((header) => {
                const meta = header.column.columnDef.meta;
                return (
                  <th
                    key={header.id}
                    scope="col"
                    style={meta?.width ? { width: meta.width } : undefined}
                    className={[
                      "px-3 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]",
                      alignClass[meta?.align ?? "left"],
                      meta?.headerClassName ?? "",
                    ]
                      .join(" ")
                      .trim()}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>{renderBody()}</tbody>
      </table>
    </div>
  );
}
