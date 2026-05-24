import { SourceSpanPopover } from "./SourceSpanPopover";

export function ClaimWithCitations({
  text, citations, spanTexts,
}: { text: string; citations: string[]; spanTexts: Record<string, string> }) {
  return (
    <span>
      {text}{" "}
      {citations.map((id) => (
        <SourceSpanPopover key={id}
          trigger={<sup>[{id}]</sup>}
          content={spanTexts[id] ?? "(span text unavailable)"} />
      ))}
    </span>
  );
}
