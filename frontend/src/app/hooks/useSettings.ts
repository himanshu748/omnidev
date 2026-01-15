"use client";

import { useState, useSyncExternalStore } from "react";

export interface AppSettings {
    // AI Configuration
    openaiApiKey: string;
    // AWS Configuration
    awsAccessKeyId: string;
    awsSecretAccessKey: string;
    awsRegion: string;
    // Location Configuration
    googleMapsApiKey: string;
    locationMethod: "ip" | "browser" | "manual";
    savedLocation: {
        latitude: number;
        longitude: number;
        city: string;
        state: string;
        country: string;
        address: string;
    } | null;
}

const DEFAULT_SETTINGS: AppSettings = {
    openaiApiKey: "",
    awsAccessKeyId: "",
    awsSecretAccessKey: "",
    awsRegion: "ap-south-1",
    googleMapsApiKey: "",
    locationMethod: "ip",
    savedLocation: null,
};

const SETTINGS_KEY = "omnidev_settings";

// Helper to load settings from localStorage
function getStoredSettings(): AppSettings {
    if (typeof window === "undefined") return DEFAULT_SETTINGS;
    try {
        const stored = localStorage.getItem(SETTINGS_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            return { ...DEFAULT_SETTINGS, ...parsed };
        }
    } catch (e) {
        console.error("Failed to load settings:", e);
    }
    return DEFAULT_SETTINGS;
}

// Check if we're on the client
function useIsClient(): boolean {
    return useSyncExternalStore(
        () => () => { },
        () => true,
        () => false
    );
}

export function useSettings() {
    const isClient = useIsClient();
    const [settings, setSettings] = useState<AppSettings>(() => getStoredSettings());

    // Save settings to localStorage
    const saveSettings = (newSettings: Partial<AppSettings>) => {
        const updated = { ...settings, ...newSettings };
        setSettings(updated);
        try {
            localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
        } catch (e) {
            console.error("Failed to save settings:", e);
        }
    };

    // Clear all settings
    const clearSettings = () => {
        setSettings(DEFAULT_SETTINGS);
        try {
            localStorage.removeItem(SETTINGS_KEY);
        } catch (e) {
            console.error("Failed to clear settings:", e);
        }
    };

    // Check if services are configured
    const isAiConfigured = Boolean(settings.openaiApiKey);
    const isAwsConfigured = Boolean(settings.awsAccessKeyId && settings.awsSecretAccessKey);
    const isLocationConfigured = Boolean(settings.googleMapsApiKey);

    return {
        settings,
        isLoaded: isClient,
        saveSettings,
        clearSettings,
        isAiConfigured,
        isAwsConfigured,
        isLocationConfigured,
    };
}
