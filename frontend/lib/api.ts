// Types and fetch helpers for the FastAPI backend.
// Kept outside app/ because this is not a route — only app/**/page.tsx are.

// 127.0.0.1 rather than "localhost": Node resolves localhost to IPv6 (::1)
// first, but uvicorn listens on IPv4 only, so server components get ECONNREFUSED.
export const API = "http://127.0.0.1:8000";

// The backend validates status against this exact list (db.py STATUSES),
// so a union type here is accurate, not just a guess.
export type Status = "tailored" | "applied" | "interview" | "rejected" | "offer";

export const STATUSES: Status[] = [
  "tailored",
  "applied",
  "interview",
  "rejected",
  "offer",
];

// One row of the dashboard table — matches db.list_applications().
// The nullable fields are columns that can be NULL in SQLite.
export interface ApplicationSummary {
  id: number;
  company_name: string;
  created_at: string;
  jd_language: string | null;
  match_score: number | null;
  verdict: string | null;
  status: Status;
  pdf_filename: string | null;
}

// Matches db.get_stats().
export interface Stats {
  total: number;
  avg_score: number;
  applied: number;
  interviews: number;
  offers: number;
}

export interface DashboardData {
  stats: Stats;
  applications: ApplicationSummary[];
}

export interface RoadmapItem {
  skill: string;
  what_it_is: string;
  connects_to: string;
  timeline: string;
  project_idea: string;
}

// The stored LLM output. Every field is optional because it is whatever the
// model returned at the time — old rows may not have every key.
export interface TailorResult {
  tailored_cv?: string;
  cover_letter?: string;
  positioning_tip?: string;
  matched_keywords?: string[];
  missing_keywords?: string[];
  cv_edits?: string[];
  learning_roadmap?: RoadmapItem[];
  validation?: {
    verdict?: string;
    summary?: string;
    flags?: { type: string; detail: string }[];
  };
}

// One full application — the summary row plus the stored job description
// and the complete analysis result.
export interface ApplicationDetail extends ApplicationSummary {
  job_description: string;
  result: TailorResult;
}

// fetch() only rejects on network failure — a 404 or 500 still resolves,
// so the status has to be checked explicitly.
export async function fetchDashboard(): Promise<DashboardData> {
  const res = await fetch(`${API}/applications`);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

// Used by the detail page, which is a server component — cache: "no-store"
// stops Next from serving a stale copy after the status changes.
export async function fetchApplication(
  id: string,
): Promise<ApplicationDetail | null> {
  const res = await fetch(`${API}/applications/${id}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

export async function updateStatus(id: number, status: Status): Promise<void> {
  const res = await fetch(`${API}/applications/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(`Could not update status (${res.status})`);
}

export async function deleteApplication(id: number): Promise<void> {
  const res = await fetch(`${API}/applications/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Could not delete (${res.status})`);
}

// Formats the ISO timestamp stored by SQLite into something readable.
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}
