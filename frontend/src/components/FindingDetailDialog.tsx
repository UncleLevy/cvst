import { ExternalLink, Wrench } from "lucide-react";
import { Link } from "react-router-dom";
import SeverityBadge from "@/components/SeverityBadge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Finding } from "@/types";

const SOURCE_LABEL: Record<string, string> = {
  nmap: "Nmap network scan",
  web: "Web application checks",
  simulated: "Simulated (demo mode)",
};

const CVE_RE = /^CVE-\d{4}-\d{4,}$/i;

/** Only ever render http(s) links from scanner data. */
function safeUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">{label}</p>
      <div className="mt-0.5 text-sm font-medium text-navy-800">{children}</div>
    </div>
  );
}

interface Props {
  finding: Finding | null;
  onClose: () => void;
}

export default function FindingDetailDialog({ finding, onClose }: Props) {
  const references = (finding?.references ?? []).map(safeUrl).filter((u): u is string => u !== null);
  const cve = finding && CVE_RE.test(finding.cve_id) ? finding.cve_id.toUpperCase() : null;

  return (
    <Dialog open={finding !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl">
        {finding && (
          <>
            <DialogHeader>
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={finding.severity} />
                {cve && (
                  <a
                    href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-mono text-[11px] font-semibold text-navy-700 hover:text-wine-700 hover:underline"
                  >
                    {cve} <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
              <DialogTitle className="pt-1 text-xl">{finding.title}</DialogTitle>
              <DialogDescription>
                {finding.target_value}
                {finding.port ? ` · port ${finding.port}` : ""}
              </DialogDescription>
            </DialogHeader>

            <div className="grid grid-cols-2 gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-4">
              <Field label="CVSS">
                {typeof finding.cvss_score === "number" ? (
                  <span className="font-mono">{finding.cvss_score.toFixed(1)}</span>
                ) : (
                  <span className="text-slate-400" title="Exposure findings are rated by severity only">
                    Not scored
                  </span>
                )}
              </Field>
              <Field label="Service">
                <span className="font-mono">{finding.service || "—"}</span>
              </Field>
              <Field label="Detected by">{SOURCE_LABEL[finding.source] ?? (finding.source || "—")}</Field>
              <Field label="Found">
                {new Date(finding.discovered_at).toLocaleString(undefined, {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </Field>
            </div>

            <section className="mt-5">
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">Description</h3>
              <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-slate-700">
                {finding.description || "No description recorded."}
              </p>
            </section>

            {finding.evidence && (
              <section className="mt-5">
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">Evidence</h3>
                <pre className="mt-1.5 overflow-x-auto whitespace-pre-wrap break-words rounded-xl bg-navy-900 p-3.5 font-mono text-xs leading-relaxed text-slate-200">
                  {finding.evidence}
                </pre>
              </section>
            )}

            {finding.recommendation && (
              <section className="mt-5 rounded-xl border border-wine-700/15 bg-wine-700/[0.04] p-4">
                <h3 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-wine-700">
                  <Wrench className="h-3.5 w-3.5" /> Recommended fix
                </h3>
                <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-navy-800">
                  {finding.recommendation}
                </p>
              </section>
            )}

            {references.length > 0 && (
              <section className="mt-5">
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">References</h3>
                <ul className="mt-1.5 space-y-1">
                  {references.map((href) => (
                    <li key={href}>
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 break-all text-xs font-medium text-navy-700 hover:text-wine-700 hover:underline"
                      >
                        {href} <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
              <Link
                to={`/scans/${finding.scan}`}
                onClick={onClose}
                className="text-xs font-semibold text-navy-700 hover:text-wine-700 hover:underline"
              >
                View scan: {finding.scan_name || `#${finding.scan}`}
              </Link>
              <button className="btn-quiet" onClick={onClose}>
                Close
              </button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
