import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import NewTailoring from "../NewTailoring";

const start = vi.fn().mockResolvedValue({ tailoring_id: "t-1" });
vi.mock("../../../api/client", () => ({
  startTailor: (...a: unknown[]) => start(...a),
}));
const nav = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom"
  );
  return { ...actual, useNavigate: () => nav };
});

function wrap(node: React.ReactElement) {
  const qc = new QueryClient();
  return <QueryClientProvider client={qc}><MemoryRouter>{node}</MemoryRouter></QueryClientProvider>;
}

describe("NewTailoring", () => {
  it("submits and navigates", async () => {
    render(wrap(<NewTailoring />));
    fireEvent.change(screen.getByPlaceholderText(/paste/i), {
      target: { value: "Job posting text" },
    });
    fireEvent.click(screen.getByRole("button", { name: /tailor/i }));
    await waitFor(() => expect(start).toHaveBeenCalledWith("Job posting text", false));
    expect(nav).toHaveBeenCalledWith("/tailor/t-1");
  });
});
