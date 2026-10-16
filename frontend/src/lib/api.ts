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
    readonly rowIds: string[] = [],
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
  const rowIds = Array.isArray(body.row_ids) ? body.row_ids.map(String) : [];
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
