export function DiffViewer({ left, right }: { left: string; right: string }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <p className="text-xs font-semibold text-green-700 mb-1">Citevault (grounded)</p>
        <pre className="bg-emerald-50 border border-emerald-200 p-3 rounded text-sm whitespace-pre-wrap">
          {left}
        </pre>
      </div>
      <div>
        <p className="text-xs font-semibold text-red-700 mb-1">Naive AI (ungrounded)</p>
        <pre className="bg-red-50 border border-red-200 p-3 rounded text-sm whitespace-pre-wrap">
          {right}
        </pre>
      </div>
    </div>
  );
}
