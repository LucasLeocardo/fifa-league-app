"use client";

import type { ReactNode } from "react";

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
 * Configure as colunas via `columns` e passe os dados em `data`.
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
    return data.map((row, index) => (
      <tr
        key={getRowKey(row, index)}
        onClick={interactive ? () => onRowClick?.(row, index) : undefined}
        className={[
          "border-b border-[var(--stroke)]/50 transition-colors last:border-b-0",
          interactive ? "cursor-pointer hover:bg-[rgba(200,245,66,0.06)]" : "",
        ]
          .join(" ")
          .trim()}
      >
        {columns.map((column) => (
          <td
            key={column.key}
            className={[
              "px-3 py-3 text-[var(--ink)]",
              alignClass[column.align ?? "left"],
              column.cellClassName ?? "",
            ]
              .join(" ")
              .trim()}
          >
            {resolveCell(column, row, index)}
          </td>
        ))}
      </tr>
    ));
  }

  return (
    <div className={wrapperClass}>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-[var(--stroke)]">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                style={column.width ? { width: column.width } : undefined}
                className={[
                  "px-3 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]",
                  alignClass[column.align ?? "left"],
                  column.headerClassName ?? "",
                ]
                  .join(" ")
                  .trim()}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{renderBody()}</tbody>
      </table>
    </div>
  );
}
