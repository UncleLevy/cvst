import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api/client";
import type { ScanType, Target } from "../types";

const SCAN_TYPES: { value: ScanType; label: string }[] = [
  { value: "network", label: "Network discovery" },
  { value: "web", label: "Web application" },
  { value: "full", label: "Full assessment" },
];

export default function ScanForm({ onCreated, onCancel }: { onCreated: () => void; onCancel: () => void }) {
  const [targets, setTargets] = useState<Target[] | null>(null);
  const [name, setName] = useState("");
  const [targetId, setTargetId] = useState("");
  const [scanType, setScanType] = useState<ScanType>("network");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/targets/")
      .then((res) => {
        const list: Target[] = res.data.results || res.data;
        setTargets(list);
        if (list.length) setTargetId(String(list[0].id));
      })
      .catch((err) => {
        setTargets([]);
        setError(errorMessage(err));
      });
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/scans/", { name, target: Number(targetId), scan_type: scanType });
      onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const input =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-[#800020] focus:outline-none focus:ring-1 focus:ring-[#800020]";
  const label = "mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500";

  return (
    <form onSubmit={submit} className="mb-6 rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[#12264a]">New scan</h2>
        <button type="button" onClick={onCancel} className="text-sm font-medium text-slate-500 hover:text-[#800020]">
          Cancel
        </button>
      </div>

      {targets && targets.length === 0 ? (
        <p className="rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-600">
          You don't have any targets yet.{" "}
          <Link to="/targets" className="font-semibold">
            Add a target
          </Link>{" "}
          first, then come back to start a scan.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className={label} htmlFor="scan-name">
              Scan name
            </label>
            <input id="scan-name" className={input} value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className={label} htmlFor="scan-target">
              Target
            </label>
            <select
              id="scan-target"
              className={input}
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              required
            >
              {(targets ?? []).map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.value})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={label} htmlFor="scan-type">
              Scan type
            </label>
            <select
              id="scan-type"
              className={input}
              value={scanType}
              onChange={(e) => setScanType(e.target.value as ScanType)}
            >
              {SCAN_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-lg border border-[#800020]/30 bg-[#800020]/10 px-3 py-2 text-sm font-medium text-[#800020]">
          {error}
        </p>
      )}

      {targets && targets.length > 0 && (
        <div className="mt-5">
          <button type="submit" disabled={busy || !name || !targetId} className="btn-primary disabled:opacity-50">
            {busy ? "Starting…" : "Start scan"}
          </button>
        </div>
      )}
    </form>
  );
}
