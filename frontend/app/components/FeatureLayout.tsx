"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Code2, Database, Eye, Globe, TerminalSquare } from "lucide-react";
import { API_BASE, isHostedWithoutApiConfig } from "@/lib/api";
import { Logo } from "@/app/components/Logo";

const FEATURE_LINKS = [
  { label: "DevOps Agent", href: "/devops", icon: TerminalSquare },
  { label: "Code Gen", href: "/codegen", icon: Code2 },
  { label: "Web Scraper", href: "/scraper", icon: Globe },
  { label: "Vision Lab", href: "/vision", icon: Eye },
  { label: "Cloud Storage", href: "/storage", icon: Database },
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
          <Link href="/" className="featureLogo" aria-label="OmniDev home">
            <Logo size={24} />
          </Link>
          <nav className="featureNav">
            {FEATURE_LINKS.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={`featureNavLink${pathname === href ? " active" : ""}`}
              >
                <Icon size={15} aria-hidden="true" /> {label}
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
