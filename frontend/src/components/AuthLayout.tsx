import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface AuthLayoutProps {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  footer?: ReactNode;
  children: ReactNode;
}

export default function AuthLayout({ icon: Icon, title, subtitle, footer, children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-navy-900 via-navy-800 to-navy-600 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-wine-700 text-white shadow-lg shadow-wine-900/40">
            <Icon className="h-6 w-6" aria-hidden="true" />
          </div>
          <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.3em] text-wine-400">CVST</p>
          <h1 className="text-3xl font-bold tracking-tight text-white">{title}</h1>
          {subtitle && <p className="mt-2 text-sm text-slate-300">{subtitle}</p>}
        </div>

        <div className="overflow-hidden rounded-2xl bg-white shadow-raised">
          <div className="h-1.5 bg-gradient-to-r from-wine-700 to-wine-500" />
          <div className="p-7">{children}</div>
        </div>

        {footer && <p className="mt-6 text-center text-sm text-slate-300">{footer}</p>}
      </div>
    </div>
  );
}
