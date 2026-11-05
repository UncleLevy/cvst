const R = 42;
const C = 2 * Math.PI * R;

interface ScanDonutProps {
  completed?: number;
  active?: number;
  failed?: number;
}

export default function ScanDonut({ completed = 0, active = 0, failed = 0 }: ScanDonutProps) {
  const total = completed + active + failed;
  const segments = [
    { value: completed, color: "#12264a", label: "Completed" },
    { value: active, color: "#94a3b8", label: "Active" },
    { value: failed, color: "#800020", label: "Failed" },
  ];
  let offset = 0;

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:gap-6">
      <svg viewBox="0 0 100 100" className="h-32 w-32 shrink-0" role="img" aria-label={`${total} scans`}>
        <circle cx="50" cy="50" r={R} fill="none" stroke="#e8ebf2" strokeWidth="11" />
        {total > 0 &&
          segments.map((seg) => {
            const len = (seg.value / total) * C;
            const el = (
              <circle
                key={seg.label}
                cx="50"
                cy="50"
                r={R}
                fill="none"
                stroke={seg.color}
                strokeWidth="11"
                strokeLinecap="butt"
                strokeDasharray={`${len} ${C - len}`}
                strokeDashoffset={-offset}
                transform="rotate(-90 50 50)"
              />
            );
            offset += len;
            return el;
          })}
        <text x="50" y="49" textAnchor="middle" fontSize="19" fontWeight="700" fill="#12264a" fontFamily="Inter, sans-serif">
          {total}
        </text>
        <text x="50" y="62" textAnchor="middle" fontSize="6.5" letterSpacing="1.4" fill="#94a3b8" fontFamily="Inter, sans-serif">
          SCANS
        </text>
      </svg>
      <ul className="w-full space-y-2.5">
        {segments.map((seg) => (
          <li key={seg.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: seg.color }} />
              {seg.label}
            </span>
            <span className="font-mono text-xs font-semibold text-navy-700">{seg.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
