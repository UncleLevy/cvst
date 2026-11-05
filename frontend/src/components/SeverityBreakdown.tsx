import { SEVERITY_COLOR, SEVERITY_ORDER } from "@/components/SeverityBadge";
import type { Severity } from "@/types";

export default function SeverityBreakdown({ counts }: { counts: Record<Severity, number> }) {
  const total = SEVERITY_ORDER.reduce((sum, key) => sum + (counts[key] ?? 0), 0);

  return (
    <div className="space-y-3">
      {SEVERITY_ORDER.map((key) => {
        const value = counts[key] ?? 0;
        const pct = total ? Math.round((value / total) * 100) : 0;
        return (
          <div key={key}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-semibold capitalize text-slate-600">{key}</span>
              <span className="font-mono text-[11px] text-slate-500">
                {value} · {pct}%
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, backgroundColor: SEVERITY_COLOR[key] }}
              />
            </div>
          </div>
        );
      })}
      <p className="border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span className="font-semibold text-navy-800">{total}</span> findings across all scans
      </p>
    </div>
  );
}
