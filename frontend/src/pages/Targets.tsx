import { Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "@/api/client";
import PageHeader from "@/components/PageHeader";
import TargetForm, { TARGET_TYPES } from "@/components/TargetForm";
import { listOf, type Paginated, type Target } from "@/types";

export default function Targets() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removing, setRemoving] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Paginated<Target>>("/targets/", { params: { page_size: 200 } });
      const items = listOf(res.data);
      setTargets(items);
      setCount(res.data.count ?? items.length);
      setError(null);
    } catch (err) {
      setError(errorMessage(err, "Could not load targets."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async (target: Target) => {
    if (!window.confirm(`Remove target "${target.name}"? Existing scan history is kept.`)) return;
    setRemoving(target.id);
    try {
      await api.delete(`/targets/${target.id}/`);
      await load();
    } catch (err) {
      setError(errorMessage(err, "Could not remove the target."));
    } finally {
      setRemoving(null);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Scope"
        title="Targets"
        subtitle="Hosts, addresses and sites you are authorised to scan."
        actions={
          <Link to="/" className="btn-quiet">
            <Plus className="h-4 w-4" /> New scan
          </Link>
        }
      />

      {error && <p className="notice-error mb-4">{error}</p>}

      <TargetForm onCreated={load} />

      <div className="surface mt-5 overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-[15px] font-semibold text-navy-800">Authorised assets</h2>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
            {count} active
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="table-head">
              <tr>
                {["Name", "Type", "Value", "Added", ""].map((h, i) => (
                  <th key={i} className="px-5 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading && (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center text-sm text-slate-500">
                    Loading targets…
                  </td>
                </tr>
              )}
              {!loading && targets.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center text-sm text-slate-500">
                    No targets yet. Add one above.
                  </td>
                </tr>
              )}
              {targets.map((target) => (
                <tr key={target.id} className="transition-colors hover:bg-wine-700/[0.03]">
                  <td className="px-5 py-3.5">
                    <p className="font-semibold text-navy-800">{target.name}</p>
                    {target.description && <p className="text-[11px] text-slate-500">{target.description}</p>}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="rounded-md bg-navy-700/[0.06] px-2 py-0.5 text-[11px] font-semibold text-navy-700">
                      {TARGET_TYPES.find((t) => t.value === target.target_type)?.label ?? target.target_type}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-mono text-xs text-slate-600">{target.value}</td>
                  <td className="whitespace-nowrap px-5 py-3.5 text-xs text-slate-500">
                    {new Date(target.created_at).toLocaleDateString(undefined, {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={() => remove(target)}
                      disabled={removing === target.id}
                      className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-semibold text-slate-500 transition hover:bg-wine-700 hover:text-white disabled:opacity-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
