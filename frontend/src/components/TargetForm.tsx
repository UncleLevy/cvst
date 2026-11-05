import { Loader2, Plus } from "lucide-react";
import { useState, type FormEvent } from "react";
import api, { errorMessage } from "@/api/client";
import type { TargetType } from "@/types";

export const TARGET_TYPES: { value: TargetType; label: string; placeholder: string }[] = [
  { value: "ip", label: "IP address", placeholder: "192.168.1.10" },
  { value: "hostname", label: "Hostname", placeholder: "server.example.com" },
  { value: "url", label: "URL", placeholder: "https://example.com" },
  { value: "network", label: "Network range", placeholder: "192.168.1.0/24" },
];

export default function TargetForm({ onCreated }: { onCreated: () => void | Promise<void> }) {
  const [name, setName] = useState("");
  const [targetType, setTargetType] = useState<TargetType>("ip");
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const clean = value.trim();
    if (/\s/.test(clean) || clean.startsWith("-")) {
      setError("Enter a single address or range, with no spaces.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.post("/targets/", {
        name: name.trim(),
        target_type: targetType,
        value: clean,
        description: description.trim(),
      });
      setName("");
      setValue("");
      setDescription("");
      await onCreated();
    } catch (err) {
      setError(errorMessage(err, "Could not add the target."));
    } finally {
      setBusy(false);
    }
  };

  const placeholder = TARGET_TYPES.find((t) => t.value === targetType)?.placeholder;

  return (
    <form onSubmit={submit} className="surface p-5">
      <h2 className="text-[15px] font-semibold text-navy-800">Add target</h2>
      <p className="mt-1 text-xs text-slate-500">
        Authorised assets only — every scan is logged against the target you pick.
      </p>
      {error && <p className="mt-3 rounded-lg bg-wine-100 px-3 py-2 text-sm font-medium text-wine-800">{error}</p>}
      <div className="mt-4 grid gap-4 md:grid-cols-4">
        <div>
          <label className="label-xs" htmlFor="t-name">
            Name
          </label>
          <input
            id="t-name"
            className="field"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Customer portal"
            required
          />
        </div>
        <div>
          <label className="label-xs" htmlFor="t-type">
            Type
          </label>
          <select
            id="t-type"
            className="field"
            value={targetType}
            onChange={(e) => setTargetType(e.target.value as TargetType)}
          >
            {TARGET_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="label-xs" htmlFor="t-value">
            Value
          </label>
          <input
            id="t-value"
            className="field font-mono"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={placeholder}
            required
          />
        </div>
        <div className="md:col-span-4">
          <label className="label-xs" htmlFor="t-desc">
            Description (optional)
          </label>
          <input
            id="t-desc"
            className="field"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Owned by the platform team"
          />
        </div>
      </div>
      <div className="mt-4 flex justify-end">
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {busy ? "Adding…" : "Add target"}
        </button>
      </div>
    </form>
  );
}
