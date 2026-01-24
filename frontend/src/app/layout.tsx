import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import "./theme.css";
import { AuthProvider } from "./context/AuthContext";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "OmniDev v1.0 | AI-Powered Developer Platform",
  description: "All-in-one AI developer platform with GPT-5 Mini, Vision AI, DevOps automation, and browser scraping",
  keywords: ["AI", "developer tools", "GPT-5", "DevOps", "web scraping", "cloud automation"],
  authors: [{ name: "Himanshu Kumar" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${outfit.variable} ${jetbrainsMono.variable}`}>
      <body className="font-outfit antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
