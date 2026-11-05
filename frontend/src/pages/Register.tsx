import { Loader2, Lock, Mail, User, UserPlus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import api, { errorMessage } from "@/api/client";
import AuthLayout from "@/components/AuthLayout";
import { useAuth } from "@/context/AuthContext";

export default function Register() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enabled, setEnabled] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .get<{ registration_enabled: boolean }>("/auth/config/")
      .then((res) => setEnabled(res.data.registration_enabled))
      .catch(() => setEnabled(false));
  }, []);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await api.post("/auth/register/", { username, email, password });
      await login(username, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Registration failed."));
    } finally {
      setBusy(false);
    }
  };

  const signInLink = (
    <>
      Already have an account?{" "}
      <Link to="/login" className="font-semibold text-wine-400 hover:underline">
        Sign in
      </Link>
    </>
  );

  if (enabled === false) {
    return (
      <AuthLayout icon={UserPlus} title="Registration closed" footer={signInLink}>
        <p className="text-sm leading-relaxed text-slate-600">
          Self-registration is turned off on this server. Ask an administrator to create an account for you.
        </p>
      </AuthLayout>
    );
  }

  const icon = "pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400";

  return (
    <AuthLayout icon={UserPlus} title="Create your account" subtitle="Sign up to start triaging" footer={signInLink}>
      {error && <p className="notice-error mb-4">{error}</p>}

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label htmlFor="r-username" className="label-xs">
            Username
          </label>
          <div className="relative">
            <User className={icon} aria-hidden="true" />
            <input
              id="r-username"
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
          <label htmlFor="r-email" className="label-xs">
            Email
          </label>
          <div className="relative">
            <Mail className={icon} aria-hidden="true" />
            <input
              id="r-email"
              type="email"
              className="field pl-10"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>
        </div>
        <div>
          <label htmlFor="r-password" className="label-xs">
            Password
          </label>
          <div className="relative">
            <Lock className={icon} aria-hidden="true" />
            <input
              id="r-password"
              type="password"
              className="field pl-10"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
        </div>
        <div>
          <label htmlFor="r-confirm" className="label-xs">
            Confirm password
          </label>
          <div className="relative">
            <Lock className={icon} aria-hidden="true" />
            <input
              id="r-confirm"
              type="password"
              className="field pl-10"
              placeholder="••••••••"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
        </div>
        <button type="submit" disabled={busy || enabled === null} className="btn-primary w-full">
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
