import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getHealth, startTailor } from "../../api/client";

export default function NewTailoring() {
  const [text, setText] = useState("");
  const [naive, setNaive] = useState(false);
  const nav = useNavigate();
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const warming = !health.data || health.data.status === "loading";
  const mut = useMutation({
    mutationFn: () => startTailor(text, naive),
    onSuccess: (data) => nav(`/tailor/${data.tailoring_id}`),
  });
  const canSubmit = !warming && !!text && !mut.isPending;
  const buttonLabel = warming ? "Backend loading…" : mut.isPending ? "Starting…" : "Tailor";
  return (
    <div className="space-y-4 max-w-3xl">
      <h1 className="text-2xl font-semibold">New Tailoring</h1>
      <textarea
        value={text} onChange={(e) => setText(e.target.value)}
        placeholder="Paste the job posting here…"
        rows={14}
        className="w-full border rounded p-3 font-mono text-sm"
      />
      <div className="flex items-center gap-3">
        <label className="text-sm">
          <input type="checkbox" checked={naive}
            onChange={(e) => setNaive(e.target.checked)} />
          {" "}Also generate a naive-AI comparison (slower, but shows the contrast)
        </label>
      </div>
      <button
        className="bg-neutral-900 text-white rounded px-4 py-2 disabled:opacity-50"
        disabled={!canSubmit}
        title={warming ? "Backend is still loading — please wait" : undefined}
        onClick={() => mut.mutate()}
      >{buttonLabel}</button>
    </div>
  );
}
