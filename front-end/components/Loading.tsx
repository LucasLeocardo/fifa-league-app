import type { ReactNode } from "react";

export type LoadingSize = "sm" | "md" | "lg";

type LoadingProps = {
  /** Texto opcional exibido ao lado do spinner. */
  label?: ReactNode;
  /** Tamanho do spinner. */
  size?: LoadingSize;
  /** Classe extra no wrapper. */
  className?: string;
};

const spinnerSize: Record<LoadingSize, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-9 w-9 border-[3px]",
};

/**
 * Indicador de carregamento reutilizavel (tema FIFA League).
 * Use durante chamadas a API, inclusive como estado de loading de tabelas.
 */
export function Loading({
  label = "Carregando...",
  size = "md",
  className,
}: Readonly<LoadingProps>) {
  const wrapperClass = [
    "flex items-center justify-center gap-3 text-[var(--muted)]",
    className ?? "",
  ]
    .join(" ")
    .trim();

  return (
    <output aria-live="polite" className={wrapperClass}>
      <span
        aria-hidden
        className={[
          "inline-block animate-spin rounded-full border-[var(--lime)]/25 border-t-[var(--lime)]",
          spinnerSize[size],
        ].join(" ")}
      />
      {label ? <span className="text-sm">{label}</span> : null}
      <span className="sr-only">Carregando</span>
    </output>
  );
}
