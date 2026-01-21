import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { webcrypto } from "crypto";
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME, middleware } from "../middleware";

let mockUser: {
    app_metadata?: { role?: string };
    user_metadata?: { role?: string };
    role?: string;
} | null = null;

vi.mock("@supabase/ssr", () => ({
    createServerClient: (
        _url: string,
        _key: string,
        options: {
            cookies: {
                getAll: () => Array<{ name: string; value: string }>;
                setAll: (cookies: Array<{ name: string; value: string }>) => void;
            };
        }
    ) => {
        options.cookies.getAll();
        options.cookies.setAll([{ name: "sb-session", value: "mock" }]);
        return {
            auth: {
                getUser: async () => ({ data: { user: mockUser } }),
            },
        };
    },
}));

const buildRequest = (url: string, init: RequestInit = {}) =>
    new NextRequest(new Request(url, init));

const withCookie = (request: NextRequest, cookie: string) =>
    new NextRequest(
        new Request(request.url, {
            method: request.method,
            headers: new Headers({
                ...Object.fromEntries(request.headers.entries()),
                cookie,
            }),
        })
    );

beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";
    if (!globalThis.crypto) {
        globalThis.crypto = webcrypto as unknown as Crypto;
    }
});

describe("middleware", () => {
    it("redirects unauthenticated users to login", async () => {
        mockUser = null;
        const request = buildRequest("https://example.com/chat");
        const response = await middleware(request);

        expect(response.status).toBe(307);
        expect(response.headers.get("location")).toContain("/auth/login");
        expect(response.cookies.get(CSRF_COOKIE_NAME)).toBeDefined();
    });

    it("allows unauthenticated users on public auth pages", async () => {
        mockUser = null;
        const request = buildRequest("https://example.com/auth/signup");
        const response = await middleware(request);

        expect(response.status).toBe(200);
    });

    it("allows authenticated users on public auth pages and redirects to home", async () => {
        mockUser = { role: "authenticated", app_metadata: { role: "user" } };
        const request = buildRequest("https://example.com/auth/login");
        const response = await middleware(request);

        expect(response.status).toBe(307);
        expect(response.headers.get("location")).toBe("https://example.com/");
    });

    it("allows authenticated users with required role", async () => {
        mockUser = { role: "authenticated", app_metadata: { role: "admin" } };
        const request = buildRequest("https://example.com/devops");
        const response = await middleware(request);

        expect(response.status).toBe(200);
    });

    it("blocks users without required role", async () => {
        mockUser = { role: "authenticated", app_metadata: { role: "user" } };
        const request = buildRequest("https://example.com/devops");
        const response = await middleware(request);

        expect(response.status).toBe(307);
        expect(response.headers.get("location")).toContain("error=forbidden");
    });

    it("reads role from user metadata", async () => {
        mockUser = { user_metadata: { role: "admin" } };
        const request = buildRequest("https://example.com/devops");
        const response = await middleware(request);

        expect(response.status).toBe(200);
    });

    it("defaults to user role when metadata is missing", async () => {
        mockUser = {};
        const request = buildRequest("https://example.com/chat");
        const response = await middleware(request);

        expect(response.status).toBe(200);
    });

    it("skips auth for static asset paths", async () => {
        mockUser = null;
        const request = buildRequest("https://example.com/_next/static/app.js");
        const response = await middleware(request);

        expect(response.status).toBe(200);
    });

    it("returns 503 when supabase config is missing", async () => {
        delete process.env.NEXT_PUBLIC_SUPABASE_URL;
        delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
        mockUser = null;
        const request = buildRequest("https://example.com/chat");
        const response = await middleware(request);

        expect(response.status).toBe(503);
    });

    it("rejects missing CSRF token on unsafe methods", async () => {
        mockUser = { role: "authenticated", app_metadata: { role: "user" } };
        const request = buildRequest("https://example.com/api/ai/chat", {
            method: "POST",
        });
        const response = await middleware(request);

        expect(response.status).toBe(403);
    });

    it("allows CSRF protected requests with valid token", async () => {
        mockUser = { role: "authenticated", app_metadata: { role: "user" } };
        const csrfToken = "test-token";
        const request = withCookie(
            buildRequest("https://example.com/api/ai/chat", {
                method: "POST",
                headers: { [CSRF_HEADER_NAME]: csrfToken },
            }),
            `${CSRF_COOKIE_NAME}=${csrfToken}`
        );
        const response = await middleware(request);

        expect(response.status).toBe(200);
    });
});
