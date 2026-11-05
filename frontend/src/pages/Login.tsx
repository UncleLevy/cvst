import { Loader2, Lock, LogIn, User } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import api, { errorMessage } from "@/api/client";
import AuthLayout from "@/components/AuthLayout";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [registrationEnabled, setRegistrationEnabled] = useState(false);

  useEffect(() => {
    api
      .get<{ registration_enabled: boolean }>("/auth/config/")
      .then((res) => setRegistrationEnabled(res.data.registration_enabled))
      .catch(() => setRegistrationEnabled(false));
  }, []);

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

  return (
    <AuthLayout
      icon={LogIn}
      title="Welcome back"
      subtitle="Sign in to the vulnerability triage console"
      footer={
        registrationEnabled ? (
          <>
            Don't have an account?{" "}
            <Link to="/register" className="font-semibold text-wine-400 hover:underline">
              Create one
            </Link>
          </>
        ) : undefined
      }
    >
      {error && <p className="notice-error mb-4">{error}</p>}

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label htmlFor="username" className="label-xs">
            Username
          </label>
          <div className="relative">
            <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              id="username"
              className="field pl-10"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              required
            />
          </div>
        </div>
        <div>
          <label htmlFor="password" className="label-xs">
            Password
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              id="password"
              type="password"
              className="field pl-10"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
        </div>
        <button type="submit" disabled={busy} className="btn-primary w-full">
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthLayout>
  );
}
