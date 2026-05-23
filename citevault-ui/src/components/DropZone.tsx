import { useRef, useState } from "react";

export function DropZone({
  onFiles,
  disabled = false,
}: {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}) {
  const [hover, setHover] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  return (
    <div
      onDragOver={(e) => { if (disabled) return; e.preventDefault(); setHover(true); }}
      onDragLeave={() => setHover(false)}
      onDrop={(e) => {
        e.preventDefault(); setHover(false);
        if (!disabled) onFiles(Array.from(e.dataTransfer.files));
      }}
      onClick={() => { if (!disabled) input.current?.click(); }}
      title={disabled ? "Backend is still loading — please wait" : undefined}
      className={`border-2 border-dashed rounded-lg p-8 text-center
        ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}
        ${hover && !disabled ? "border-neutral-900 bg-neutral-100" : "border-neutral-300"}`}
    >
      <p className="text-neutral-600">Drag-and-drop files (.md, .txt, .pdf), or click to choose.</p>
      <input
        ref={input} type="file" multiple accept=".md,.txt,.pdf" className="hidden"
        disabled={disabled}
        onChange={(e) => onFiles(Array.from(e.target.files ?? []))}
      />
    </div>
  );
}
