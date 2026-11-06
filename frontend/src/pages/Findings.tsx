import { Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import api, { errorMessage } from "@/api/client";
import CveLookup from "@/components/CveLookup";
import FindingDetailDialog from "@/components/FindingDetailDialog";
import FindingsTable from "@/components/FindingsTable";
import PageHeader from "@/components/PageHeader";
import { SEVERITY_ORDER } from "@/components/SeverityBadge";
import { cn } from "@/lib/utils";
import { listOf, type Finding, type Paginated, type SeverityStats } from "@/types";

type Filter = "all" | (typeof SEVERITY_ORDER)[number];

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [severity, setSeverity] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Finding | null>(null);

  const loadCounts = useCallback(async () => {
    try {
      const res = await api.get<SeverityStats>("/vulnerabilities/stats/");
      setCounts({ all: res.data.total, ...res.data.by_severity });
    } catch (err) {
      setError(errorMessage(err, "Could not load finding counts."));
    }
  }, []);

  const load = useCallback(async () => {
    try {
      const params: Record<string, string | number> = { page_size: 200 };
      if (severity !== "all") params.severity = severity;
      if (search.trim()) params.search = search.trim();
      const res = await api.get<Paginated<Finding>>("/vulnerabilities/", { params });
      setFindings(listOf(res.data));
      setError(null);
    } catch (err) {
      setError(errorMessage(err, "Could not load findings."));
    } finally {
      setLoading(false);
    }
  }, [severity, search]);

  useEffect(() => {
    loadCounts();
  }, [loadCounts]);

  // Debounce typing in the search box.
  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [load]);

  const filters: Filter[] = ["all", ...SEVERITY_ORDER];

  return (
    <div>
      <PageHeader
        eyebrow="Triage"
        title="Findings"
        subtitle="Everything your scans have surfaced, ranked by risk. P1 findings come first."
      />
      <CveLookup />

      {error && <p className="notice-error mb-4">{error}</p>}

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap gap-1.5">
          {filters.map((key) => (
            <button
              key={key}
              onClick={() => setSeverity(key)}
              className={cn(
                "rounded-lg px-3 py-1.5 text-[12px] font-semibold capitalize transition",
                severity === key
                  ? "bg-navy-800 text-white shadow-sm"
                  : "bg-white text-slate-600 ring-1 ring-slate-200 hover:text-navy-800",
              )}
            >
              {key}
              <span className={cn("ml-1.5 font-mono text-[11px]", severity === key ? "text-slate-300" : "text-slate-400")}>
                {counts[key] ?? 0}
              </span>
            </button>
          ))}
        </div>
        <div className="relative ml-auto w-full sm:w-64">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            className="field pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search findings"
            aria-label="Search findings"
          />
        </div>
      </div>

      <FindingsTable findings={findings} loading={loading} showScan onSelect={setSelected} />
      <FindingDetailDialog
        finding={selected}
        onClose={() => setSelected(null)}
        onUpdate={(updated) => {
          setSelected(updated);
          setFindings((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
          loadCounts();
        }}
      />
    </div>
  );
}
