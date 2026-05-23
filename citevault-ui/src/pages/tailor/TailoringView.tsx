import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { streamTailoring, getTailoring, getPdfUrl } from "../../api/client";
import type { TailoringResult } from "../../api/types";
import { ClaimWithCitations } from "../../components/ClaimWithCitations";
import { VerdictBadge } from "../../components/VerdictBadge";
import { DiffViewer } from "../../components/DiffViewer";

type Tab = "resume" | "cover" | "naive" | "diff";

export default function TailoringView() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<TailoringResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<{ event: string; data: Record<string, unknown> }[]>([]);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [tab, setTab] = useState<Tab>("resume");

  useEffect(() => {
    if (!id) return;

    getTailoring(id).then((data) => {
      setResult(data);
      if (data.status === "complete" || data.status === "error") return;

      const es = streamTailoring(id);
      es.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data as string) as { event: string; data: Record<string, unknown> };
          if (msg.event === "complete") {
            getTailoring(id).then(setResult);
            es.close();
          } else {
            setLogs((prev) => [...prev, msg]);
          }
        } catch {
          es.close();
        }
      };
      es.onerror = () => es.close();
    }).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Tailoring not found.");
    });
  }, [id]);

  useEffect(() => {
    if (!result || result.status !== "complete" || result.pdf_ready) return;
    setPdfGenerating(true);
    const timer = setInterval(() => {
      getTailoring(id!).then((updated) => {
        if (updated.pdf_ready) {
          setResult(updated);
          setPdfGenerating(false);
          clearInterval(timer);
        }
      });
    }, 2000);
    return () => clearInterval(timer);
  }, [id, result?.status, result?.pdf_ready]);

  if (error) return (
    <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {error}
    </div>
  );
  if (!result) return <p>Loading tailoring {id}...</p>;

  const tabs: { key: Tab; label: string }[] = [
    { key: "resume", label: "Résumé" },
    { key: "cover", label: "Cover Letter" },
    ...(result.naive_md ? [
      { key: "naive" as Tab, label: "Naive AI" },
      { key: "diff" as Tab, label: "Diff" },
    ] : []),
  ];

  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tailoring Result</h1>
        <div className="flex items-center gap-3">
          {result.pdf_ready ? (
            <a
              href={getPdfUrl(id!)}
              download="citevault-resume.pdf"
              className="text-sm bg-neutral-900 text-white rounded px-3 py-1.5 hover:bg-neutral-700"
            >
              Download PDF
            </a>
          ) : pdfGenerating ? (
            <span className="text-sm text-neutral-400">Generating PDF…</span>
          ) : null}
          <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
            result.status === "complete" ? "bg-green-100 text-green-700" : "bg-blue-100 text-blue-700"
          }`}>
            {result.status}
          </span>
        </div>
      </header>

      {result.status === "running" && (
        <div className="bg-neutral-900 text-neutral-400 p-4 rounded font-mono text-xs h-64 overflow-y-auto space-y-1">
          {logs.map((l, i) => (
            <div key={i} className="flex items-center gap-2">
              {l.data?.verdict && <VerdictBadge verdict={String(l.data.verdict)} />}
              <span>{l.event}{l.data?.text ? `: ${String(l.data.text)}` : ""}</span>
            </div>
          ))}
          <div className="animate-pulse text-white">_ Processing...</div>
        </div>
      )}

      {result.verified_claims && result.verified_claims.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-medium border-b pb-2 text-neutral-500">Verified Grounded Claims</h2>
          <ul className="list-disc pl-5 space-y-2">
            {result.verified_claims.map((claim) => (
              <li key={claim.id}>
                <ClaimWithCitations
                  text={claim.text}
                  citations={claim.citations}
                  spanTexts={result.span_texts || {}}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      {result.resume_md && (
        <div className="space-y-4">
          <div className="flex gap-2 border-b">
            {tabs.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 text-sm font-medium -mb-px border-b-2 transition-colors ${
                  tab === t.key
                    ? "border-neutral-900 text-neutral-900"
                    : "border-transparent text-neutral-500 hover:text-neutral-700"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "resume" && (
            <div className="prose prose-sm max-w-none bg-white p-6 border rounded shadow-sm
              [&_.footnotes]:border-t [&_.footnotes]:mt-6 [&_.footnotes]:pt-4
              [&_.footnotes]:text-xs [&_.footnotes]:text-neutral-500
              [&_.footnotes_li]:mt-1">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.resume_md}</ReactMarkdown>
            </div>
          )}
          {tab === "cover" && (
            <div className="prose prose-sm max-w-none bg-white p-6 border rounded shadow-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.cover_letter_md || ""}</ReactMarkdown>
            </div>
          )}
          {tab === "naive" && result.naive_md && (
            <pre className="bg-red-50 border border-red-200 p-4 rounded text-sm whitespace-pre-wrap">
              {result.naive_md}
            </pre>
          )}
          {tab === "diff" && result.naive_md && (
            <DiffViewer left={result.resume_md} right={result.naive_md} />
          )}
        </div>
      )}

      {result.gap_report && result.gap_report.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-medium border-b pb-2">Gap Analysis</h2>
          <div className="space-y-3">
            {result.gap_report.map((gap, i) => (
              <div key={i} className="bg-amber-50 border border-amber-200 p-4 rounded text-sm">
                <p className="font-semibold text-amber-900">{gap.requirement_text}</p>
                <p className="text-amber-800 mt-1 italic">Suggestion: {gap.neutral_suggestion}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
