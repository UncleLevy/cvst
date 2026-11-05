import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: number | string;
  hint?: string;
  accent: string;
  icon?: LucideIcon;
  className?: string;
}

export default function StatCard({ label, value, hint, accent, icon: Icon, className }: StatCardProps) {
  return (
    <div className={cn("surface relative overflow-hidden p-4 sm:p-5", className)}>
      <span className="absolute inset-x-0 top-0 h-[3px]" style={{ backgroundColor: accent }} />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
          <p className="mt-2 text-[28px] font-bold leading-none tracking-tight text-navy-800">{value}</p>
          {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
        </div>
        {Icon && (
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
            style={{ backgroundColor: `${accent}14`, color: accent }}
          >
            <Icon className="h-4 w-4" strokeWidth={2.2} />
          </span>
        )}
      </div>
    </div>
  );
}
