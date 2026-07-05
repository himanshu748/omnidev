import type { CSSProperties } from "react";

/**
 * The OmniDev brand mark — a nested "secure enclosure": an outer rounded
 * boundary holding a protected core. One component, used on every surface,
 * so the brand reads identically in the landing nav, the cockpit, and every
 * module page. `currentColor` lets it inherit the surrounding text color.
 */
export function LogoMark({
  size = 26,
  className,
  style,
}: {
  size?: number;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={style}
      aria-hidden="true"
    >
      <rect
        x="2.75"
        y="2.75"
        width="18.5"
        height="18.5"
        rx="5.5"
        stroke="currentColor"
        strokeWidth="1.6"
        opacity="0.85"
      />
      <rect x="8" y="8" width="8" height="8" rx="2.4" fill="currentColor" />
    </svg>
  );
}

/**
 * Full lockup: the mark plus the "OmniDev" wordmark. `tone` controls the
 * accent used for the mark; the wordmark uses the ambient text color.
 */
export function Logo({
  size = 26,
  wordmark = true,
  markColor = "var(--accent, #4DA2FF)",
  className,
}: {
  size?: number;
  wordmark?: boolean;
  markColor?: string;
  className?: string;
}) {
  return (
    <span
      className={className}
      style={{ display: "inline-flex", alignItems: "center", gap: 9 }}
    >
      <LogoMark size={size} style={{ color: markColor }} />
      {wordmark && (
        <span style={{ fontWeight: 700, letterSpacing: "-0.01em", fontSize: size * 0.66 }}>
          OmniDev
        </span>
      )}
    </span>
  );
}
