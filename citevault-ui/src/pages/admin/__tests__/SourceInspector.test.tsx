import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SourceInspector from "../SourceInspector";

vi.mock("../../../api/client", () => ({
  getSource: vi.fn().mockResolvedValue({
    id: "s1", kind: "note", path: "x.md", text: "hello",
    created_at: "2026-05-11", spans: [
      { id: "sp1", start_offset: 0, end_offset: 5, text: "hello" },
    ],
  }),
}));

function wrap(node: React.ReactElement, route = "/admin/source/s1") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/admin/source/:id" element={node} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("SourceInspector", () => {
  it("shows path and a span", async () => {
    render(wrap(<SourceInspector />));
    await waitFor(() => expect(screen.getByText("x.md")).toBeInTheDocument());
    expect(screen.getByText("hello")).toBeInTheDocument();
  });
});
