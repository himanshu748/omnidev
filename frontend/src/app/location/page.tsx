"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useSettings } from "../hooks/useSettings";
import { AuthGuard } from "../components/AuthGuard";
import { buildAuthHeaders } from "../lib/api";

interface Location {
    latitude: number | null;
    longitude: number | null;
    city: string | null;
    state: string | null;
    country: string | null;
    address: string | null;
    accuracy?: number;
    source?: "ip" | "browser" | "search";
}

export default function LocationPage() {
    const { settings, isLoaded, saveSettings } = useSettings();
    const [currentLocation, setCurrentLocation] = useState<Location | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResult, setSearchResult] = useState<Location | null>(null);
    const [loading, setLoading] = useState(true);
    const [searching, setSearching] = useState(false);
    const [gettingBrowserLocation, setGettingBrowserLocation] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [tempApiKey, setTempApiKey] = useState("");

    useEffect(() => {
        if (isLoaded) {
            setTempApiKey(settings.googleMapsApiKey);
            if (settings.locationMethod === "manual" && settings.savedLocation) {
                // Use saved manual location
                setCurrentLocation({
                    latitude: settings.savedLocation.latitude,
                    longitude: settings.savedLocation.longitude,
                    city: settings.savedLocation.city,
                    state: settings.savedLocation.state,
                    country: settings.savedLocation.country,
                    address: settings.savedLocation.address,
                    source: "search", // Shows as "Manual" with search icon
                });
                setLoading(false);
            } else if (settings.locationMethod === "browser") {
                getBrowserLocation();
            } else {
                fetchCurrentLocation();
            }
        }
    }, [isLoaded, settings.locationMethod]);

    const saveAsMyLocation = (location: Location) => {
        if (!location.latitude || !location.longitude) return;
        saveSettings({
            locationMethod: "manual",
            savedLocation: {
                latitude: location.latitude,
                longitude: location.longitude,
                city: location.city || "",
                state: location.state || "",
                country: location.country || "",
                address: location.address || "",
            }
        });
        setCurrentLocation({ ...location, source: "search" });
        alert("✅ Location saved! This will be used as your default location.");
    };

    const fetchCurrentLocation = async () => {
        setLoading(true);
        try {
            let url = "/api/location/current";
            if (settings.googleMapsApiKey) {
                url += `?api_key=${encodeURIComponent(settings.googleMapsApiKey)}`;
            }
            const res = await fetch(url, {
                headers: await buildAuthHeaders(),
            });
            const data = await res.json();
            setCurrentLocation({ ...data, source: "ip" });
        } catch {
            console.error("Failed to fetch location");
        } finally {
            setLoading(false);
        }
    };

    const getBrowserLocation = async () => {
        if (!navigator.geolocation) {
            alert("Browser geolocation is not supported on this device");
            fetchCurrentLocation();
            return;
        }

        setGettingBrowserLocation(true);
        setLoading(true);

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude, accuracy } = position.coords;

                // Reverse geocode to get address
                try {
                    let url = `/api/location/reverse?lat=${latitude}&lng=${longitude}`;
                    if (settings.googleMapsApiKey) {
                        url += `&api_key=${encodeURIComponent(settings.googleMapsApiKey)}`;
                    }
                    const res = await fetch(url, {
                        headers: await buildAuthHeaders(),
                    });
                    const data = await res.json();

                    setCurrentLocation({
                        latitude,
                        longitude,
                        city: data.city,
                        state: data.state,
                        country: data.country,
                        address: data.address,
                        accuracy: Math.round(accuracy),
                        source: "browser",
                    });
                } catch {
                    setCurrentLocation({
                        latitude,
                        longitude,
                        city: null,
                        state: null,
                        country: null,
                        address: null,
                        accuracy: Math.round(accuracy),
                        source: "browser",
                    });
                }
                setLoading(false);
                setGettingBrowserLocation(false);
            },
            (error) => {
                console.error("Geolocation error:", error.message);
                alert(`Could not get location: ${error.message}. Falling back to IP-based location.`);
                fetchCurrentLocation();
                setGettingBrowserLocation(false);
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    };

    const searchLocation = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;

        setSearching(true);
        try {
            let url = `/api/location/search?query=${encodeURIComponent(searchQuery)}`;
            if (settings.googleMapsApiKey) {
                url += `&api_key=${encodeURIComponent(settings.googleMapsApiKey)}`;
            }
            const res = await fetch(url, {
                headers: await buildAuthHeaders(),
            });
            const data = await res.json();
            setSearchResult({ ...data, source: "search" });
        } catch {
            console.error("Search failed");
        } finally {
            setSearching(false);
        }
    };

    const saveApiSettings = () => {
        saveSettings({ googleMapsApiKey: tempApiKey });
        setShowSettings(false);
    };

    const LocationCard = ({ title, location, icon, canSave = false }: { title: string; location: Location | null; icon: string; canSave?: boolean }) => (
        <motion.div
            className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-2xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-[#39ff14]/20 flex items-center justify-center text-sm">{icon}</span>
                {title}
                {location?.source && (
                    <span className={`text-xs px-2 py-1 rounded-full ml-auto ${location.source === "browser"
                        ? "bg-[#39ff14]/20 text-[#39ff14] border border-[#39ff14]/30"
                        : location.source === "ip"
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                        }`}>
                        {location.source === "browser" ? "📍 GPS" : location.source === "ip" ? "🌐 IP" : "🔍 Search"}
                    </span>
                )}
            </h2>
            {location ? (
                <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="text-xs text-gray-500 mb-1">Latitude</div>
                            <div className="font-mono text-[#39ff14]">{location.latitude?.toFixed(6)}</div>
                        </div>
                        <div>
                            <div className="text-xs text-gray-500 mb-1">Longitude</div>
                            <div className="font-mono text-[#39ff14]">{location.longitude?.toFixed(6)}</div>
                        </div>
                    </div>
                    {location.accuracy && (
                        <div>
                            <div className="text-xs text-gray-500 mb-1">Accuracy</div>
                            <div className="text-[#39ff14]">± {location.accuracy}m</div>
                        </div>
                    )}
                    <div>
                        <div className="text-xs text-gray-500 mb-1">City</div>
                        <div className="text-white">{location.city || "Unknown"}</div>
                    </div>
                    <div>
                        <div className="text-xs text-gray-500 mb-1">State / Region</div>
                        <div className="text-white">{location.state || "Unknown"}</div>
                    </div>
                    <div>
                        <div className="text-xs text-gray-500 mb-1">Country</div>
                        <div className="text-white">{location.country || "Unknown"}</div>
                    </div>
                    {location.address && (
                        <div>
                            <div className="text-xs text-gray-500 mb-1">Full Address</div>
                            <div className="text-gray-300 text-sm">{location.address}</div>
                        </div>
                    )}
                    {location.latitude && location.longitude && (
                        <div className="flex flex-wrap gap-2 mt-2">
                            <motion.a
                                href={`https://www.google.com/maps?q=${location.latitude},${location.longitude}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[#39ff14]/30 text-sm hover:border-[#39ff14] hover:text-[#39ff14] transition-all"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                🗺️ Open in Maps
                            </motion.a>
                            {canSave && (
                                <motion.button
                                    onClick={() => saveAsMyLocation(location)}
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#39ff14]/10 border border-[#39ff14]/50 text-[#39ff14] text-sm hover:bg-[#39ff14]/20 transition-all"
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    💾 Set as My Location
                                </motion.button>
                            )}
                        </div>
                    )}
                </div>
            ) : (
                <div className="text-gray-500 text-center py-8">No location data</div>
            )}
        </motion.div>
    );

    return (
        <AuthGuard>
            <main className="min-h-screen bg-[#050505] text-white">
                {/* Background Grid */}
                <div className="fixed inset-0 pointer-events-none">
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(57,255,20,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(57,255,20,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
                </div>

                <header className="backdrop-blur-xl bg-black/40 border-b border-[#39ff14]/10 sticky top-0 z-50">
                    <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                            <span className="text-xl">←</span>
                            <span className="text-xl font-bold text-[#39ff14]">
                                OmniDev
                            </span>
                        </Link>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <span className="text-2xl">📍</span>
                                <span className="font-semibold">Location Services</span>
                            </div>
                            <motion.button
                                onClick={() => setShowSettings(true)}
                                className="p-2 rounded-lg border border-[#39ff14]/30 hover:border-[#39ff14] hover:text-[#39ff14] transition-all"
                                title="Settings"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                ⚙️
                            </motion.button>
                        </div>
                    </div>
                </header>

                {/* Settings Modal */}
                <AnimatePresence>
                    {showSettings && (
                        <motion.div
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <motion.div
                                className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-2xl p-6 max-w-md w-full"
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                            >
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-xl font-bold text-[#39ff14]">Location Settings</h2>
                                    <button
                                        onClick={() => setShowSettings(false)}
                                        className="text-gray-400 hover:text-white text-2xl"
                                    >
                                        ×
                                    </button>
                                </div>

                                <div className="space-y-6">
                                    {/* Location Method */}
                                    <div>
                                        <label className="text-sm text-gray-400 mb-2 block">Location Method</label>
                                        <div className="grid grid-cols-2 gap-3">
                                            <motion.button
                                                onClick={() => saveSettings({ locationMethod: "ip" })}
                                                className={`p-3 rounded-lg border text-sm transition-all ${settings.locationMethod === "ip"
                                                    ? "border-[#39ff14] bg-[#39ff14]/20 text-[#39ff14]"
                                                    : "border-[#39ff14]/20 hover:border-[#39ff14]/50"
                                                    }`}
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                            >
                                                🌐 IP-Based
                                            </motion.button>
                                            <motion.button
                                                onClick={() => saveSettings({ locationMethod: "browser" })}
                                                className={`p-3 rounded-lg border text-sm transition-all ${settings.locationMethod === "browser"
                                                    ? "border-[#39ff14] bg-[#39ff14]/20 text-[#39ff14]"
                                                    : "border-[#39ff14]/20 hover:border-[#39ff14]/50"
                                                    }`}
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                            >
                                                📍 GPS (Precise)
                                            </motion.button>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-2">
                                            {settings.locationMethod === "browser"
                                                ? "Uses device GPS for precise location (requires permission)"
                                                : "Uses IP address for approximate location"}
                                        </p>
                                    </div>

                                    {/* Google Maps API Key */}
                                    <div>
                                        <label className="text-sm text-gray-400 mb-2 block">
                                            Google Maps API Key (Optional)
                                        </label>
                                        <input
                                            type="password"
                                            value={tempApiKey}
                                            onChange={(e) => setTempApiKey(e.target.value)}
                                            placeholder="AIza..."
                                            className="w-full bg-[#050505] border border-[#39ff14]/20 rounded-xl px-4 py-3 focus:outline-none focus:border-[#39ff14] transition-colors text-sm"
                                        />
                                        <p className="text-xs text-gray-500 mt-2">
                                            Provides better geocoding results. Get one from{" "}
                                            <a
                                                href="https://console.cloud.google.com/apis/credentials"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-[#39ff14] hover:underline"
                                            >
                                                Google Cloud Console
                                            </a>
                                        </p>
                                    </div>

                                    <div className="flex gap-3">
                                        <motion.button
                                            onClick={saveApiSettings}
                                            className="flex-1 bg-[#39ff14] text-black font-semibold px-6 py-3 rounded-xl"
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                        >
                                            Save Settings
                                        </motion.button>
                                        <motion.button
                                            onClick={() => {
                                                setTempApiKey("");
                                                saveSettings({ googleMapsApiKey: "" });
                                            }}
                                            className="px-4 py-2 rounded-lg border border-[#39ff14]/20 hover:border-red-500 hover:text-red-400 transition-all text-sm"
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                        >
                                            Clear
                                        </motion.button>
                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="max-w-6xl mx-auto px-6 py-8">
                    {/* Action Buttons */}
                    <motion.div
                        className="flex flex-wrap gap-3 mb-6"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <motion.button
                            onClick={getBrowserLocation}
                            disabled={gettingBrowserLocation}
                            className="bg-[#39ff14] text-black font-semibold px-4 py-2 text-sm flex items-center gap-2 disabled:opacity-50 rounded-xl"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            {gettingBrowserLocation ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : "📍"}
                            Use Precise Location
                        </motion.button>
                        <motion.button
                            onClick={fetchCurrentLocation}
                            disabled={loading}
                            className="px-4 py-2 rounded-xl border border-[#39ff14]/30 text-sm hover:border-[#39ff14] hover:text-[#39ff14] transition-all disabled:opacity-50"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            🌐 Use IP Location
                        </motion.button>
                        {settings.googleMapsApiKey && (
                            <span className="px-3 py-2 rounded-full text-xs bg-[#39ff14]/20 text-[#39ff14] border border-[#39ff14]/30 flex items-center gap-1">
                                ✓ Google API Connected
                            </span>
                        )}
                    </motion.div>

                    {/* Search Bar */}
                    <motion.div
                        className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-2xl p-6 mb-8"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span className="w-8 h-8 rounded-lg bg-[#39ff14]/20 flex items-center justify-center text-sm">🔍</span>
                            Search Location
                        </h2>
                        <form onSubmit={searchLocation} className="flex gap-3">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Enter city, address, or place name..."
                                className="flex-1 bg-[#050505] border border-[#39ff14]/20 rounded-xl px-4 py-3 focus:outline-none focus:border-[#39ff14] transition-colors"
                            />
                            <motion.button
                                type="submit"
                                disabled={searching || !searchQuery.trim()}
                                className="bg-[#39ff14] text-black font-semibold px-6 py-3 rounded-xl disabled:opacity-50"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {searching ? <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : "Search"}
                            </motion.button>
                        </form>
                    </motion.div>

                    {/* Location Cards */}
                    <div className="grid md:grid-cols-2 gap-6">
                        {loading ? (
                            <div className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-2xl p-6 flex items-center justify-center">
                                <div className="w-8 h-8 border-2 border-[#39ff14]/30 border-t-[#39ff14] rounded-full animate-spin" />
                            </div>
                        ) : (
                            <LocationCard title="Your Current Location" location={currentLocation} icon="📍" />
                        )}

                        {searchResult && (
                            <LocationCard title="Search Result" location={searchResult} icon="🔍" canSave={true} />
                        )}
                    </div>

                    {/* Features Info */}
                    <motion.div
                        className="mt-12 grid md:grid-cols-4 gap-4"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        {[
                            { icon: "🌐", title: "IP Geolocation", desc: "Automatic location from IP" },
                            { icon: "📍", title: "GPS Location", desc: "Precise browser location" },
                            { icon: "🔄", title: "Reverse Geocoding", desc: "Coordinates to address" },
                            { icon: "🔑", title: "Custom API", desc: "Use your own Google key" },
                        ].map((feature, i) => (
                            <motion.div
                                key={feature.title}
                                className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-xl p-4 text-center"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 + i * 0.1 }}
                                whileHover={{ scale: 1.05, borderColor: "rgba(57, 255, 20, 0.5)" }}
                            >
                                <div className="text-3xl mb-2">{feature.icon}</div>
                                <h3 className="font-medium mb-1">{feature.title}</h3>
                                <p className="text-xs text-gray-400">{feature.desc}</p>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </main>
        </AuthGuard>
    );
}
