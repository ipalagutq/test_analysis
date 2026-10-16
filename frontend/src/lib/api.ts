// Typed client for the FastAPI backend under /api; components never call fetch directly.
// Types mirror the Pydantic models in src/test_analysis/api/*.py.

export type Sex = "M" | "F";

export interface Patient {
  id: number;
  display_name: string;
  sex: Sex;
  birth_year: number;
}

export interface SampleInfo {
  name: string;
  title: string;
  media_type: string;
  patient_id: number;
}

export interface UploadCreated {
  draft_id: string;
}

export type Flag = "low" | "normal" | "high" | "unknown";

export type LlmFlag = "low" | "normal" | "high";

export type DraftStatus = "draft" | "confirmed" | "discarded";

export type TestGroup = "cbc" | "biochem";

/** One review row (extraction/normalize.py `DraftRow`). */
export interface DraftRow {
  row_id: number;
  test_name_raw: string;
  value_raw: string;
  value: number | null;
  unit_raw: string | null;
  code: string | null;
  canonical_value: number | null;
  canonical_unit: string | null;
  flag: Flag;
  llm_flag: LlmFlag | null;
  ref_range_raw: string | null;
  confidence: number;
  needs_review: boolean;
  include: boolean;
}

export interface Draft {
  id: string;
  patient_id: number;
  status: DraftStatus;
  model: string | null;
  extractor: string;
  page_count: number;
  rows: DraftRow[];
  created_at: string;
}

export interface CatalogEntry {
  code: string;
  name_ru: string;
  unit: string;
  group: TestGroup;
}

/** The reviewer's decision on one row; only these fields go to confirm. */
export interface ConfirmRow {
  row_id: number;
  code: string | null;
  canonical_value: number | null;
  include: boolean;
}

export interface ConfirmRequest {
  /** ISO date `YYYY-MM-DD`. */
  collected_at: string;
  rows: ConfirmRow[];
}

export interface VisitCreated {
  visit_id: number;
}

/** One confirmed result in a visit (patient_card/repository.py `TimelineResult`). */
export interface TimelineResult {
  code: string;
  name_ru: string;
  value: number;
  unit: string;
  flag: Flag;
}

export interface TimelineVisit {
  visit_id: number;
  /** ISO date `YYYY-MM-DD`. */
  collected_at: string;
  model: string | null;
  results: TimelineResult[];
}

export interface TrendPoint {
  collected_at: string;
  value: number;
  flag: Flag;
}

/** One test across visits; the reference interval is for the patient's sex. */
export interface Trend {
  code: string;
  unit: string;
  ref_low: number | null;
  ref_high: number | null;
  points: TrendPoint[];
}

export interface HealthStatus {
  status: "ok";
  version: string;
  extractor: "openrouter" | "fake";
}

/** Error in the backend `{"error", "detail"}` format (api/errors.py). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly detail: string,
    readonly rowIds: number[] = [],
  ) {
    super(`${code}: ${detail}`);
    this.name = "ApiError";
  }
}

interface ErrorBody {
  error?: unknown;
  detail?: unknown;
  row_ids?: unknown;
}

async function toApiError(response: Response): Promise<ApiError> {
  // unhandled 500s and proxy errors come back as plain text, not JSON
  let body: ErrorBody = {};
  try {
    body = (await response.json()) as ErrorBody;
  } catch {
    // keep the fallback below
  }
  const code = typeof body.error === "string" ? body.error : `http_${response.status}`;
  const detail =
    typeof body.detail === "string" ? body.detail : response.statusText || "Неизвестная ошибка";
  const rowIds = Array.isArray(body.row_ids) ? body.row_ids.map(Number) : [];
  return new ApiError(response.status, code, detail, rowIds);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, init);
  } catch {
    throw new ApiError(0, "network_error", "Сервер недоступен");
  }
  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as T;
}

function postJson<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health");
}

export function listPatients(): Promise<Patient[]> {
  return request<Patient[]>("/patients");
}

export function listSamples(): Promise<SampleInfo[]> {
  return request<SampleInfo[]>("/samples");
}

/** URL of a demo scan file, for a plain download link. */
export function sampleUrl(name: string): string {
  return `/api/samples/${encodeURIComponent(name)}`;
}

/** Upload a scan for a patient; resolves with the id of the review draft. */
export function uploadScan(file: File, patientId: number): Promise<UploadCreated> {
  const form = new FormData();
  form.append("file", file);
  form.append("patient_id", String(patientId));
  // no Content-Type header: the browser sets the multipart boundary itself
  return request<UploadCreated>("/uploads", { method: "POST", body: form });
}

export function listCatalog(): Promise<CatalogEntry[]> {
  return request<CatalogEntry[]>("/catalog");
}

export function getDraft(draftId: string): Promise<Draft> {
  return request<Draft>(`/drafts/${encodeURIComponent(draftId)}`);
}

/** URL of the PNG of a draft page; pages are numbered from 0. */
export function draftPageUrl(draftId: string, page: number): string {
  return `/api/drafts/${encodeURIComponent(draftId)}/pages/${page}`;
}

/** Write the included rows into a new visit; 422 `ApiError.rowIds` lists the invalid rows. */
export function confirmDraft(draftId: string, body: ConfirmRequest): Promise<VisitCreated> {
  return postJson<VisitCreated>(`/drafts/${encodeURIComponent(draftId)}/confirm`, body);
}

export function discardDraft(draftId: string): Promise<Draft> {
  return postJson<Draft>(`/drafts/${encodeURIComponent(draftId)}/discard`);
}

/** Visits of a patient, newest first. */
export function getTimeline(patientId: number): Promise<TimelineVisit[]> {
  return request<TimelineVisit[]>(`/patients/${patientId}/timeline`);
}

/** Values of one test across the patient's visits, oldest first. */
export function getTrend(patientId: number, code: string): Promise<Trend> {
  return request<Trend>(`/patients/${patientId}/trends?code=${encodeURIComponent(code)}`);
}
