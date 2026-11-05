import { useCallback, useEffect, useState } from "react";
import api, { errorMessage } from "../api/client";
import ScanForm from "../components/ScanForm";
import type { Scan } from "../types";

// Palette
const BURGUNDY = "#800020";
const NAVY = "#12264a";
const SLATE = "#94a3b8";

type Kind = "completed" | "failed" | "active";

const kindOf = (status: string): Kind =>
  status === "completed" ? "completed" : status === "failed" ? "failed" : "active";

const PILL: Record<Kind, string> = {
  completed: "bg-[#12264a]/10 text-[#12264a] ring-[#12264a]/30",
  failed: "bg-[#800020]/10 text-[#800020] ring-[#800020]/30",
  active: "bg-slate-200 text-slate-700 ring-slate-300",
};

const DOT: Record<Kind, string> = {
  completed: "bg-[#12264a]",
  failed: "bg-[#800020]",
  active: "bg-slate-400 animate-pulse",
};

function StatCard({
  label,
  value,
  accent,
  icon,
}: {
  label: string;
  value: number;
  accent: string;
  icon: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="absolute inset-y-0 left-0 w-1.5" style={{ backgroundColor: accent }} />
      <div className="flex items-center justify-between pl-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-1 text-3xl font-bold text-[#12264a]">{value}</p>
        </div>
        <div
          className="flex h-11 w-11 items-center justify-center rounded-full text-lg text-white"
          style={{ backgroundColor: accent }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function Donut({ completed, active, failed }: { completed: number; active: number; failed: number }) {
  const total = completed + active + failed;
  const R = 42;
  const C = 2 * Math.PI * R;
  const segments = [
    { value: completed, color: NAVY },
    { value: active, color: SLATE },
    { value: failed, color: BURGUNDY },
  ];
  let offset = 0;

  return (
    <svg viewBox="0 0 100 100" className="h-36 w-36">
      <circle cx="50" cy="50" r={R} fill="none" stroke="#e2e8f0" strokeWidth="12" />
      {total > 0 &&
        segments.map((seg, i) => {
          const len = (seg.value / total) * C;
          const el = (
            <circle
              key={i}
              cx="50"
              cy="50"
              r={R}
              fill="none"
              stroke={seg.color}
              strokeWidth="12"
              strokeDasharray={`${len} ${C - len}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 50 50)"
            />
          );
          offset += len;
          return el;
        })}
      <text x="50" y="48" textAnchor="middle" className="fill-[#12264a]" fontSize="16" fontWeight="700">
        {total}
      </text>
      <text x="50" y="61" textAnchor="middle" className="fill-slate-500" fontSize="7">
        SCANS
      </text>
    </svg>
  );
}

export default function Dashboard() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const fetchScans = useCallback(async () => {
    try {
      const res = await api.get("/scans/");
      setScans(res.data.results || res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(errorMessage(err, "Could not load scans."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScans();
    const interval = setInterval(fetchScans, 4000); // poll every 4s
    return () => clearInterval(interval);
  }, [fetchScans]);

  const restart = async (id: number) => {
    try {
      await api.post(`/scans/${id}/restart/`);
      fetchScans();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const completed = scans.filter((s) => kindOf(s.status) === "completed").length;
  const failed = scans.filter((s) => kindOf(s.status) === "failed").length;
  const active = scans.length - completed - failed;

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-300 border-t-[#800020]" />
          <p className="text-sm font-medium text-[#12264a]">Loading scans...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-100">
      {/* Header band */}
      <header className="bg-gradient-to-r from-[#0b1730] via-[#12264a] to-[#1b3a6b] pb-24 pt-8 shadow-lg">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#800020] text-lg font-black text-white shadow-md">
              C
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">CVST Dashboard</h1>
              <p className="text-sm text-slate-300">Vulnerability scan overview</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-200 ring-1 ring-white/20">
              <span className="h-2 w-2 animate-pulse rounded-full bg-[#c0304f]" />
              Live · refreshing every 4s
            </div>
            <button onClick={() => setShowForm((v) => !v)} className="btn-primary">
              + New scan
            </button>
          </div>
        </div>
        <div className="mx-auto mt-6 h-0.5 max-w-6xl bg-gradient-to-r from-[#800020] via-[#800020]/40 to-transparent" />
      </header>

      <main className="mx-auto -mt-16 max-w-6xl px-6 pb-12">
        {error && (
          <div className="mb-4 rounded-lg border border-[#800020]/30 bg-[#800020]/10 px-4 py-3 text-sm font-medium text-[#800020]">
            {error}
          </div>
        )}

        {showForm && (
          <ScanForm
            onCancel={() => setShowForm(false)}
            onCreated={() => {
              setShowForm(false);
              fetchScans();
            }}
          />
        )}

        {/* Stats + chart */}
        <div className="mb-6 grid gap-4 lg:grid-cols-3">
          <div className="grid grid-cols-2 gap-4 lg:col-span-2">
            <StatCard label="Total scans" value={scans.length} accent={NAVY} icon="Σ" />
            <StatCard label="Active" value={active} accent="#64748b" icon="↻" />
            <StatCard label="Completed" value={completed} accent="#1b3a6b" icon="✓" />
            <StatCard label="Failed" value={failed} accent={BURGUNDY} icon="!" />
          </div>

          <div className="flex items-center justify-between rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <Donut completed={completed} active={active} failed={failed} />
            <ul className="space-y-2 text-sm text-slate-600">
              <li className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: NAVY }} /> Completed
              </li>
              <li className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: SLATE }} /> Active
              </li>
              <li className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: BURGUNDY }} /> Failed
              </li>
            </ul>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-semibold text-[#12264a]">Recent scans</h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {scans.length} total
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-[#12264a] text-slate-100">
                <tr>
                  {["Name", "Target", "Status", "Progress", "Findings", "Created", ""].map((h, i) => (
                    <th
                      key={i}
                      className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scans.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-5 py-12 text-center text-sm text-slate-500">
                      No scans yet. Click “New scan” to start one.
                    </td>
                  </tr>
                )}
                {scans.map((scan) => {
                  const kind = kindOf(scan.status);
                  const barColor =
                    kind === "completed"
                      ? "bg-[#12264a]"
                      : kind === "failed"
                      ? "bg-slate-400"
                      : "bg-gradient-to-r from-[#800020] to-[#b3304f]";
                  return (
                    <tr
                      key={scan.id}
                      className="transition-colors odd:bg-white even:bg-slate-50/60 hover:bg-[#800020]/5"
                    >
                      <td className="px-5 py-4">
                        <div className="font-semibold text-[#12264a]">{scan.name}</div>
                        {kind === "failed" && scan.error_message && (
                          <div className="mt-0.5 max-w-xs truncate text-xs text-[#800020]" title={scan.error_message}>
                            {scan.error_message}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4 text-sm text-slate-700">
                        <div className="font-medium">{scan.target_detail?.name}</div>
                        <div className="font-mono text-xs text-slate-500">{scan.target_detail?.value}</div>
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${PILL[kind]}`}
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${DOT[kind]}`} />
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-2.5 w-36 overflow-hidden rounded-full bg-slate-200">
                            <div
                              className={`h-2.5 rounded-full transition-all duration-500 ${barColor}`}
                              style={{ width: `${Math.min(100, Math.max(0, scan.progress))}%` }}
                            />
                          </div>
                          <span className="w-10 text-xs font-semibold text-slate-600">{scan.progress}%</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-sm font-semibold text-[#12264a]">
                        {scan.vulnerability_count ?? 0}
                      </td>
                      <td className="px-5 py-4 text-sm text-slate-500">
                        {new Date(scan.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-4 text-right">
                        {(kind === "completed" || kind === "failed") && (
                          <button
                            onClick={() => restart(scan.id)}
                            className="rounded-md px-2.5 py-1 text-xs font-semibold text-[#800020] ring-1 ring-[#800020]/40 transition hover:bg-[#800020] hover:text-white"
                          >
                            Restart
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
