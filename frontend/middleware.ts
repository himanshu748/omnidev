import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

export const CSRF_COOKIE_NAME = "omnidev_csrf";
export const CSRF_HEADER_NAME = "x-omnidev-csrf";

const PUBLIC_PATHS = ["/auth/login", "/auth/signup"];
const ROLE_RULES = [
    { prefix: "/devops", roles: ["admin"] },
    { prefix: "/storage", roles: ["admin"] },
];
const SAFE_METHODS = ["GET", "HEAD", "OPTIONS"];

const isPublicPath = (pathname: string) =>
    PUBLIC_PATHS.some((path) => pathname.startsWith(path));

const isAssetPath = (pathname: string) =>
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.startsWith("/robots.txt") ||
    pathname.startsWith("/sitemap.xml");

const getRequiredRoles = (pathname: string) => {
    const match = ROLE_RULES.find((rule) => pathname.startsWith(rule.prefix));
    return match?.roles ?? ["user", "admin"];
};

const withResponseCookies = (source: NextResponse, target: NextResponse) => {
    source.cookies.getAll().forEach((cookie) => {
        target.cookies.set(cookie);
    });
    return target;
};

export async function middleware(request: NextRequest) {
    const { pathname, search } = request.nextUrl;

    if (isAssetPath(pathname)) {
        return NextResponse.next();
    }

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
        return new NextResponse("Supabase configuration missing", { status: 503 });
    }

    const response = NextResponse.next();

    const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
        cookies: {
            getAll: () => request.cookies.getAll(),
            setAll: (cookies) => {
                cookies.forEach((cookie) => response.cookies.set(cookie));
            },
        },
    });

    const existingCsrf = request.cookies.get(CSRF_COOKIE_NAME)?.value;
    const csrfToken = existingCsrf ?? crypto.randomUUID();

    if (!existingCsrf) {
        response.cookies.set(CSRF_COOKIE_NAME, csrfToken, {
            path: "/",
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
            httpOnly: false,
        });
    }

    if (!SAFE_METHODS.includes(request.method)) {
        const headerToken = request.headers.get(CSRF_HEADER_NAME);
        if (!headerToken || headerToken !== csrfToken) {
            const denied = new NextResponse("CSRF validation failed", { status: 403 });
            return withResponseCookies(response, denied);
        }
    }

    const { data: { user } } = await supabase.auth.getUser();

    if (isPublicPath(pathname)) {
        if (user) {
            const redirectUrl = new URL("/", request.url);
            const redirectResponse = NextResponse.redirect(redirectUrl);
            return withResponseCookies(response, redirectResponse);
        }
        return response;
    }

    if (!user) {
        const redirectUrl = new URL("/auth/login", request.url);
        redirectUrl.searchParams.set("redirect", `${pathname}${search}`);
        const redirectResponse = NextResponse.redirect(redirectUrl);
        return withResponseCookies(response, redirectResponse);
    }

    const role = user.app_metadata?.role || user.user_metadata?.role || user.role || "user";
    const allowedRoles = getRequiredRoles(pathname);

    if (!allowedRoles.includes(role)) {
        const redirectUrl = new URL("/auth/login", request.url);
        redirectUrl.searchParams.set("error", "forbidden");
        redirectUrl.searchParams.set("redirect", `${pathname}${search}`);
        const redirectResponse = NextResponse.redirect(redirectUrl);
        return withResponseCookies(response, redirectResponse);
    }

    return response;
}

export const config = {
    matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)"],
};
