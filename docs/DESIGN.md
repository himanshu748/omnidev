# 🎨 OmniDev — Design System & Stitch Prototypes

> Frontend design documentation, Stitch screen references, and design tokens.

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Stitch Prototypes](#stitch-prototypes)
3. [Design Tokens](#design-tokens)
4. [Typography](#typography)
5. [Color Palette](#color-palette)
6. [Component Library](#component-library)
7. [Responsive Breakpoints](#responsive-breakpoints)
8. [Animations](#animations)

---

## Design Philosophy

OmniDev follows a **premium dark SaaS** aesthetic — inspired by tools like Linear, Vercel, and Raycast. Key principles:

| Principle | Description |
|-----------|-------------|
| **Dark-first** | Deep navy/black backgrounds reduce eye strain for developers |
| **Glassmorphism** | Semi-transparent cards with backdrop blur create depth |
| **Gradient accents** | Indigo → purple gradients add energy without overwhelming |
| **Monospace for code** | JetBrains Mono for all technical content |
| **Micro-animations** | Subtle motion creates polish without distraction |
| **Consistent spacing** | 8px grid system throughout |

---

## Stitch Prototypes

All UI designs were created in **Google Stitch** and can be accessed from the project:

**Project ID:** `5072531539344186758`  
**Project URL:** [Open in Stitch](https://stitch.google.com/projects/5072531539344186758)

### Screen Index

| # | Screen | Screen ID | Dimensions |
|---|--------|-----------|------------|
| 1 | **Landing Page** | `be0b6d05018747dbbb2cf39c26b8c9ec` | 2560 × 7824 |
| 2 | **Web Scraper Dashboard** | `6bb1251aa33e401a84ece73b6a68308f` | 2560 × 3144 |
| 3 | **DevOps Agent Dashboard** | `bcc0f3477e5b4755a98ca5acc7ea2270` | 2560 × 2880 |
| 4 | **Vision Lab Dashboard** | `4976d0a12a5249ff84d90887c47a2d67` | 2560 × 2734 |
| 5 | **Cloud Storage Manager** | `a08369346c6f44d889716860c7c5eee4` | 2560 × 2478 |
| 6 | **Location Services Hub** | `df86930c88034c4b8b0931719689fabb` | 2560 × 3174 |

### Design Highlights from Stitch

**Landing Page:**
- Full-page layout with 8 sections: Nav → Hero → Features → Code Demo → Testimonials → Pricing → FAQ → Footer
- "Complete Toolset" section header above feature grid
- 3×2 feature card grid with glassmorphism + Material Icons
- Split-layout code demo with syntax-highlighted Python example
- 3-tier pricing cards with gradient border highlight on recommended plan

**Feature Dashboards (Scraper, DevOps, Vision, Storage, Location):**
- Split-panel layout: input form on left, output console on right (DevOps)
- Structured JSON result rendering with syntax highlighting
- Status indicators (green dot = success, red = error)
- Pill-shaped active tab navigation
- Recent operations history (DevOps)
- System notification panel with warnings

---

## Design Tokens

### CSS Custom Properties

```css
:root {
  /* Backgrounds */
  --bg:            #06090f;
  --bg-soft:       #0c1322;
  --bg-card:       rgba(14, 21, 38, 0.65);
  --bg-card-hover: rgba(20, 30, 52, 0.85);

  /* Text */
  --text:          #e8edf6;
  --text-dim:      #8b9bc0;
  --text-muted:    #5c6d94;

  /* Accents */
  --accent:        #6366f1;    /* Indigo */
  --accent-strong: #4f46e5;    /* Deep indigo */
  --accent-soft:   rgba(99, 102, 241, 0.12);
  --accent-glow:   rgba(99, 102, 241, 0.25);
  --accent2:       #06b6d4;    /* Cyan */
  --accent3:       #a78bfa;    /* Purple */

  /* Status */
  --emerald:       #34d399;    /* Success */
  --rose:          #f87171;    /* Error */
  --amber:         #fbbf24;    /* Warning */

  /* Borders & Glass */
  --border:        rgba(42, 62, 102, 0.4);
  --border-hover:  rgba(99, 102, 241, 0.45);
  --glass:         rgba(10, 16, 30, 0.72);
  --glass-strong:  rgba(10, 16, 30, 0.88);

  /* Radius */
  --radius:        16px;
  --radius-sm:     10px;
  --radius-xs:     8px;

  /* Shadows */
  --shadow-glow:   0 0 60px -12px rgba(99, 102, 241, 0.3);
  --shadow-lg:     0 20px 60px -15px rgba(0,0,0,0.5);
}
```

---

## Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Body text | Inter | 400 | 16px (1rem) |
| Headings | Inter | 700–800 | 1.25–3.5rem |
| Code / mono | JetBrains Mono | 400–500 | 0.85–0.9rem |
| Labels | Inter | 600 | 0.72–0.85rem |
| Nav links | Inter | 500 | 0.88rem |

### Heading Scale

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| H1 | `clamp(2.2rem, 5vw, 3.5rem)` | 800 | Hero headlines |
| H2 | `clamp(1.8rem, 4vw, 3rem)` | 700 | Section titles |
| H3 | `1.25rem` | 600 | Card titles |
| H4 | `1rem` | 600 | Sub-sections |

---

## Color Palette

### Primary Palette

| Color | Hex | Usage |
|-------|-----|-------|
| ![#06090f](https://via.placeholder.com/12/06090f/06090f.png) | `#06090f` | Page background |
| ![#0c1322](https://via.placeholder.com/12/0c1322/0c1322.png) | `#0c1322` | Soft background |
| ![#6366f1](https://via.placeholder.com/12/6366f1/6366f1.png) | `#6366f1` | Primary accent |
| ![#4f46e5](https://via.placeholder.com/12/4f46e5/4f46e5.png) | `#4f46e5` | Dark accent |
| ![#a78bfa](https://via.placeholder.com/12/a78bfa/a78bfa.png) | `#a78bfa` | Light purple |

### Status Colors

| Color | Hex | Usage |
|-------|-----|-------|
| ![#34d399](https://via.placeholder.com/12/34d399/34d399.png) | `#34d399` | Success / Online |
| ![#f87171](https://via.placeholder.com/12/f87171/f87171.png) | `#f87171` | Error / Danger |
| ![#fbbf24](https://via.placeholder.com/12/fbbf24/fbbf24.png) | `#fbbf24` | Warning |
| ![#06b6d4](https://via.placeholder.com/12/06b6d4/06b6d4.png) | `#06b6d4` | Info / Cyan |

---

## Component Library

### Cards (Glassmorphism)

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  backdrop-filter: blur(12px);
  transition: all 0.35s ease;
}

.card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-hover);
  transform: translateY(-4px);
  box-shadow: var(--shadow-glow);
}
```

### Buttons

| Variant | Style | Usage |
|---------|-------|-------|
| **Primary** | Indigo gradient fill | Main CTAs |
| **Ghost** | Transparent + border | Secondary actions |
| **Block** | Full-width | Form submits |
| **Pill** | Small, rounded | Quick actions, chips |

### Form Inputs

```css
.input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  color: var(--text);
  padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace;
}
```

### Badges / Pills

```css
.badge {
  display: inline-flex;
  padding: 5px 14px;
  font-size: 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--accent-soft);
  color: var(--accent);
}
```

---

## Responsive Breakpoints

| Breakpoint | Width | Behavior |
|-----------|-------|----------|
| **Mobile** | `< 640px` | Single column, stacked cards |
| **Tablet** | `640–1024px` | 2-column grids |
| **Desktop** | `> 1024px` | Full layout, 3-column grids |

---

## Animations

### Framer Motion Patterns

```tsx
// Page entrance
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}

// Staggered children
variants={{
  visible: { transition: { staggerChildren: 0.1 } }
}}

// Hover lift
whileHover={{ y: -4, transition: { duration: 0.2 } }}
```

### CSS Animations

| Animation | Duration | Usage |
|-----------|----------|-------|
| `pulse` | 4–8s | Background orbs |
| `float` | 6s | Floating elements |
| `fadeIn` | 0.6s | Section entrance |
| `slideUp` | 0.5s | Card reveal |

---

<p align="center">
  <em>For technical architecture, see <a href="ARCHITECTURE.md">ARCHITECTURE.md</a>. For contributing guidelines, see <a href="../CONTRIBUTING.md">CONTRIBUTING.md</a>.</em>
</p>
