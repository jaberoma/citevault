import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { deleteEvidence, getHealth, listEvidence, uploadEvidence } from "../../api/client";
import { DropZone } from "../../components/DropZone";

export default function EvidenceLibrary() {
  const qc = useQueryClient();
  const [uploadingCount, setUploadingCount] = useState(0);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const warming = !health.data || health.data.status === "loading";
  const list = useQuery({ queryKey: ["evidence"], queryFn: listEvidence });
  const upload = useMutation({
    mutationFn: (file: File) => uploadEvidence(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evidence"] }),
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteEvidence(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evidence"] }),
  });

  async function handleFiles(files: File[]) {
    const existingNames = new Set(
      list.data?.sources.map((s) => s.path.split("/").pop() ?? s.path) ?? []
    );
    const newFiles = files.filter((f) => !existingNames.has(f.name));
    if (!newFiles.length) return;

    setUploadErrors([]);
    setUploadingCount(newFiles.length);
    await Promise.all(
      newFiles.map(async (f) => {
        try {
          await upload.mutateAsync(f);
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          setUploadErrors((prev) => [...prev, `${f.name}: ${msg}`]);
        } finally {
          setUploadingCount((n) => n - 1);
        }
      })
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Evidence Library</h1>
      <DropZone onFiles={handleFiles} disabled={warming} />
      {uploadingCount > 0 && (
        <div className="flex items-center gap-2 text-sm text-neutral-600">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Uploading {uploadingCount} file{uploadingCount > 1 ? "s" : ""}…
        </div>
      )}
      {uploadErrors.length > 0 && (
        <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 space-y-1">
          <p className="font-medium">Upload failed:</p>
          {uploadErrors.map((e, i) => <p key={i}>{e}</p>)}
        </div>
      )}
      {list.isLoading && <p>Loading…</p>}
      {list.data && (
        <table className="w-full border border-neutral-200 rounded">
          <thead className="bg-neutral-100 text-left text-sm">
            <tr>
              <th className="px-3 py-2">File</th>
              <th className="px-3 py-2">Kind</th>
              <th className="px-3 py-2">Added</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {list.data.sources.map((s) => (
              <tr key={s.id} className="border-t border-neutral-200">
                <td className="px-3 py-2">
                  <Link to={`/admin/source/${s.id}`} className="text-blue-600 hover:underline">
                    {s.path.split("/").pop() ?? s.path}
                  </Link>
                </td>
                <td className="px-3 py-2 text-neutral-500">{s.kind}</td>
                <td className="px-3 py-2 text-neutral-500">
                  {new Date(s.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    className="text-red-600 hover:underline"
                    onClick={() => remove.mutate(s.id)}
                  >Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
