import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://omnidev-flame.vercel.app"),
  title: {
    default: "OmniDev - Local AI Developer Workbench",
    template: "%s | OmniDev",
  },
  description:
    "A local-first FastAPI and Next.js workbench for DevOps automation, code generation, scraping, vision, and S3 storage.",
  openGraph: {
    title: "OmniDev - Local AI Developer Workbench",
    description:
      "Local-first FastAPI and Next.js dashboards for AI-assisted developer workflows across cloud, scraping, vision, and storage.",
    url: "https://omnidev-flame.vercel.app",
    siteName: "OmniDev",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "OmniDev - Local AI Developer Workbench",
    description:
      "Local-first FastAPI and Next.js dashboards for AI-assisted developer workflows.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "var(--font-body), system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
