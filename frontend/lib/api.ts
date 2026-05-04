import { clearToken, getToken } from "./auth";

/**
 * Base URL for browser API calls. Empty string = same origin (nginx or single host).
 * Set NEXT_PUBLIC_API_URL at build time only if the API is on a different host than the UI.
 */
export function getPublicApiBase(): string {
  const u = process.env.NEXT_PUBLIC_API_URL;
  if (u === undefined || u === "") return "";
  return u.replace(/\/$/, "");
}

export function apiUrl(path: string): string {
  const base = getPublicApiBase();
  if (path.startsWith("http")) return path;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function apiFetch<T>(
  path: string,
  opts: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(opts.headers);
  headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");
  if (opts.auth !== false) {
    const t = getToken();
    if (t) headers.set("Authorization", `Bearer ${t}`);
  }
  const res = await fetch(apiUrl(path), { ...opts, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && !path.includes("/auth/login")) {
      window.location.href = "/login";
    }
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
