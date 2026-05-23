import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import History from "../History";

vi.mock("../../../api/client", () => ({
  listTailorings: vi.fn().mockResolvedValue({ tailorings: [
    { tailoring_id: "t-1", status: "complete",
      summary: { first_pass_verified: 5, drafts_total: 7 },
      job_role: "Senior Backend Engineer" },
  ]}),
}));

function wrap(node: React.ReactElement) {
  const qc = new QueryClient();
  return <QueryClientProvider client={qc}><MemoryRouter>{node}</MemoryRouter></QueryClientProvider>;
}

describe("History", () => {
  it("renders a row with job role", async () => {
    render(wrap(<History />));
    await waitFor(() =>
      expect(screen.getByText(/Senior Backend Engineer/)).toBeInTheDocument()
    );
    expect(screen.getByText(/5 \/ 7 verified/)).toBeInTheDocument();
  });
});
