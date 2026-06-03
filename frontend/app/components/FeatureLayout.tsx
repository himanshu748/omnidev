"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { API_BASE, isHostedWithoutApiConfig } from "@/lib/api";

const FEATURE_LINKS = [
  { label: "DevOps Agent", href: "/devops", emoji: "🤖" },
  { label: "Code Gen", href: "/codegen", emoji: "⚡" },
  { label: "Web Scraper", href: "/scraper", emoji: "🕷️" },
  { label: "Vision Lab", href: "/vision", emoji: "🖼️" },
  { label: "Cloud Storage", href: "/storage", emoji: "📦" },
  { label: "Location", href: "/location", emoji: "📍" },
];

type EndpointInfo = {
  method: "GET" | "POST" | "DELETE";
  path: string;
};

export default function FeatureLayout({
  children,
  title,
  description,
  icon,
  endpoints,
}: {
  children: React.ReactNode;
  title: string;
  description: string;
  icon?: string;
  endpoints?: EndpointInfo[];
}) {
  const pathname = usePathname();
  const [showApiNotice, setShowApiNotice] = useState(false);

  useEffect(() => {
    setShowApiNotice(isHostedWithoutApiConfig());
  }, []);

  return (
    <div className="featureApp">
      <header className="featureHeader">
        <div className="featureHeaderInner">
          <Link href="/" className="featureLogo">
            Omni<span style={{ color: "var(--accent)" }}>Dev</span>
          </Link>
          <nav className="featureNav">
            {FEATURE_LINKS.map(({ href, label, emoji }) => (
              <Link
                key={href}
                href={href}
                className={`featureNavLink${pathname === href ? " active" : ""}`}
              >
                <span aria-hidden>{emoji}</span> {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="featureMain">
        <div className="featurePageHead">
          {icon && <div className="featurePageIcon">{icon}</div>}
          <h1 className="featureTitle">{title}</h1>
          <p className="featureDesc">{description}</p>
          {showApiNotice && (
            <div className="featureApiNotice" role="status">
              <span className="statusDot statusError" />
              <span>Backend API not configured for this hosted frontend.</span>
              <code>{API_BASE}</code>
            </div>
          )}
          {endpoints && endpoints.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 14 }}>
              {endpoints.map((ep) => (
                <span key={`${ep.method}-${ep.path}`} className="featureEndpoint">
                  <span className={`featureEndpointMethod ${ep.method.toLowerCase()}`}>
                    {ep.method}
                  </span>
                  {ep.path}
                </span>
              ))}
            </div>
          )}
        </div>
        {children}
      </main>
    </div>
  );
}
