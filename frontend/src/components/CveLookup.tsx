import { ExternalLink, Loader2, Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import api, { errorMessage } from "@/api/client";
import SeverityBadge from "@/components/SeverityBadge";
import type { CveInfo } from "@/types";

const CVE_RE = /^CVE-\d{4}-\d{4,}$/i;

/** Look any CVE up in the NVD, independent of scan results. */
export default function CveLookup() {
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<CveInfo | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const id = query.trim().toUpperCase();
    setInfo(null);
    if (!CVE_RE.test(id)) {
      setError("Enter a CVE identifier such as CVE-2021-41773.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await api.get<CveInfo>(`/vulnerabilities/cve/${id}/`);
      setInfo(res.data);
    } catch (err) {
      setError(errorMessage(err, "NVD lookup failed."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="surface mb-5 p-4">
      <form onSubmit={submit} className="flex flex-wrap items-center gap-3">
        <label htmlFor="cve-lookup" className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          NVD lookup
        </label>
        <input
          id="cve-lookup"
          className="field max-w-xs flex-1 font-mono"
          placeholder="CVE-2021-41773"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="btn-quiet" disabled={busy}>
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
          Look up
        </button>
      </form>

      {error && <p className="notice-error mt-3">{error}</p>}

      {info && (
        <div className="mt-4 rounded-xl bg-slate-50 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm font-bold text-navy-800">{info.cve_id}</span>
            <SeverityBadge severity={info.severity} />
            {info.cvss_score !== null && (
              <span className="font-mono text-xs font-semibold text-navy-700">
                CVSS {info.cvss_score.toFixed(1)} (v{info.cvss_version})
              </span>
            )}
            <a
              href={`https://nvd.nist.gov/vuln/detail/${info.cve_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-navy-700 hover:text-wine-700 hover:underline"
            >
              Open in NVD <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{info.description}</p>
          {info.cvss_vector && <p className="mt-2 break-all font-mono text-[11px] text-slate-400">{info.cvss_vector}</p>}
        </div>
      )}
    </div>
  );
}
