export const trackEvent = (name: string, payload: Record<string, unknown> = {}) => {
    if (typeof window === "undefined") {
        return;
    }
    const body = JSON.stringify({
        name,
        path: window.location.pathname,
        meta: payload,
    });
    const blob = new Blob([body], { type: "application/json" });
    if (navigator.sendBeacon) {
        navigator.sendBeacon("/analytics/event", blob);
        return;
    }
    fetch("/analytics/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
    }).catch(() => {});
};
