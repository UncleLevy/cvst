import { SEVERITY_COLOR, SEVERITY_ORDER } from "@/components/SeverityBadge";
import type { Severity } from "@/types";

export default function SeverityTiles({ counts }: { counts: Record<Severity, number> }) {
  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-5">
      {SEVERITY_ORDER.map((key) => (
        <div
          key={key}
          className="rounded-xl bg-white p-3 ring-1 ring-navy-900/[0.07]"
          style={{ borderTop: `2px solid ${SEVERITY_COLOR[key]}` }}
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{key}</p>
          <p className="mt-1 font-mono text-xl font-semibold text-navy-800">{counts[key] ?? 0}</p>
        </div>
      ))}
    </div>
  );
}
