import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import TailoringView from "../TailoringView";

const mockGet = vi.fn();
const mockStream = vi.fn();

vi.mock("../../../api/client", () => ({
  getTailoring: (...a: unknown[]) => mockGet(...a),
  streamTailoring: (...a: unknown[]) => mockStream(...a),
}));

describe("TailoringView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock EventSource minimal
    mockStream.mockReturnValue({
      close: vi.fn(),
      onmessage: null,
      onerror: null,
    });
  });

  it("shows resume markdown once complete", async () => {
    mockGet.mockResolvedValue({
      status: "complete",
      resume_md: "# Tailored Résumé\n- Experience 1",
    });

    render(
      <MemoryRouter initialEntries={["/tailor/t1"]}>
        <Routes><Route path="/tailor/:id" element={<TailoringView />} /></Routes>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("Experience 1")).toBeInTheDocument());
    expect(screen.getAllByText("Tailored Résumé")).toHaveLength(2);
  });

  it("shows loading state while fetching initial data", () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves
    render(
      <MemoryRouter initialEntries={["/tailor/t1"]}>
        <Routes><Route path="/tailor/:id" element={<TailoringView />} /></Routes>
      </MemoryRouter>
    );
    expect(screen.getByText(/loading tailoring t1/i)).toBeInTheDocument();
  });
});
