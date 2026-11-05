import { ArrowUpRight, RotateCw } from "lucide-react";
import { Link } from "react-router-dom";
import StatusPill from "@/components/StatusPill";
import { statusKind } from "@/lib/scanActions";
import { cn } from "@/lib/utils";
import type { Scan } from "@/types";

function ProgressBar({ value, kind }: { value: number; kind: "completed" | "failed" | "active" }) {
  const color =
    kind === "completed"
      ? "bg-navy-700"
      : kind === "failed"
        ? "bg-wine-700/60"
        : "bg-gradient-to-r from-wine-700 to-wine-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200">
        <div
          className={cn("h-full rounded-full transition-all duration-700", color)}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <span className="font-mono text-[11px] text-slate-500">{value}%</span>
    </div>
  );
}

interface RecentScansTableProps {
  scans: Scan[];
  total: number;
  loading: boolean;
  onRestart?: (scan: Scan) => void;
}

export default function RecentScansTable({ scans, total, loading, onRestart }: RecentScansTableProps) {
  return (
    <div className="surface overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <h2 className="text-[15px] font-semibold text-navy-800">Recent scans</h2>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
          {total} total
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left">
          <thead className="table-head">
            <tr>
              {["Scan", "Target", "Status", "Progress", "Findings", "Created", ""].map((h, i) => (
                <th key={i} className="whitespace-nowrap px-5 py-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={7} className="px-5 py-12 text-center text-sm text-slate-500">
                  Loading scans…
                </td>
              </tr>
            )}
            {!loading && scans.length === 0 && (
              <tr>
                <td colSpan={7} className="px-5 py-12 text-center text-sm text-slate-500">
                  No scans yet. Start one to see findings here.
                </td>
              </tr>
            )}
            {!loading &&
              scans.map((scan) => {
                const kind = statusKind(scan.status);
                return (
                  <tr key={scan.id} className="group transition-colors hover:bg-wine-700/[0.03]">
                    <td className="px-5 py-3.5">
                      <Link
                        to={`/scans/${scan.id}`}
                        className="flex items-center gap-1.5 font-semibold text-navy-800 hover:text-wine-700"
                      >
                        {scan.name}
                        <ArrowUpRight className="h-3.5 w-3.5 opacity-0 transition group-hover:opacity-100" />
                      </Link>
                      <p className="text-[11px] capitalize text-slate-500">{scan.scan_type} scan</p>
                      {kind === "failed" && scan.error_message && (
                        <p className="mt-0.5 max-w-xs truncate text-[11px] text-wine-700" title={scan.error_message}>
                          {scan.error_message}
                        </p>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <p className="max-w-[180px] truncate text-xs font-medium text-slate-700">
                        {scan.target_detail?.name}
                      </p>
                      <p className="max-w-[180px] truncate font-mono text-[11px] text-slate-500">
                        {scan.target_detail?.value}
                      </p>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusPill status={scan.status} />
                    </td>
                    <td className="px-5 py-3.5">
                      <ProgressBar value={scan.progress ?? 0} kind={kind} />
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-xs font-semibold text-navy-700">
                        {scan.vulnerability_count ?? 0}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 text-xs text-slate-500">
                      {new Date(scan.created_at).toLocaleDateString(undefined, { day: "2-digit", month: "short" })}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {(kind === "completed" || kind === "failed") && onRestart ? (
                        <button
                          onClick={() => onRestart(scan)}
                          title="Restart scan"
                          className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-semibold text-slate-500 transition hover:bg-wine-700 hover:text-white"
                        >
                          <RotateCw className="h-3.5 w-3.5" />
                          Rerun
                        </button>
                      ) : (
                        <span className="text-[11px] font-medium text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
