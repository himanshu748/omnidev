"use client";

import { useEffect, useRef, type ReactNode } from "react";

/**
 * Fades content up once it enters the viewport.
 * Motion lives entirely in CSS behind prefers-reduced-motion,
 * so this component only toggles a class. A timed fallback keeps
 * content visible even if IntersectionObserver never fires.
 */
export default function Reveal({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const show = () => node.classList.add("lpRevealVisible");

    if (typeof IntersectionObserver === "undefined") {
      show();
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            show();
            observer.disconnect();
          }
        }
      },
      { threshold: 0.01, rootMargin: "0px 0px -8% 0px" },
    );
    observer.observe(node);

    // Already on screen at mount (e.g. deep link, fast scroll).
    const rect = node.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      show();
      observer.disconnect();
    }

    // Last-resort: never leave content hidden.
    const fallback = window.setTimeout(show, 3000);

    return () => {
      observer.disconnect();
      window.clearTimeout(fallback);
    };
  }, []);

  return (
    <div ref={ref} className={`lpReveal ${className}`}>
      {children}
    </div>
  );
}
