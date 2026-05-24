import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { getSource } from "../../api/client";

export default function SourceInspector() {
  const { id } = useParams<{ id: string }>();
  const q = useQuery({
    queryKey: ["source", id], queryFn: () => getSource(id!), enabled: !!id,
  });
  if (q.isLoading) return <p>Loading…</p>;
  if (!q.data) return <p>Not found.</p>;
  return (
    <div className="space-y-4">
      <Link to="/admin" className="text-sm text-neutral-500">← Back</Link>
      <h1 className="text-2xl font-semibold">{q.data.path}</h1>
      <p className="text-sm text-neutral-500">Kind: {q.data.kind}</p>
      <h2 className="text-lg font-medium mt-6">Spans ({q.data.spans.length})</h2>
      <ul className="divide-y divide-neutral-200 border border-neutral-200 rounded">
        {q.data.spans.map((s) => (
          <li key={s.id} className="px-3 py-2 text-sm">
            <span className="text-xs text-neutral-400 mr-2">[{s.id}]</span>
            {s.text}
          </li>
        ))}
      </ul>
    </div>
  );
}
