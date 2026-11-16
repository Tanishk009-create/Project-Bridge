const API_URL = "/api/v1";
let refreshInFlight: Promise<boolean> | null = null;

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options, credentials: "include", cache: "no-store",
      signal: options.signal ?? AbortSignal.timeout(15000),
      headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError(0, "Bridge could not reach the server. Check that the backend is running and try again.");
  }
  if (response.status === 401 && retry && !path.startsWith("/auth/")) {
    refreshInFlight ??= fetch(`${API_URL}/auth/refresh`, {method: "POST", credentials: "include", signal: AbortSignal.timeout(10000)})
      .then(r => r.ok).catch(() => false).finally(() => { refreshInFlight = null; });
    if (await refreshInFlight) return apiRequest<T>(path, options, false);
    window.dispatchEvent(new Event("bridge-session-expired"));
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((item: {msg: string}) => item.msg.replace(/^Value error, /, "")).join(" ")
      : `Request failed (${response.status}). Please try again.`;
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function errorMessage(error: unknown) { return error instanceof Error ? error.message : "Something went wrong. Please try again."; }
export function apiDate(value: string) { return new Date(/Z$|[+-]\d\d:\d\d$/.test(value) ? value : value + "Z"); }
