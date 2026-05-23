import { describe, expect, it, vi, beforeEach } from "vitest";
import { listEvidence } from "../client";

describe("api client", () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it("calls /api/evidence and returns parsed sources", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ sources: [{ id: "s1", kind: "note", path: "x.md",
        created_at: "2026-05-11T00:00:00" }] }),
    } as Response);

    const result = await listEvidence();
    expect(result.sources).toHaveLength(1);
    expect(result.sources[0].id).toBe("s1");
  });

  it("throws on non-2xx", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false, status: 500, statusText: "Server Error", text: async () => "boom",
    } as Response);
    await expect(listEvidence()).rejects.toThrow();
  });
});
