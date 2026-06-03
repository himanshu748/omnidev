/** Backend API base URL. Set NEXT_PUBLIC_API_URL in .env.local for production. */
const configuredApiUrl =
  typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "";

function isLocalHost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

export const API_BASE =
  configuredApiUrl
    ? configuredApiUrl
    : "http://localhost:8000";

export function api(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export function isHostedWithoutApiConfig(): boolean {
  if (configuredApiUrl || typeof window === "undefined") return false;
  return !isLocalHost(window.location.hostname);
}
