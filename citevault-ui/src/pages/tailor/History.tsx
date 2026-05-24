import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listTailorings } from "../../api/client";

export default function History() {
  const q = useQuery({ queryKey: ["tailorings"], queryFn: listTailorings });

  if (q.isLoading) return <p>Loading history...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Tailoring History</h1>
      <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-neutral-50 border-b font-medium text-neutral-500 uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3">Role</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Grounding</th>
              <th className="px-6 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {q.data?.tailorings.map((t) => (
              <tr key={t.tailoring_id} className="hover:bg-neutral-50 transition-colors">
                <td className="px-6 py-4 font-medium">
                  {t.job_role || "(Unknown Role)"}
                  <div className="text-xs text-neutral-400 font-mono mt-0.5">{t.tailoring_id}</div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs uppercase font-bold ${
                    t.status === "complete" ? "bg-green-100 text-green-700" : "bg-blue-100 text-blue-700"
                  }`}>
                    {t.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-neutral-600">
                  {t.summary ? (
                    <span>{t.summary.first_pass_verified} / {t.summary.drafts_total} verified</span>
                  ) : "-"}
                </td>
                <td className="px-6 py-4 text-right">
                  <Link
                    to={`/tailor/${t.tailoring_id}`}
                    className="text-blue-600 hover:underline font-medium"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
            {(!q.data || q.data.tailorings.length === 0) && (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-neutral-500">
                  No tailorings yet. Start a new one!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
