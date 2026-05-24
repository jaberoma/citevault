import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getSettings, listOllamaModels, putSettings } from "../../api/client";
import type { AppSettings } from "../../api/types";

export default function Settings() {
  const q = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const modelsQ = useQuery({ queryKey: ["ollama-models"], queryFn: listOllamaModels });
  const [draft, setDraft] = useState<AppSettings | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (q.data) setDraft(q.data);
  }, [q.data]);

  const save = useMutation({
    mutationFn: (s: AppSettings) => putSettings(s),
    onSuccess: () => setSaveError(null),
    onError: (e: Error) => setSaveError(e.message),
  });

  if (!draft) return <p>Loading…</p>;

  const availableModels = modelsQ.data?.models ?? [];

  return (
    <form
      className="space-y-4 max-w-lg"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate(draft);
      }}
    >
      <h1 className="text-2xl font-semibold">Settings</h1>
      <label className="block">
        <span className="block text-sm font-medium mb-1">Model</span>
        <div className="flex items-center gap-2">
          <input
            value={draft.model}
            onChange={(e) => setDraft({ ...draft, model: e.target.value })}
            className="flex-1 border rounded px-3 py-2"
          />
          {q.data?.available === true && (
            <span className="text-xs text-green-600 font-medium">available</span>
          )}
          {q.data?.available === false && (
            <span className="text-xs text-amber-600 font-medium">not downloaded</span>
          )}
        </div>
      </label>
      {availableModels.length > 0 && (
        <div>
          <span className="block text-xs text-neutral-500 mb-1">
            Downloaded models — click to select
          </span>
          <div className="flex flex-wrap gap-2">
            {availableModels.map((m) => (
              <button
                key={m.name}
                type="button"
                onClick={() => setDraft({ ...draft, model: m.name })}
                className="text-xs border rounded px-2 py-1 hover:bg-neutral-100"
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>
      )}
      {saveError && (
        <p className="text-sm text-red-600">{saveError}</p>
      )}
      <button
        type="submit"
        className="bg-neutral-900 text-white rounded px-4 py-2"
        disabled={save.isPending}
      >
        {save.isPending ? "Saving…" : "Save"}
      </button>
    </form>
  );
}
