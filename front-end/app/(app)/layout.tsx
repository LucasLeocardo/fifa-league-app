import type { ReactNode } from "react";

import { AppShell } from "@/components/AppShell";

/**
 * Layout das telas autenticadas. Todas as rotas dentro de (app) herdam a
 * sidebar de navegacao. Rotas publicas (login, register) ficam fora do grupo.
 */
export default function AppGroupLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return <AppShell>{children}</AppShell>;
}
