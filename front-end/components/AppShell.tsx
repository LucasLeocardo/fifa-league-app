"use client";

import type { ReactNode } from "react";

import { AppSidebar } from "@/components/AppSidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

type AppShellProps = {
  children: ReactNode;
};

/**
 * Casca das telas autenticadas: sidebar de navegacao a esquerda + area de
 * conteudo com uma barra superior contendo o gatilho da sidebar.
 * Aplicada via layout do route group (app), entao vale para todas as telas.
 */
export function AppShell({ children }: Readonly<AppShellProps>) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="pitch-atmosphere">
        <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-4 backdrop-blur">
          <SidebarTrigger className="text-[var(--ink)] hover:bg-[rgba(200,245,66,0.12)] hover:text-[var(--lime)]" />
          <span className="font-[family-name:var(--font-display)] text-sm tracking-[0.2em] text-[var(--lime)]">
            FIFA LEAGUE
          </span>
        </header>
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
