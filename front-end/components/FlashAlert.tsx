"use client";

import { useEffect } from "react";

import { useFlashStore } from "@/store/flash";

const AUTO_DISMISS_MS = 4200;

export function FlashAlert() {
  const message = useFlashStore((s) => s.message);
  const variant = useFlashStore((s) => s.variant);
  const clear = useFlashStore((s) => s.clear);

  useEffect(() => {
    if (!message) return;

    const timer = window.setTimeout(() => clear(), AUTO_DISMISS_MS);
    return () => window.clearTimeout(timer);
  }, [message, clear]);

  if (!message) return null;

  const isSuccess = variant === "success";

  return (
    <div
      className="pointer-events-none fixed inset-x-0 top-0 z-[100] flex justify-center px-4 pt-4 sm:px-6"
      aria-live={isSuccess ? "polite" : "assertive"}
    >
      <div
        role={isSuccess ? "status" : "alert"}
        className={[
          "flash-alert pointer-events-auto flex w-full max-w-xl items-start gap-3 border px-4 py-3.5 shadow-[0_12px_40px_rgba(0,0,0,0.35)] backdrop-blur-md",
          isSuccess
            ? "border-[rgba(200,245,66,0.45)] bg-[rgba(14,42,72,0.94)] text-[var(--lime)]"
            : "border-[rgba(255,107,107,0.45)] bg-[rgba(48,14,18,0.94)] text-[var(--danger)]",
        ].join(" ")}
      >
        <span
          aria-hidden
          className={[
            "mt-0.5 inline-block h-2.5 w-2.5 shrink-0",
            isSuccess ? "bg-[var(--lime)]" : "bg-[var(--danger)]",
          ].join(" ")}
        />
        <p className="min-w-0 flex-1 text-sm leading-snug text-[var(--ink)]">
          {message}
        </p>
        <button
          type="button"
          onClick={clear}
          className="shrink-0 text-xs uppercase tracking-[0.12em] text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
          aria-label="Fechar alerta"
        >
          Fechar
        </button>
      </div>
    </div>
  );
}
