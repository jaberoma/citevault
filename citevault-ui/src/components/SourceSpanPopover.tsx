import * as Popover from "@radix-ui/react-popover";

export function SourceSpanPopover({
  trigger, content,
}: { trigger: React.ReactNode; content: string }) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button className="text-blue-600 hover:underline">{trigger}</button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content sideOffset={4}
          className="bg-white border border-neutral-200 rounded p-3 max-w-md text-sm shadow-lg z-50">
          {content}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
