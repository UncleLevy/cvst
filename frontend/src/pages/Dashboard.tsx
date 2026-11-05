import { Activity, CheckCircle2, Layers, Plus, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "@/api/client";
import PageHeader from "@/components/PageHeader";
import RecentScansTable from "@/components/RecentScansTable";
import ScanDonut from "@/components/ScanDonut";
import ScanForm from "@/components/ScanForm";
import { EMPTY_SEVERITY } from "@/components/SeverityBadge";
import SeverityBreakdown from "@/components/SeverityBreakdown";
import StatCard from "@/components/StatCard";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { restartScan } from "@/lib/scanActions";
import { listOf, type Paginated, type Scan, type ScanStats, type Severity, type SeverityStats } from "@/types";

const EMPTY_STATS: ScanStats = { total: 0, active: 0, completed: 0, failed: 0 };

export default function Dashboard() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [stats, setStats] = useState<ScanStats>(EMPTY_STATS);
  const [severity, setSeverity] = useState<Record<Severity, number>>(EMPTY_SEVERITY);
  const [findingsTotal, setFindingsTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const [scanPage, scanStats, vulnStats] = await Promise.all([
        api.get<Paginated<Scan>>("/scans/", { params: { page_size: 20 } }),
        api.get<ScanStats>("/scans/stats/"),
        api.get<SeverityStats>("/vulnerabilities/stats/"),
      ]);
      setScans(listOf(scanPage.data));
      setStats(scanStats.data);
      setSeverity({ ...EMPTY_SEVERITY, ...vulnStats.data.by_severity });
      setFindingsTotal(vulnStats.data.total);
      setError(null);
    } catch (err) {
      setError(errorMessage(err, "Could not load scan activity."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 4000); // poll every 4s
    return () => clearInterval(timer);
  }, [load]);

  const handleRestart = async (scan: Scan) => {
    try {
      await restartScan(scan.id);
      await load();
    } catch (err) {
      setError(errorMessage(err, "Could not restart the scan."));
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Security overview"
        title="Scan operations"
        subtitle="Track assessments across your authorised targets and triage what they surface."
        actions={
          <>
            <span className="hidden items-center gap-2 rounded-full bg-white px-3 py-1.5 text-[11px] font-semibold text-slate-500 ring-1 ring-slate-200 sm:inline-flex">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-wine-700" />
              Live
            </span>
            <button className="btn-primary" onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" /> New scan
            </button>
          </>
        }
      />

      {error && <p className="notice-error mb-4">{error}</p>}

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatCard label="Total scans" value={stats.total} accent="#12264a" icon={Layers} />
        <StatCard label="Active" value={stats.active} accent="#64748b" icon={Activity} hint="Running or queued" />
        <StatCard
          label="Completed"
          value={stats.completed}
          accent="#1b3a6b"
          icon={CheckCircle2}
          hint={`${stats.failed} failed`}
        />
        <StatCard label="Findings" value={findingsTotal} accent="#800020" icon={TriangleAlert} hint="Across all scans" />
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <div className="surface p-5">
          <h2 className="mb-4 text-[15px] font-semibold text-navy-800">Scan status</h2>
          <ScanDonut completed={stats.completed} active={stats.active} failed={stats.failed} />
        </div>
        <div className="surface p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-[15px] font-semibold text-navy-800">Severity mix</h2>
            <Link
              to="/findings"
              className="text-[11px] font-semibold uppercase tracking-[0.12em] text-wine-700 hover:underline"
            >
              Review findings
            </Link>
          </div>
          <SeverityBreakdown counts={severity} />
        </div>
      </div>

      <div className="mt-5">
        <RecentScansTable scans={scans} total={stats.total} loading={loading} onRestart={handleRestart} />
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New scan</DialogTitle>
            <DialogDescription>Pick an authorised target and the module to run against it.</DialogDescription>
          </DialogHeader>
          <ScanForm
            onCancel={() => setDialogOpen(false)}
            onCreated={() => {
              setDialogOpen(false);
              load();
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
