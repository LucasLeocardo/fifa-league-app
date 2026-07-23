"use client";

import { ChartColumn, LayoutDashboard, LogOut, Trophy, Users, CalendarDays } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { ApiError, logout as logoutRequest } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useFlashStore } from "@/store/flash";

type NavItem = {
  title: string;
  href: string;
  icon: typeof Trophy;
};

const navItems: NavItem[] = [
  { title: "Classificação", href: "/standings", icon: Trophy },
  { title: "Elenco", href: "/squad", icon: Users },
  { title: "Estatísticas", href: "/stats", icon: ChartColumn },
  { title: "Resultados", href: "/results", icon: CalendarDays },
  { title: "Início", href: "/home", icon: LayoutDashboard },
];

export function AppSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const name = useAuthStore((s) => s.name);
  const accessToken = useAuthStore((s) => s.accessToken);
  const clearSession = useAuthStore((s) => s.clearSession);
  const flashSuccess = useFlashStore((s) => s.success);
  const flashError = useFlashStore((s) => s.error);
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      if (accessToken) {
        await logoutRequest(accessToken);
      }
      flashSuccess("Sessao encerrada.");
    } catch (err) {
      if (err instanceof ApiError) {
        flashError(err.message);
      } else {
        flashError("Nao foi possivel encerrar no servidor. Sessao local limpa.");
      }
    } finally {
      clearSession();
      setLoggingOut(false);
      router.replace("/login");
    }
  }

  return (
    <Sidebar collapsible="offcanvas">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-2">
          <span className="grid size-8 place-items-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
            <Trophy className="size-4" />
          </span>
          <span className="font-[family-name:var(--font-display)] text-sm tracking-[0.2em] text-sidebar-primary">
            FIFA LEAGUE
          </span>
        </div>
      </SidebarHeader>

      <SidebarSeparator />

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navegação</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    isActive={pathname === item.href}
                    render={<Link href={item.href} />}
                  >
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        {name ? (
          <p className="px-2 text-xs text-sidebar-foreground/70">
            Logado como{" "}
            <span className="font-medium text-sidebar-foreground">{name}</span>
          </p>
        ) : null}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={handleLogout} disabled={loggingOut}>
              <LogOut />
              <span>{loggingOut ? "Saindo..." : "Sair"}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
