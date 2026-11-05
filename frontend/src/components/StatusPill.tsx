import { cn } from "@/lib/utils";
import { statusKind } from "@/lib/scanActions";

const STYLES = {
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  failed: "bg-wine-100 text-wine-800 ring-wine-600/25",
  active: "bg-slate-100 text-navy-700 ring-navy-700/15",
} as const;

const DOT = {
  completed: "bg-emerald-500",
  failed: "bg-wine-700",
  active: "bg-navy-600",
} as const;

const LABELS: Record<string, string> = {
  idle: "Idle",
  queued: "Queued",
  scanning: "Scanning",
  analysing: "Analysing",
  reporting: "Reporting",
  completed: "Completed",
  failed: "Failed",
};

export default function StatusPill({ status, className }: { status: string; className?: string }) {
  const kind = statusKind(status);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1",
        STYLES[kind],
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", DOT[kind], kind === "active" && "animate-pulse")} />
      {LABELS[status] ?? status}
    </span>
  );
}
