import Link from "next/link";

type AuthShellProps = {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer: React.ReactNode;
};

export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <main className="pitch-atmosphere relative flex min-h-dvh items-stretch overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 left-[12%] hidden w-px bg-gradient-to-b from-transparent via-[var(--lime)]/35 to-transparent md:block"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 top-1/2 hidden h-[28rem] w-[28rem] -translate-y-1/2 rounded-full border border-[var(--lime)]/15 md:block"
      />

      <section className="relative z-10 mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 items-center gap-10 px-6 py-12 md:grid-cols-[1.1fr_0.9fr] md:gap-16 md:px-10 lg:px-14">
        <div className="auth-rise max-w-xl">
          <p className="mb-4 font-[family-name:var(--font-display)] text-sm tracking-[0.35em] text-[var(--lime)]">
            TEMPORADA AO VIVO
          </p>
          <h1 className="font-[family-name:var(--font-display)] text-[clamp(3.4rem,12vw,6.5rem)] leading-[0.88] tracking-wide text-[var(--ink)]">
            FIFA
            <span className="block text-[var(--lime)]">LEAGUE</span>
          </h1>
          <div className="auth-flare mt-5 h-1 w-28 bg-[var(--lime)]" />
          <p className="mt-6 max-w-md text-base leading-relaxed text-[var(--muted)] md:text-lg">
            Organize confrontos, acompanhe o ranking e transforme cada partida em
            disputa de temporada.
          </p>
        </div>

        <div className="auth-rise-delay w-full max-w-md justify-self-center md:justify-self-end">
          <div className="border border-[var(--stroke)] bg-[var(--panel)] p-7 backdrop-blur-md md:p-8">
            <h2 className="font-[family-name:var(--font-display)] text-3xl tracking-wide text-[var(--ink)] md:text-4xl">
              {title}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">{subtitle}</p>
            <div className="mt-7">{children}</div>
            <div className="mt-6 border-t border-[var(--stroke)] pt-5 text-sm text-[var(--muted)]">
              {footer}
            </div>
          </div>
          <p className="mt-4 text-center text-xs tracking-wide text-[var(--muted)]">
            <Link href="/" className="transition-colors hover:text-[var(--lime)]">
              FIFA League
            </Link>{" "}
            · entre em campo
          </p>
        </div>
      </section>
    </main>
  );
}
