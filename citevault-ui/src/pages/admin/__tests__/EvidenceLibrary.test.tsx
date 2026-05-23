import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import EvidenceLibrary from "../EvidenceLibrary";

vi.mock("../../../api/client", () => ({
  listEvidence: vi.fn().mockResolvedValue({ sources: [
    { id: "s1", kind: "resume_master", path: "master.md",
      created_at: "2026-05-11T10:00:00" },
  ]}),
  uploadEvidence: vi.fn(),
  deleteEvidence: vi.fn(),
}));

function wrap(node: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        {node}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("EvidenceLibrary", () => {
  it("renders a source row", async () => {
    render(wrap(<EvidenceLibrary />));
    await waitFor(() => expect(screen.getByText("master.md")).toBeInTheDocument());
    expect(screen.getByText(/resume_master/)).toBeInTheDocument();
  });
});
