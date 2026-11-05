import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `relative px-3 py-2 text-sm font-semibold transition-colors ${
    isActive ? "text-white" : "text-slate-300 hover:text-white"
  } ${isActive ? "after:absolute after:inset-x-3 after:-bottom-px after:h-0.5 after:bg-[#c0304f]" : ""}`;

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100">
      <nav className="border-b border-white/10 bg-[#0b1730]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 py-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#800020] text-sm font-black text-white">
                C
              </div>
              <span className="text-lg font-bold tracking-tight text-white">CVST</span>
            </div>
            <div className="flex items-center">
              <NavLink to="/" end className={linkClass}>
                Dashboard
              </NavLink>
              <NavLink to="/targets" className={linkClass}>
                Targets
              </NavLink>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold leading-tight text-white">{user?.username}</p>
              <p className="text-xs capitalize leading-tight text-slate-400">{user?.role}</p>
            </div>
            <button
              onClick={logout}
              className="rounded-md bg-white/10 px-3 py-1.5 text-sm font-semibold text-slate-100 ring-1 ring-white/20 transition hover:bg-[#800020] hover:ring-[#800020]"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>
      <Outlet />
    </div>
  );
}
