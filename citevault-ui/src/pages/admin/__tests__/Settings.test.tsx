import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Settings from "../Settings";

vi.mock("../../../api/client", () => ({
  getSettings: vi.fn().mockResolvedValue({ model: "gemma4:e4b", available: true }),
  putSettings: vi.fn().mockResolvedValue({ model: "gemma4:e4b", available: true }),
  listOllamaModels: vi.fn().mockResolvedValue({
    models: [{ name: "gemma4:e4b", size: 9608350718, family: "gemma4" }],
  }),
}));

function wrap(node: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{node}</QueryClientProvider>;
}

describe("Settings", () => {
  it("renders current model name", async () => {
    render(wrap(<Settings />));
    await waitFor(() =>
      expect(screen.getByDisplayValue("gemma4:e4b")).toBeInTheDocument()
    );
  });

  it("shows available badge when model is downloaded", async () => {
    render(wrap(<Settings />));
    await waitFor(() =>
      expect(screen.getByText("available")).toBeInTheDocument()
    );
  });

  it("shows downloaded model chips", async () => {
    render(wrap(<Settings />));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "gemma4:e4b" })).toBeInTheDocument()
    );
  });

  it("shows error message when save fails", async () => {
    const client = await import("../../../api/client");
    vi.mocked(client.putSettings).mockRejectedValueOnce(
      new Error("422: Model not downloaded. Run: ollama pull bad:v1")
    );
    render(wrap(<Settings />));
    await waitFor(() => screen.getByDisplayValue("gemma4:e4b"));
    fireEvent.change(screen.getByDisplayValue("gemma4:e4b"), {
      target: { value: "bad:v1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() =>
      expect(screen.getByText(/not downloaded/i)).toBeInTheDocument()
    );
  });
});
