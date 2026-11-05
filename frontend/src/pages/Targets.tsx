import { useCallback, useEffect, useState, type FormEvent } from "react";
import api, { errorMessage } from "../api/client";
import type { Target, TargetType } from "../types";

const TYPES: { value: TargetType; label: string; placeholder: string }[] = [
  { value: "ip", label: "IP address", placeholder: "192.168.1.10" },
  { value: "hostname", label: "Hostname", placeholder: "server.example.com" },
  { value: "url", label: "URL", placeholder: "https://example.com" },
  { value: "network", label: "Network range", placeholder: "192.168.1.0/24" },
];

export default function Targets() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [type, setType] = useState<TargetType>("ip");
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await api.get("/targets/");
      setTargets(res.data.results || res.data);
    } catch (err) {
      setError(errorMessage(err, "Could not load targets."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/targets/", { name, target_type: type, value, description });
      setName("");
      setValue("");
      setDescription("");
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (t: Target) => {
    if (!window.confirm(`Remove target "${t.name}"? Existing scan history is kept.`)) return;
    try {
      await api.delete(`/targets/${t.id}/`);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const input =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-[#800020] focus:outline-none focus:ring-1 focus:ring-[#800020]";
  const label = "mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500";
  const placeholder = TYPES.find((t) => t.value === type)?.placeholder;

  return (
    <div>
      <header className="bg-gradient-to-r from-[#0b1730] via-[#12264a] to-[#1b3a6b] pb-20 pt-8 shadow-lg">
        <div className="mx-auto max-w-6xl px-6">
          <h1 className="text-2xl font-bold tracking-tight !text-white">Targets</h1>
          <p className="text-sm text-slate-300">Hosts, addresses and sites you are authorised to scan</p>
          <div className="mt-6 h-0.5 bg-gradient-to-r from-[#800020] via-[#800020]/40 to-transparent" />
        </div>
      </header>

      <main className="mx-auto -mt-12 max-w-6xl space-y-6 px-6 pb-12">
        {error && (
          <div className="rounded-lg border border-[#800020]/30 bg-[#800020]/10 px-4 py-3 text-sm font-medium text-[#800020]">
            {error}
          </div>
        )}

        <form onSubmit={create} className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h2 className="mb-4 text-lg font-semibold text-[#12264a]">Add target</h2>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className={label} htmlFor="t-name">
                Name
              </label>
              <input id="t-name" className={input} value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label className={label} htmlFor="t-type">
                Type
              </label>
              <select
                id="t-type"
                className={input}
                value={type}
                onChange={(e) => setType(e.target.value as TargetType)}
              >
                {TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className={label} htmlFor="t-value">
                Value
              </label>
              <input
                id="t-value"
                className={`${input} font-mono`}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={placeholder}
                required
              />
            </div>
            <div className="md:col-span-4">
              <label className={label} htmlFor="t-desc">
                Description (optional)
              </label>
              <input id="t-desc" className={input} value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Only add systems you own or have written permission to test.
          </p>
          <div className="mt-4">
            <button type="submit" disabled={busy} className="btn-primary disabled:opacity-60">
              {busy ? "Adding…" : "Add target"}
            </button>
          </div>
        </form>

        <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-semibold text-[#12264a]">Your targets</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-[#12264a] text-slate-100">
                <tr>
                  {["Name", "Type", "Value", "Added", ""].map((h, i) => (
                    <th key={i} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading && (
                  <tr>
                    <td colSpan={5} className="px-5 py-10 text-center text-sm text-slate-500">
                      Loading…
                    </td>
                  </tr>
                )}
                {!loading && targets.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-5 py-10 text-center text-sm text-slate-500">
                      No targets yet. Add one above.
                    </td>
                  </tr>
                )}
                {targets.map((t) => (
                  <tr key={t.id} className="odd:bg-white even:bg-slate-50/60 hover:bg-[#800020]/5">
                    <td className="px-5 py-4">
                      <div className="font-semibold text-[#12264a]">{t.name}</div>
                      {t.description && <div className="text-xs text-slate-500">{t.description}</div>}
                    </td>
                    <td className="px-5 py-4">
                      <span className="rounded-full bg-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700">
                        {TYPES.find((x) => x.value === t.target_type)?.label ?? t.target_type}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-mono text-sm text-slate-700">{t.value}</td>
                    <td className="px-5 py-4 text-sm text-slate-500">{new Date(t.created_at).toLocaleDateString()}</td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => remove(t)}
                        className="rounded-md px-2.5 py-1 text-xs font-semibold text-[#800020] ring-1 ring-[#800020]/40 transition hover:bg-[#800020] hover:text-white"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
