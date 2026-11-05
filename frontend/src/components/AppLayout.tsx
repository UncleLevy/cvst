import { Crosshair, LayoutDashboard, LogOut, ShieldAlert, type LucideIcon } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

export const NAV_ITEMS: { to: string; label: string; icon: LucideIcon; end?: boolean }[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/targets", label: "Targets", icon: Crosshair },
  { to: "/findings", label: "Findings", icon: ShieldAlert },
];

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-wine-700 text-base font-black text-white shadow-lg shadow-wine-900/40">
        C
      </div>
      <div className="leading-tight">
        <p className="text-[15px] font-bold tracking-[0.16em] text-white">CVST</p>
        <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-400">Vuln triage</p>
      </div>
    </div>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-[#eff1f6]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 flex-col bg-gradient-to-b from-navy-900 via-navy-800 to-navy-700 px-4 py-6 lg:flex">
        <Brand />
        <nav className="mt-9 flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                  isActive
                    ? "bg-white/10 text-white shadow-inner ring-1 ring-white/15"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-100",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn("h-4 w-4", isActive ? "text-wine-400" : "text-slate-500")} strokeWidth={2.2} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mb-3 rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">Scope reminder</p>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-400">
            Only scan systems you own or have written permission to test.
          </p>
        </div>

        <div className="flex items-center justify-between gap-2 rounded-xl bg-white/[0.06] px-3 py-2.5 ring-1 ring-white/10">
          <div className="min-w-0 leading-tight">
            <p className="truncate text-sm font-semibold text-white">{user?.username}</p>
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            aria-label="Sign out"
            className="rounded-lg p-2 text-slate-400 transition hover:bg-wine-700 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      <div className="lg:pl-60">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-navy-800/10 bg-navy-800 px-4 py-3 lg:hidden">
          <Brand />
          <nav className="flex items-center gap-1 overflow-x-auto">
            {NAV_ITEMS.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                    isActive ? "bg-white/15 text-white" : "text-slate-300 hover:text-white",
                  )
                }
              >
                {label}
              </NavLink>
            ))}
            <button
              onClick={logout}
              aria-label="Sign out"
              className="ml-1 rounded-lg p-1.5 text-slate-300 hover:bg-wine-700 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
