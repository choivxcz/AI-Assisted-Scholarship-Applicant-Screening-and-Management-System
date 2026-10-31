export const API_BASE = "http://127.0.0.1:8765/api";
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(input, init);
}
