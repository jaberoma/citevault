export type SourceKind = "resume_master" | "readme" | "blog_post" | "note";

export interface Source {
  id: string;
  kind: SourceKind;
  path: string;
  created_at: string;
}

export interface SourceDetail extends Source {
  text: string;
  spans: Span[];
}

export interface Span {
  id: string;
  start_offset: number;
  end_offset: number;
  text: string;
}

export interface TailorRequest {
  job_posting: string;
  naive_compare?: boolean;
}

export interface VerifiedClaim {
  id: string;
  text: string;
  citations: string[];
}

export interface GapEntry {
  requirement_text: string;
  closest_evidence: string | null;
  neutral_suggestion: string;
}

export interface TailoringResult {
  tailoring_id: string;
  status: "running" | "complete" | "error";
  resume_md?: string;
  cover_letter_md?: string;
  gaps_md?: string;
  verified_claims?: VerifiedClaim[];
  gap_report?: GapEntry[];
  span_texts?: Record<string, string>;
  summary?: {
    drafts_total: number;
    first_pass_verified: number;
    rewritten_verified: number;
    rejected: number;
    requirements_total: number;
    requirements_met: number;
  };
  naive_md?: string | null;
  pdf_ready?: boolean;
  error?: string;
}

export interface AppSettings {
  model: string;
  available?: boolean;
}

export interface OllamaModel {
  name: string;
  size: number;
  family: string;
}

export interface HealthStatus {
  status: "ok" | "loading";
}
