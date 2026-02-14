/** Backend API base URL. Set NEXT_PUBLIC_API_URL in .env.local for production. */
export const API_BASE =
  typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "http://localhost:8000";

export function api(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}
