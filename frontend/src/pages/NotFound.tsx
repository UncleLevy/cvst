import { Link, useLocation } from "react-router-dom";

export default function NotFound() {
  const { pathname } = useLocation();

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#eff1f6] p-6">
      <div className="surface w-full max-w-md p-8 text-center">
        <p className="text-6xl font-light tracking-tight text-wine-700">404</p>
        <div className="mx-auto my-4 h-0.5 w-12 bg-slate-200" />
        <h1 className="text-xl font-bold text-navy-800">Page not found</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          There is no page at <span className="font-mono text-slate-700">{pathname}</span>.
        </p>
        <Link to="/" className="btn-primary mt-6">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
