import { cn } from "@/lib/utils";
import type { Priority } from "@/types";

export const PRIORITY_LABEL: Record<Priority, string> = {
  P1: "Fix immediately",
  P2: "Fix urgently",
  P3: "Plan a fix",
  P4: "Monitor / backlog",
};

const STYLES: Record<Priority, string> = {
  P1: "bg-wine-800 text-white",
  P2: "bg-wine-100 text-wine-800",
  P3: "bg-navy-700/10 text-navy-700",
  P4: "bg-slate-100 text-slate-500",
};

export default function PriorityBadge({ priority, className }: { priority: Priority; className?: string }) {
  return (
    <span
      title={PRIORITY_LABEL[priority]}
      className={cn(
        "inline-flex items-center rounded-md px-1.5 py-0.5 font-mono text-[11px] font-bold",
        STYLES[priority] ?? STYLES.P4,
        className,
      )}
    >
      {priority}
    </span>
  );
}
