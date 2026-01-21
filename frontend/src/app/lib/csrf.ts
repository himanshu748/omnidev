export const CSRF_COOKIE_NAME = "omnidev_csrf";
export const CSRF_HEADER_NAME = "x-omnidev-csrf";

export const getCsrfToken = () => {
    if (typeof document === "undefined") {
        return null;
    }

    const match = document.cookie.match(
        new RegExp(`(?:^|; )${CSRF_COOKIE_NAME}=([^;]*)`)
    );

    return match ? decodeURIComponent(match[1]) : null;
};

export const csrfHeaders = () => {
    const token = getCsrfToken();
    const headers: Record<string, string> = {};
    if (token) {
        headers[CSRF_HEADER_NAME] = token;
    }
    return headers;
};
