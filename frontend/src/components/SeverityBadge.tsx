import { cn } from "@/lib/utils";
import type { Severity } from "@/types";

const SEVERITIES: Record<Severity, { label: string; className: string }> = {
  critical: { label: "Critical", className: "bg-wine-800 text-white ring-wine-800" },
  high: { label: "High", className: "bg-wine-100 text-wine-800 ring-wine-600/30" },
  medium: { label: "Medium", className: "bg-amber-50 text-amber-800 ring-amber-600/30" },
  low: { label: "Low", className: "bg-sky-50 text-sky-800 ring-sky-600/25" },
  info: { label: "Info", className: "bg-slate-100 text-slate-600 ring-slate-400/40" },
};

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "#65001a",
  high: "#c0304f",
  medium: "#d99a2b",
  low: "#2b5490",
  info: "#94a3b8",
};

export const EMPTY_SEVERITY: Record<Severity, number> = {
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
  info: 0,
};

export default function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const style = SEVERITIES[severity] ?? SEVERITIES.info;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-[0.08em] ring-1",
        style.className,
        className,
      )}
    >
      {style.label}
    </span>
  );
}
