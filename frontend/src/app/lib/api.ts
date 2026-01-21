import { createClient } from "./supabase";
import { csrfHeaders } from "./csrf";

const SETTINGS_KEY = "omnidev_settings";

const getStoredSettings = () => {
    if (typeof window === "undefined") {
        return null;
    }
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) {
        return null;
    }
    try {
        return JSON.parse(raw) as { apiAccessKey?: string };
    } catch {
        return null;
    }
};

export const buildAuthHeaders = async (includeApiKey = true) => {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    const headers: Record<string, string> = {
        ...csrfHeaders(),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    if (includeApiKey) {
        const settings = getStoredSettings();
        if (settings?.apiAccessKey) {
            headers["X-API-Key"] = settings.apiAccessKey;
        }
    }

    return headers;
};
