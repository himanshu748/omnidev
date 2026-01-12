"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Location {
    latitude: number | null;
    longitude: number | null;
    city: string | null;
    state: string | null;
    country: string | null;
    address: string | null;
}

export default function LocationPage() {
    const [currentLocation, setCurrentLocation] = useState<Location | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResult, setSearchResult] = useState<Location | null>(null);
    const [loading, setLoading] = useState(true);
    const [searching, setSearching] = useState(false);

    useEffect(() => {
        fetchCurrentLocation();
    }, []);

    const fetchCurrentLocation = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://localhost:8000/api/location/current");
            const data = await res.json();
            setCurrentLocation(data);
        } catch {
            console.error("Failed to fetch location");
        } finally {
            setLoading(false);
        }
    };

    const searchLocation = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;

        setSearching(true);
        try {
            const res = await fetch(`http://localhost:8000/api/location/search?query=${encodeURIComponent(searchQuery)}`);
            const data = await res.json();
            setSearchResult(data);
        } catch {
            console.error("Search failed");
        } finally {
            setSearching(false);
        }
    };

    const LocationCard = ({ title, location, icon }: { title: string; location: Location | null; icon: string }) => (
        <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span>{icon}</span> {title}
            </h2>
            {location ? (
                <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="text-xs text-gray-500 mb-1">Latitude</div>
                            <div className="font-mono text-violet-400">{location.latitude?.toFixed(6)}</div>
                        </div>
                        <div>
                            <div className="text-xs text-gray-500 mb-1">Longitude</div>
                            <div className="font-mono text-cyan-400">{location.longitude?.toFixed(6)}</div>
                        </div>
                    </div>
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
                        <a
                            href={`https://www.google.com/maps?q=${location.latitude},${location.longitude}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 mt-2 rounded-lg border border-[--border] text-sm hover:border-violet-500 hover:text-violet-400 transition-all"
                        >
                            🗺️ Open in Google Maps
                        </a>
                    )}
                </div>
            ) : (
                <div className="text-gray-500 text-center py-8">No location data</div>
            )}
        </div>
    );

    return (
        <main className="min-h-screen">
            <div className="animated-bg" />

            <header className="glass-card border-b border-[--border] sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <span className="text-xl">←</span>
                        <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                            OmniDev
                        </span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">📍</span>
                        <span className="font-semibold">Location Services</span>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto px-6 py-8">
                {/* Search Bar */}
                <div className="glass-card p-6 mb-8">
                    <h2 className="text-lg font-semibold mb-4">Search Location</h2>
                    <form onSubmit={searchLocation} className="flex gap-3">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Enter city, address, or place name..."
                            className="flex-1 bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-violet-500 transition-colors"
                        />
                        <button
                            type="submit"
                            disabled={searching || !searchQuery.trim()}
                            className="glow-button text-white px-6 disabled:opacity-50"
                        >
                            {searching ? <div className="spinner" /> : "Search"}
                        </button>
                    </form>
                </div>

                {/* Location Cards */}
                <div className="grid md:grid-cols-2 gap-6">
                    {loading ? (
                        <div className="glass-card p-6 flex items-center justify-center">
                            <div className="spinner" />
                        </div>
                    ) : (
                        <LocationCard title="Your Current Location" location={currentLocation} icon="📍" />
                    )}

                    {searchResult && (
                        <LocationCard title="Search Result" location={searchResult} icon="🔍" />
                    )}
                </div>

                {/* Features Info */}
                <div className="mt-12 grid md:grid-cols-3 gap-4">
                    {[
                        { icon: "🌐", title: "IP Geolocation", desc: "Automatic location detection based on IP address" },
                        { icon: "🔄", title: "Reverse Geocoding", desc: "Convert coordinates to readable addresses" },
                        { icon: "🔍", title: "Location Search", desc: "Search for any place by name" },
                    ].map((feature) => (
                        <div key={feature.title} className="glass-card p-4 text-center">
                            <div className="text-3xl mb-2">{feature.icon}</div>
                            <h3 className="font-medium mb-1">{feature.title}</h3>
                            <p className="text-xs text-gray-400">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </main>
    );
}
