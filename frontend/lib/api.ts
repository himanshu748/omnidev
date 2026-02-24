/** Backend API base URL. Set NEXT_PUBLIC_API_URL in .env.local for production. */
export const API_BASE =
  typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : (() => {
        if (typeof window !== "undefined") {
          return `http://${window.location.hostname}:8000`;
        }
        return "http://localhost:8000";
      })();

export function api(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}
