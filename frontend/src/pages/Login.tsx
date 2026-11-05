import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/";
  if (user) return <Navigate to={from} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Invalid username or password."));
    } finally {
      setBusy(false);
    }
  };

  const input =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 shadow-sm focus:border-[#800020] focus:outline-none focus:ring-1 focus:ring-[#800020]";

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#0b1730] via-[#12264a] to-[#1b3a6b] px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-xl bg-[#800020] text-2xl font-black text-white shadow-lg">
            C
          </div>
          <h1 className="text-3xl font-bold tracking-tight !text-white">CVST</h1>
          <p className="mt-1 text-sm text-slate-300">Vulnerability scanning &amp; triage</p>
        </div>

        <form onSubmit={submit} className="overflow-hidden rounded-2xl bg-white shadow-2xl">
          <div className="h-1.5 bg-gradient-to-r from-[#800020] to-[#b3304f]" />
          <div className="space-y-4 p-6">
            <h2 className="text-lg font-semibold text-[#12264a]">Sign in</h2>

            {error && (
              <p className="rounded-lg border border-[#800020]/30 bg-[#800020]/10 px-3 py-2 text-sm font-medium text-[#800020]">
                {error}
              </p>
            )}

            <div>
              <label htmlFor="username" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Username
              </label>
              <input
                id="username"
                className={input}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
                required
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Password
              </label>
              <input
                id="password"
                type="password"
                className={input}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <button type="submit" disabled={busy} className="btn-primary w-full disabled:opacity-60">
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
