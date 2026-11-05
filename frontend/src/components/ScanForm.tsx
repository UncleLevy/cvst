import { Crosshair, Loader2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "@/api/client";
import { cn } from "@/lib/utils";
import { listOf, type Paginated, type ScanType, type Target } from "@/types";

const SCAN_TYPES: { value: ScanType; label: string; hint: string }[] = [
  { value: "network", label: "Network discovery", hint: "Open ports, exposed services" },
  { value: "web", label: "Web application", hint: "Headers, TLS, injection checks" },
  { value: "full", label: "Full assessment", hint: "Both modules in one pass" },
];

interface ScanFormProps {
  onCreated: () => void;
  onCancel?: () => void;
}

export default function ScanForm({ onCreated, onCancel }: ScanFormProps) {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loadingTargets, setLoadingTargets] = useState(true);
  const [name, setName] = useState("");
  const [targetId, setTargetId] = useState("");
  const [scanType, setScanType] = useState<ScanType>("network");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Paginated<Target>>("/targets/", { params: { page_size: 200 } })
      .then((res) => {
        const items = listOf(res.data);
        setTargets(items);
        if (items.length) setTargetId(String(items[0].id));
      })
      .catch((err) => setError(errorMessage(err, "Could not load targets.")))
      .finally(() => setLoadingTargets(false));
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const target = targets.find((t) => String(t.id) === targetId);
    if (!target) {
      setError("Add a target before starting a scan.");
      return;
    }
    setBusy(true);
    try {
      const label = SCAN_TYPES.find((t) => t.value === scanType)?.label ?? scanType;
      await api.post("/scans/", {
        name: name.trim() || `${target.name} · ${label}`,
        target: target.id,
        scan_type: scanType,
      });
      onCreated();
    } catch (err) {
      setError(errorMessage(err, "Could not start the scan."));
    } finally {
      setBusy(false);
    }
  };

  const noTargets = !loadingTargets && targets.length === 0;

  return (
    <form onSubmit={submit} className="space-y-4">
      {error && <p className="rounded-lg bg-wine-100 px-3 py-2 text-sm font-medium text-wine-800">{error}</p>}

      {noTargets ? (
        <div className="rounded-xl border border-dashed border-slate-300 px-4 py-6 text-center">
          <Crosshair className="mx-auto h-5 w-5 text-slate-400" />
          <p className="mt-2 text-sm text-slate-600">No targets yet.</p>
          <Link to="/targets" className="mt-1 inline-block text-sm font-semibold text-wine-700 hover:underline">
            Add your first target
          </Link>
        </div>
      ) : (
        <>
          <div>
            <label className="label-xs" htmlFor="scan-name">
              Scan name
            </label>
            <input
              id="scan-name"
              className="field"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Weekly perimeter sweep"
            />
          </div>
          <div>
            <label className="label-xs" htmlFor="scan-target">
              Target
            </label>
            <select
              id="scan-target"
              className="field"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              disabled={loadingTargets}
            >
              {targets.map((target) => (
                <option key={target.id} value={target.id}>
                  {target.name} — {target.value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <span className="label-xs">Module</span>
            <div className="grid gap-2 sm:grid-cols-3">
              {SCAN_TYPES.map((type) => {
                const selected = scanType === type.value;
                return (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setScanType(type.value)}
                    className={cn(
                      "rounded-xl border px-3 py-2.5 text-left transition",
                      selected
                        ? "border-wine-700 bg-wine-700/[0.05] ring-1 ring-wine-700/20"
                        : "border-slate-200 hover:border-slate-300",
                    )}
                  >
                    <span className="block text-[13px] font-semibold text-navy-800">{type.label}</span>
                    <span className="mt-0.5 block text-[11px] leading-snug text-slate-500">{type.hint}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}

      <p className="text-[11px] leading-relaxed text-slate-500">
        Unless real scanning is enabled on the server, findings are produced in demo mode and labelled{" "}
        <span className="font-semibold">[SIMULATED]</span>. Only scan systems you own or have written permission to
        test.
      </p>

      <div className="flex items-center justify-end gap-2 border-t border-slate-100 pt-4">
        {onCancel && (
          <button type="button" className="btn-quiet" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={busy || targets.length === 0}>
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? "Queueing…" : "Start scan"}
        </button>
      </div>
    </form>
  );
}
