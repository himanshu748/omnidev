# 🎨 Design System

> OmniDev's visual design is built on a premium dark theme with glassmorphism, micro-animations, and offline-safe system font stacks — designed in [Stitch by Google](https://stitch.withgoogle.com) and adapted for local-first builds.

<br />

## Stitch Project

**Project ID:** `5072531539344186758`  
**Title:** OmniDev - AI Developer Platform

### Generated Screens

| # | Screen | Screen ID | Resolution |
|---|--------|-----------|------------|
| 1 | **Landing Page** — Hero, features, code demo, proof, runbook | `be0b6d05018747dbbb2cf39c26b8c9ec` | 2560×7824 |
| 2 | **Web Scraper Dashboard** — URL input, modes, results | `6bb1251aa33e401a84ece73b6a68308f` | 2560×3144 |
| 3 | **DevOps Agent Dashboard** — NLU command, suggestions | `bcc0f3477e5b4755a98ca5acc7ea2270` | 2560×2880 |
| 4 | **Vision Lab Dashboard** — Upload, analysis modes | `4976d0a12a5249ff84d90887c47a2d67` | 2560×2734 |
| 5 | **Cloud Storage Manager** — Bucket browser, upload | `a08369346c6f44d889716860c7c5eee4` | 2560×2478 |

<br />

## Typography

### Primary: System Sans

```
Font stack: Inter, Segoe UI, system-ui, sans-serif
Weights: Browser/system dependent
Usage: All headings, body text, navigation, buttons, labels
```

**Why a system stack?** OmniDev should build and run offline without fetching fonts at build time. The stack keeps the interface crisp while avoiding a hidden network dependency. (The Next.js web frontend these screens were designed for was later removed in favor of the native SwiftUI app, which inherits this visual language.)

### Monospace: System Mono

```
Font stack: SFMono-Regular, Cascadia Code, Liberation Mono, ui-monospace, monospace
Usage: Code blocks, API endpoints, JSON responses, terminal output, technical values
```

### Font Scale

| Element | Size | Weight | Tracking |
|---------|------|--------|----------|
| Hero Headline | `clamp(2.8rem, 6vw, 4.5rem)` | 700 | `-0.03em` |
| Section Title | `clamp(1.8rem, 4vw, 3rem)` | 700 | `-0.02em` |
| Section Lead | `1.05rem` | 400 | normal |
| Card Title | `1.2rem` | 600 | normal |
| Body Text | `0.95rem` | 400 | normal |
| Label | `0.72rem` | 600 | `0.14em` |
| Code/Mono | `0.85rem` | 400 | normal |

<br />

## Color Palette

### Core Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#06090f` | Page background |
| `--bg-soft` | `#0c1322` | Elevated surfaces |
| `--bg-card` | `rgba(14, 21, 38, 0.65)` | Card backgrounds |
| `--accent` | `#6366f1` | Primary indigo |
| `--accent-strong` | `#4f46e5` | Hover/active indigo |
| `--accent3` | `#a78bfa` | Secondary purple |
| `--text` | `#e8edf6` | Primary text |
| `--text-dim` | `#8b9bc0` | Secondary text |
| `--text-muted` | `#5c6d94` | Muted/placeholder |

### Stitch Reference Colors

| Hex | Name | Context |
|-----|------|---------|
| `#06090f` | Deep Navy | Background |
| `#0f111a` | Card Navy | Elevated glass panels |
| `#2d2b55` | Code Purple | Code block gradient start |
| `#6567f1` | Primary Indigo | Buttons, accents, focus rings |
| `#a78bfa` | Soft Purple | Gradient endpoints, highlights |

### Gradients

```css
/* Hero text gradient */
background: linear-gradient(to right, #a78bfa, #6567f1);

/* Code block background */
background: linear-gradient(135deg, #2d2b55 0%, #06090f 100%);

/* Button gradient */
background: linear-gradient(135deg, #6366f1, #4f46e5);
```

<br />

## Glassmorphism

### Glass Panel (Cards)

```css
.glass-panel {
  background: rgba(16, 17, 34, 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

### Glass Navigation

```css
.glass-nav {
  background: rgba(6, 9, 15, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
```

### Input Glass

```css
.input-glass {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.input-glass:focus {
  border-color: #6467f2;
  box-shadow: 0 0 0 2px rgba(100, 103, 242, 0.2);
}
```

<br />

## Components

### Section Label (Badge)

```css
.sectionLabel {
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  border: 1px solid rgba(99, 102, 241, 0.25);
  background: rgba(99, 102, 241, 0.06);
  border-radius: 999px;
  padding: 6px 16px;
}
```

### Buttons

| Class | Style |
|-------|-------|
| `.btnPrimary` | Indigo gradient + glow shadow |
| `.btnGhost` | Transparent + border + blur |
| `.btnBlock` | Full-width variant |

### Feature Cards

- Glassmorphism background with 1px white/8% border
- Emoji icon in colored background pill
- `translateY(-6px)` + glow on hover
- `transition: 0.35s cubic-bezier(0.4, 0, 0.2, 1)`

<br />

## Animations

### Framer Motion

All page sections use stagger reveal animations:

```tsx
const stagger = {
  hidden: { opacity: 0 },
  visible: { transition: { staggerChildren: 0.12 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
};
```

### CSS Animations

- **Background orbs**: `animate-blob` (infinite, 7s)
- **Hover lifts**: `translateY(-2px)` to `translateY(-6px)`
- **Focus rings**: `box-shadow` transition on inputs
- **Gradient shifts**: Animated gradient on hero text

<br />

## Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| `< 640px` | Single column, stacked layout |
| `640px–1024px` | 2-column grids, compact nav |
| `> 1024px` | Full 3-column grids, wide cards |

All sizes use `clamp()` and `min()` for fluid scaling.
