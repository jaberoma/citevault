type Verdict = "VERIFIED" | "REWRITTEN" | "REJECTED" | string;

const styles: Record<string, string> = {
  VERIFIED: "bg-green-100 text-green-800",
  REWRITTEN: "bg-yellow-100 text-yellow-800",
  REJECTED: "bg-red-100 text-red-800",
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase ${styles[verdict] ?? "bg-neutral-100 text-neutral-700"}`}>
      {verdict}
    </span>
  );
}
