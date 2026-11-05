import { ArrowLeft, Clock3, Loader2, RotateCw, Server, type LucideIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorMessage } from "@/api/client";
import FindingDetailDialog from "@/components/FindingDetailDialog";
import FindingsTable from "@/components/FindingsTable";
import { EMPTY_SEVERITY } from "@/components/SeverityBadge";
import SeverityTiles from "@/components/SeverityTiles";
import StatusPill from "@/components/StatusPill";
import { isNotFound, restartScan } from "@/lib/scanActions";
import { listOf, type Finding, type Paginated, type Scan, type Severity } from "@/types";

const MODULE_LABEL: Record<string, string> = {
  network: "Network discovery",
  web: "Web application",
  full: "Full assessment",
};

function Stat({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="mt-0.5 h-4 w-4 text-slate-400" />
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">{label}</p>
        <p className="text-sm font-medium text-navy-800">{value}</p>
      </div>
    </div>
  );
}

export default function ScanDetail() {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [counts, setCounts] = useState<Record<Severity, number>>(EMPTY_SEVERITY);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState(false);
  const [selected, setSelected] = useState<Finding | null>(null);

  const load = useCallback(async () => {
    try {
      const scanRes = await api.get<Scan>(`/scans/${id}/`);
      setScan(scanRes.data);
      const [findingsRes, summaryRes] = await Promise.all([
        api.get<Paginated<Finding>>("/vulnerabilities/", { params: { scan: id, page_size: 200 } }),
        api.get<{ by_severity: Record<Severity, number> }>(`/scans/${id}/summary/`),
      ]);
      setFindings(listOf(findingsRes.data));
      setCounts({ ...EMPTY_SEVERITY, ...summaryRes.data.by_severity });
      setNotFound(false);
      setError(null);
    } catch (err) {
      if (isNotFound(err)) setNotFound(true);
      else setError(errorMessage(err, "Could not load this scan."));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll while the scan is still running.
  const active = scan !== null && scan.status !== "completed" && scan.status !== "failed";
  useEffect(() => {
    if (!active) return undefined;
    const timer = setInterval(load, 2500);
    return () => clearInterval(timer);
  }, [active, load]);

  const rerun = async () => {
    if (!scan) return;
    setRerunning(true);
    try {
      await restartScan(scan.id);
      await load();
    } catch (err) {
      setError(errorMessage(err, "Could not restart the scan."));
    } finally {
      setRerunning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading scan…
      </div>
    );
  }

  if (notFound || !scan) {
    return (
      <div className="surface mx-auto mt-10 max-w-md p-8 text-center">
        <p className="text-lg font-semibold text-navy-800">{notFound ? "Scan not found" : "Could not load scan"}</p>
        <p className="mt-1 text-sm text-slate-500">{notFound ? "It may have been removed." : error}</p>
        <Link to="/" className="btn-primary mt-5">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const duration = scan.started_at
    ? Math.max(
        1,
        Math.round(
          ((scan.finished_at ? new Date(scan.finished_at) : new Date()).getTime() -
            new Date(scan.started_at).getTime()) /
            1000,
        ),
      )
    : null;

  return (
    <div>
      <Link
        to="/"
        className="mb-4 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 transition hover:text-wine-700"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Dashboard
      </Link>

      {error && <p className="notice-error mb-4">{error}</p>}

      <div className="surface p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-wine-700">Scan report</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-navy-800">{scan.name}</h1>
            <p className="mt-1 font-mono text-xs text-slate-500">
              {scan.target_detail?.name} · {scan.target_detail?.value}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusPill status={scan.status} />
            {(scan.status === "completed" || scan.status === "failed") && (
              <button className="btn-quiet" onClick={rerun} disabled={rerunning}>
                {rerunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RotateCw className="h-3.5 w-3.5" />}
                Rerun
              </button>
            )}
          </div>
        </div>

        <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-navy-700 to-wine-700 transition-all duration-700"
            style={{ width: `${scan.progress ?? 0}%` }}
          />
        </div>

        <div className="mt-5 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-3">
          <Stat icon={Server} label="Module" value={MODULE_LABEL[scan.scan_type] ?? scan.scan_type} />
          <Stat
            icon={Clock3}
            label="Started"
            value={
              scan.started_at
                ? new Date(scan.started_at).toLocaleString(undefined, {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "—"
            }
          />
          <Stat icon={Clock3} label="Duration" value={duration ? `${duration}s` : "—"} />
        </div>

        {scan.error_message && (
          <p className="mt-4 rounded-lg bg-wine-100 px-3 py-2 text-sm font-medium text-wine-800">
            {scan.error_message}
          </p>
        )}
      </div>

      <div className="mt-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[15px] font-semibold text-navy-800">Findings</h2>
          <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400">
            {findings.length} recorded
          </span>
        </div>
        <SeverityTiles counts={counts} />
      </div>

      <div className="mt-4">
        <FindingsTable findings={findings} loading={false} onSelect={setSelected} />
        <FindingDetailDialog finding={selected} onClose={() => setSelected(null)} />
      </div>
    </div>
  );
}
