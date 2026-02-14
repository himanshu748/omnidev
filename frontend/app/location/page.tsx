"use client";

import { useState } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type IPResult = {
  ip: string;
  city: string;
  region: string;
  country: string;
  postal?: string;
  latitude: number | null;
  longitude: number | null;
  timezone?: string;
  org?: string;
};

type GeoResult = {
  latitude: number;
  longitude: number;
  display_name: string;
  address: Record<string, string>;
};

type GeocodeEntry = {
  display_name: string;
  latitude: number;
  longitude: number;
  type: string;
  address: Record<string, string>;
};

type MyLocResult = {
  ip: string;
  city: string;
  region: string;
  country: string;
  latitude: number | null;
  longitude: number | null;
};

function openMap(lat: number, lng: number) {
  window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
}

export default function LocationPage() {
  const [activeTab, setActiveTab] = useState<"me" | "ip" | "reverse" | "geocode">("me");

  // My location
  const [myLoc, setMyLoc] = useState<MyLocResult | null>(null);
  const [myLocLoading, setMyLocLoading] = useState(false);

  // IP lookup
  const [ipInput, setIpInput] = useState("");
  const [ipResult, setIpResult] = useState<IPResult | null>(null);
  const [ipLoading, setIpLoading] = useState(false);

  // Reverse geocode
  const [lat, setLat] = useState("40.7128");
  const [lng, setLng] = useState("-74.0060");
  const [reverseResult, setReverseResult] = useState<GeoResult | null>(null);
  const [reverseLoading, setReverseLoading] = useState(false);

  // Geocode
  const [address, setAddress] = useState("");
  const [geocodeResults, setGeocodeResults] = useState<GeocodeEntry[]>([]);
  const [geocodeLoading, setGeocodeLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const clearAll = () => {
    setError(null);
    setMyLoc(null);
    setIpResult(null);
    setReverseResult(null);
    setGeocodeResults([]);
  };

  async function fetchMyLocation() {
    clearAll();
    setMyLocLoading(true);
    try {
      const res = await fetch(api("/api/location/me"));
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Failed"); return; }
      setMyLoc(data);
    } catch { setError("Network error"); }
    finally { setMyLocLoading(false); }
  }

  async function fetchIPLocation(e: React.FormEvent) {
    e.preventDefault();
    clearAll();
    setIpLoading(true);
    try {
      const param = ipInput.trim() ? `?ip=${encodeURIComponent(ipInput.trim())}` : "";
      const res = await fetch(api(`/api/location/ip${param}`));
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Failed"); return; }
      setIpResult(data);
    } catch { setError("Network error"); }
    finally { setIpLoading(false); }
  }

  async function fetchReverseGeocode(e: React.FormEvent) {
    e.preventDefault();
    clearAll();
    setReverseLoading(true);
    try {
      const res = await fetch(api(`/api/location/reverse?lat=${lat}&lng=${lng}`));
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Failed"); return; }
      setReverseResult(data);
    } catch { setError("Network error"); }
    finally { setReverseLoading(false); }
  }

  async function fetchGeocode(e: React.FormEvent) {
    e.preventDefault();
    clearAll();
    setGeocodeLoading(true);
    try {
      const res = await fetch(api(`/api/location/geocode?q=${encodeURIComponent(address)}&limit=5`));
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Failed"); return; }
      setGeocodeResults(data.results ?? []);
    } catch { setError("Network error"); }
    finally { setGeocodeLoading(false); }
  }

  const tabs = [
    { key: "me" as const, label: "🏠 My Location" },
    { key: "ip" as const, label: "🌐 IP Lookup" },
    { key: "reverse" as const, label: "📍 Reverse Geocode" },
    { key: "geocode" as const, label: "🔍 Search Address" },
  ];

  return (
    <FeatureLayout
      title="Location Services"
      description="IP geolocation, forward & reverse geocoding, and public IP detection — all from one dashboard."
      icon="📍"
      endpoints={[
        { method: "GET", path: "/api/location/me" },
        { method: "GET", path: "/api/location/ip" },
        { method: "GET", path: "/api/location/reverse" },
        { method: "GET", path: "/api/location/geocode" },
      ]}
    >
      {/* Tab switcher */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 24 }}>
        {tabs.map(t => (
          <button
            key={t.key}
            className={`modePill ${activeTab === t.key ? "active" : ""}`}
            onClick={() => { setActiveTab(t.key); clearAll(); }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <div className="featureResult featureError" style={{ marginBottom: 16 }}><strong>⚠</strong> {error}</div>}

      {/* MY LOCATION TAB */}
      {activeTab === "me" && (
        <div className="featureCard">
          <h2><span className="cardIcon">🏠</span> Detect My Location</h2>
          <p className="featureCardSubtitle">Detect the server&apos;s public IP and resolve the geographic location.</p>
          <button
            className="featureBtn featureBtnPrimary"
            onClick={fetchMyLocation}
            disabled={myLocLoading}
          >
            {myLocLoading ? <span className="loadingDot">Detecting</span> : "📡 Detect Location"}
          </button>

          {myLoc && (
            <div className="featureResult featureSuccess" style={{ marginTop: 20 }}>
              <div className="resultRow">
                <span className="resultLabel">IP Address</span>
                <span className="resultValue" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{myLoc.ip}</span>
              </div>
              <div className="resultRow">
                <span className="resultLabel">City</span>
                <span className="resultValue">{myLoc.city}</span>
              </div>
              <div className="resultRow">
                <span className="resultLabel">Region</span>
                <span className="resultValue">{myLoc.region}</span>
              </div>
              <div className="resultRow">
                <span className="resultLabel">Country</span>
                <span className="resultValue">{myLoc.country}</span>
              </div>
              {myLoc.latitude != null && (
                <div className="resultRow">
                  <span className="resultLabel">Coordinates</span>
                  <span className="resultValue">{myLoc.latitude}, {myLoc.longitude}</span>
                </div>
              )}
              {myLoc.latitude != null && myLoc.longitude != null && (
                <div className="mapActions">
                  <button className="mapBtn" onClick={() => openMap(myLoc.latitude!, myLoc.longitude!)}>
                    🗺️ Open in Google Maps
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* IP LOOKUP TAB */}
      {activeTab === "ip" && (
        <div className="featureCard">
          <h2><span className="cardIcon">🌐</span> IP Geolocation Lookup</h2>
          <p className="featureCardSubtitle">Lookup location info for any IP address. Leave empty to use your public IP.</p>
          <form className="featureForm" onSubmit={fetchIPLocation}>
            <div>
              <label htmlFor="loc-ip">IP Address</label>
              <input
                id="loc-ip"
                type="text"
                value={ipInput}
                onChange={(e) => setIpInput(e.target.value)}
                placeholder="8.8.8.8 (leave empty for your IP)"
              />
            </div>
            <div className="suggestionChips">
              {["8.8.8.8", "1.1.1.1", "13.107.42.14", ""].map((ip) => (
                <button key={ip || "self"} type="button" className="suggestionChip" onClick={() => setIpInput(ip)}>
                  {ip || "My IP"}
                </button>
              ))}
            </div>
            <button type="submit" className="featureBtn featureBtnPrimary" disabled={ipLoading}>
              {ipLoading ? <span className="loadingDot">Looking up</span> : "🔍 Lookup IP"}
            </button>
          </form>

          {ipResult && (
            <div className="featureResult featureSuccess" style={{ marginTop: 20 }}>
              {([
                ["IP", ipResult.ip, true],
                ["City", ipResult.city, false],
                ["Region", ipResult.region, false],
                ["Country", ipResult.country, false],
                ["Postal", ipResult.postal, false],
                ["Timezone", ipResult.timezone, false],
                ["Org", ipResult.org, false],
              ] as [string, string | undefined, boolean][]).filter(([, v]) => v).map(([label, value, mono]) => (
                <div className="resultRow" key={label}>
                  <span className="resultLabel">{label}</span>
                  <span className="resultValue" style={mono ? { fontFamily: "'JetBrains Mono', monospace" } : undefined}>
                    {value}
                  </span>
                </div>
              ))}
              {ipResult.latitude != null && (
                <div className="resultRow">
                  <span className="resultLabel">Coordinates</span>
                  <span className="resultValue">{ipResult.latitude}, {ipResult.longitude}</span>
                </div>
              )}
              {ipResult.latitude != null && ipResult.longitude != null && (
                <div className="mapActions">
                  <button className="mapBtn" onClick={() => openMap(ipResult.latitude!, ipResult.longitude!)}>
                    🗺️ Open in Google Maps
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* REVERSE GEOCODE TAB */}
      {activeTab === "reverse" && (
        <div className="featureCard">
          <h2><span className="cardIcon">📍</span> Reverse Geocoding</h2>
          <p className="featureCardSubtitle">Convert latitude/longitude coordinates to a human-readable address via OpenStreetMap Nominatim.</p>
          <form className="featureForm" onSubmit={fetchReverseGeocode}>
            <div className="formGrid">
              <div>
                <label htmlFor="loc-lat">Latitude</label>
                <input id="loc-lat" type="text" value={lat} onChange={(e) => setLat(e.target.value)} placeholder="40.7128" />
              </div>
              <div>
                <label htmlFor="loc-lng">Longitude</label>
                <input id="loc-lng" type="text" value={lng} onChange={(e) => setLng(e.target.value)} placeholder="-74.0060" />
              </div>
            </div>
            <div className="suggestionChips">
              {[
                { label: "New York", lat: "40.7128", lng: "-74.0060" },
                { label: "London", lat: "51.5074", lng: "-0.1278" },
                { label: "Tokyo", lat: "35.6762", lng: "139.6503" },
                { label: "Sydney", lat: "-33.8688", lng: "151.2093" },
              ].map(p => (
                <button key={p.label} type="button" className="suggestionChip" onClick={() => { setLat(p.lat); setLng(p.lng); }}>
                  {p.label}
                </button>
              ))}
            </div>
            <button type="submit" className="featureBtn featureBtnPrimary" disabled={reverseLoading}>
              {reverseLoading ? <span className="loadingDot">Resolving</span> : "📍 Reverse Geocode"}
            </button>
          </form>

          {reverseResult && (
            <div className="featureResult featureSuccess" style={{ marginTop: 20 }}>
              <div className="resultRow">
                <span className="resultLabel">Address</span>
                <span className="resultValue">{reverseResult.display_name}</span>
              </div>
              <div className="resultRow">
                <span className="resultLabel">Coordinates</span>
                <span className="resultValue" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                  {reverseResult.latitude}, {reverseResult.longitude}
                </span>
              </div>
              {Object.keys(reverseResult.address).length > 0 && (
                <div className="resultRow" style={{ flexDirection: "column", gap: 6 }}>
                  <span className="resultLabel">Address Details</span>
                  <pre style={{ fontSize: "0.82rem", color: "var(--text-dim)" }}>
                    {JSON.stringify(reverseResult.address, null, 2)}
                  </pre>
                </div>
              )}
              <div className="mapActions">
                <button className="mapBtn" onClick={() => openMap(reverseResult.latitude, reverseResult.longitude)}>
                  🗺️ Open in Google Maps
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* GEOCODE (forward) TAB */}
      {activeTab === "geocode" && (
        <div className="featureCard">
          <h2><span className="cardIcon">🔍</span> Address Search (Forward Geocode)</h2>
          <p className="featureCardSubtitle">Convert a place name or address to geographic coordinates.</p>
          <form className="featureForm" onSubmit={fetchGeocode}>
            <div>
              <label htmlFor="loc-addr">Address or Place Name</label>
              <input
                id="loc-addr"
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. 1600 Pennsylvania Avenue NW, Washington DC"
                required
              />
            </div>
            <div className="suggestionChips">
              {["Times Square, New York", "Eiffel Tower, Paris", "Taj Mahal, India", "Big Ben, London"].map(a => (
                <button key={a} type="button" className="suggestionChip" onClick={() => setAddress(a)}>
                  {a}
                </button>
              ))}
            </div>
            <button type="submit" className="featureBtn featureBtnPrimary" disabled={geocodeLoading}>
              {geocodeLoading ? <span className="loadingDot">Searching</span> : "🔍 Search"}
            </button>
          </form>

          {geocodeResults.length > 0 && (
            <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 12 }}>
              {geocodeResults.map((r, i) => (
                <div key={i} className="featureResult featureSuccess" style={{ marginTop: 0 }}>
                  <div className="resultRow">
                    <span className="resultLabel">Place</span>
                    <span className="resultValue">{r.display_name}</span>
                  </div>
                  <div className="resultRow">
                    <span className="resultLabel">Coordinates</span>
                    <span className="resultValue" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                      {r.latitude}, {r.longitude}
                    </span>
                  </div>
                  <div className="resultRow">
                    <span className="resultLabel">Type</span>
                    <span className="resultValue" style={{ textTransform: "capitalize" }}>{r.type}</span>
                  </div>
                  <div className="mapActions">
                    <button className="mapBtn" onClick={() => openMap(r.latitude, r.longitude)}>
                      🗺️ Google Maps
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </FeatureLayout>
  );
}
