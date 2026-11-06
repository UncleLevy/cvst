import { Link } from "react-router-dom";
import PriorityBadge from "@/components/PriorityBadge";
import SeverityBadge from "@/components/SeverityBadge";
import type { Finding } from "@/types";

interface FindingsTableProps {
  findings: Finding[];
  loading: boolean;
  showScan?: boolean;
  onSelect?: (finding: Finding) => void;
}

export default function FindingsTable({ findings, loading, showScan = false, onSelect }: FindingsTableProps) {
  const cols = showScan ? 7 : 6;
  return (
    <div className="surface overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left">
          <thead className="table-head">
            <tr>
              <th className="px-5 py-3">Priority</th>
              <th className="px-5 py-3">Severity</th>
              <th className="px-5 py-3">Finding</th>
              <th className="px-5 py-3">Service</th>
              <th className="px-5 py-3">CVSS</th>
              {showScan && <th className="px-5 py-3">Scan</th>}
              <th className="px-5 py-3">Found</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={cols} className="px-5 py-12 text-center text-sm text-slate-500">
                  Loading findings…
                </td>
              </tr>
            )}
            {!loading && findings.length === 0 && (
              <tr>
                <td colSpan={cols} className="px-5 py-12 text-center text-sm text-slate-500">
                  No findings match this view.
                </td>
              </tr>
            )}
            {!loading &&
              findings.map((finding) => (
                <tr
                  key={finding.id}
                  className={`align-top transition-colors hover:bg-wine-700/[0.03] ${onSelect ? "cursor-pointer" : ""}`}
                  onClick={onSelect ? () => onSelect(finding) : undefined}
                >
                  <td className="px-5 py-3.5">
                    <PriorityBadge priority={finding.priority} />
                  </td>
                  <td className="px-5 py-3.5">
                    <SeverityBadge severity={finding.severity} />
                  </td>
                  <td className="max-w-md px-5 py-3.5">
                    {onSelect ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(finding);
                        }}
                        className="text-left text-sm font-semibold text-navy-800 hover:text-wine-700 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-wine-700"
                      >
                        {finding.title}
                      </button>
                    ) : (
                      <p className="text-sm font-semibold text-navy-800">{finding.title}</p>
                    )}
                    {finding.description && (
                      <p className="mt-0.5 line-clamp-2 text-xs leading-relaxed text-slate-500">
                        {finding.description}
                      </p>
                    )}
                    {finding.cve_id && (
                      <p className="mt-1 font-mono text-[11px] text-slate-400">{finding.cve_id}</p>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-600">
                    {finding.service || "—"}
                    {finding.port ? `:${finding.port}` : ""}
                  </td>
                  <td className="px-5 py-3.5 font-mono text-xs font-semibold text-navy-700">
                    {typeof finding.cvss_score === "number" ? finding.cvss_score.toFixed(1) : "—"}
                  </td>
                  {showScan && (
                    <td className="px-5 py-3.5">
                      <Link
                        to={`/scans/${finding.scan}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs font-semibold text-navy-700 hover:text-wine-700 hover:underline"
                      >
                        {finding.scan_name || "View scan"}
                      </Link>
                    </td>
                  )}
                  <td className="whitespace-nowrap px-5 py-3.5 text-xs text-slate-500">
                    {new Date(finding.discovered_at).toLocaleDateString(undefined, {
                      day: "2-digit",
                      month: "short",
                    })}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
