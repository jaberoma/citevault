import type { AppSettings, HealthStatus, OllamaModel, Source, SourceDetail, TailoringResult } from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string) || "";

async function jfetch<T>(input: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${input}`, init);
  if (!r.ok) {
    const body = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText}: ${body}`);
  }
  return r.json() as Promise<T>;
}

export const listEvidence = () => jfetch<{ sources: Source[] }>("/api/evidence");

export const getSource = (id: string) =>
  jfetch<SourceDetail>(`/api/evidence/source/${id}`);

export const uploadEvidence = async (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/api/evidence/source`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ id: string; kind: string; path: string }>;
};

export const deleteEvidence = async (id: string) => {
  const r = await fetch(`${BASE}/api/evidence/source/${id}`, { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
};

export const startTailor = (job_posting: string, naive_compare = false) =>
  jfetch<{ tailoring_id: string }>("/api/tailor", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_posting, naive_compare }),
  });

export const getTailoring = (id: string) =>
  jfetch<TailoringResult>(`/api/tailor/${id}`);

export const streamTailoring = (id: string) =>
  new EventSource(`${BASE}/api/tailor/${id}/stream`);

export const listTailorings = () =>
  jfetch<{
    tailorings: {
      tailoring_id: string;
      status: string;
      job_role?: string;
      summary?: { drafts_total: number; first_pass_verified: number };
    }[];
  }>("/api/tailor");

export const getPdfUrl = (id: string) => `${BASE}/api/tailor/${id}/pdf`;

export const getHealth = () => jfetch<HealthStatus>("/api/health");
export const getSettings = () => jfetch<AppSettings>("/api/settings");
export const putSettings = (s: AppSettings) =>
  jfetch<AppSettings>("/api/settings", {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(s),
  });
export const listOllamaModels = () =>
  jfetch<{ models: OllamaModel[] }>("/api/ollama/models");
