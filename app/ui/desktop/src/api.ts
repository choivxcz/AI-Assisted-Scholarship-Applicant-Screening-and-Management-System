export const API_BASE = "http://127.0.0.1:8765/api";
const TOKEN_KEY = "iskolar-staff-session";
export const getSessionToken = () => sessionStorage.getItem(TOKEN_KEY);
export const setSessionToken = (token: string | null) => token ? sessionStorage.setItem(TOKEN_KEY, token) : sessionStorage.removeItem(TOKEN_KEY);
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const token = getSessionToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401 && !String(input).endsWith("/auth/login")) {
    setSessionToken(null);
    window.dispatchEvent(new Event("iskolar-session-expired"));
  }
  return response;
}
