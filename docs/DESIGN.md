---
name: OmniDev
description: A terminal instrument for an offline Mac tool, cool near black, hairline ruled, one signal blue.
colors:
  ground: "#0B0D11"
  ground-veil: "rgba(11,13,17,0.82)"
  panel: "#101319"
  panel-2: "#0E1116"
  rule: "#1C222B"
  rule-soft: "#161B23"
  rule-lift: "#2C3542"
  ink: "#E7EBF1"
  dim: "#98A3B3"
  signal: "#4DA2FF"
  signal-lift: "#6BB4FF"
  signal-ink: "#06101E"
  allow: "#5FD08A"
  refuse: "#FF7B72"
  refuse-edge: "#37232A"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "clamp(40px, 6.6vw, 72px)"
    fontWeight: 680
    lineHeight: 1.02
    letterSpacing: "-0.032em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "clamp(28px, 3.8vw, 40px)"
    fontWeight: 660
    lineHeight: 1.13
    letterSpacing: "-0.028em"
  lede:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  section-prose:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "17.5px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  caption:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "normal"
  data:
    fontFamily: "ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.75
    letterSpacing: "normal"
  readout:
    fontFamily: "ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  meta:
    fontFamily: "ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0.02em"
  label:
    fontFamily: "ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0.08em"
rounded:
  focus: "3px"
  code: "5px"
  chip: "6px"
  action: "9px"
  panel: "12px"
  frame: "14px"
  dot: "50%"
spacing:
  chip-gap: "7px"
  action-gap: "12px"
  row-gap: "14px"
  inset: "16px"
  gutter: "24px"
  block: "64px"
  section: "118px"
components:
  button-primary:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.signal-ink}"
    rounded: "{rounded.action}"
    padding: "13px 22px"
  button-primary-hover:
    backgroundColor: "{colors.signal-lift}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.action}"
    padding: "13px 22px"
  button-ghost-hover:
    backgroundColor: "{colors.panel-2}"
  bar:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    height: "58px"
  bar-compact:
    backgroundColor: "{colors.ground-veil}"
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
  panel-head:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.dim}"
    typography: "{typography.label}"
    padding: "11px 16px"
  frame:
    backgroundColor: "{colors.panel-2}"
    rounded: "{rounded.frame}"
  readout-row:
    textColor: "{colors.ink}"
    typography: "{typography.readout}"
    padding: "11px 16px"
  token-chip:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.chip}"
    padding: "2.5px 8px"
  token-chip-struck:
    textColor: "{colors.refuse}"
  inline-code:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.code}"
    padding: "1px 6px"
---

# Design System: OmniDev

Recorded from the shipped landing page at `site/index.html` (single self-contained file, inline CSS and JS, GSAP vendored at `site/vendor/`). Every value below was read out of that build, not out of a plan.

**This file replaces a retired system.** The previous DESIGN.md described an indigo and purple glassmorphism world (backdrop-blur panels, gradient text, Framer Motion stagger) designed in Google Stitch for a Next.js `frontend/` directory. That directory was deleted in v0.6. None of those tokens survive in either the native SwiftUI app or this page, so none of them are carried here as incumbent. One decision does carry forward: system font stacks only, so nothing fetches a webfont at build time or run time.

## Overview

**Creative North Star: "The Instrument Panel"**

OmniDev runs entirely on your machine, so the page that sells it behaves like a machine you own rather than a brochure for one. The surface is a cool near black chassis with hairline rules, measured readouts and real recorded output. Nothing is illustrated: the screenshots are real screen recordings, the 0.82 retrieval score is a measured number from a recorded probe and the refused command list is transcribed from `agent_tools.py`. The page earns trust by showing instrument readings, not by asserting adjectives.

Density is high and deliberate. Prose is capped by explicit `ch` measures so nothing sprawls, panels stack in a 1000px column and the vertical rhythm is a long 118px between sections so each claim gets a room of its own. Type does the classifying: the system SF stack carries every human sentence, monospace carries every machine value. That split is the loudest signal in the system and it is never blurred.

Depth is structural, never decorative. There is not one `box-shadow` and not one gradient in the build. Surfaces separate by a three step tonal ladder plus 1px hairlines, and the sense of physical layering comes entirely from motion: parallax drift on media frames, staggered reveals, a spec sheet that reads itself out with drawing leaders and counting values. Confirmed rejections: the AI product hero of gradient glow, orb or blob backdrops, four identical feature cards and a second accent hue.

**Key Characteristics:**
- Cool near black ground (#0B0D11) with a three step tonal ladder, no shadows anywhere
- Exactly one accent (signal blue) plus two strictly functional status colors
- System SF for prose, monospace for every machine-produced value
- 1px hairlines in two weights as the only division device
- Motion supplies depth and is applied only by JS under a reduced-motion guard
- Every text block carries an explicit `ch` cap

## Colors

A cool near black instrument palette: one blue that means "this is the signal", two colors that mean only "allowed" and "refused", plus a narrow neutral ladder doing all the structural work.

### Primary
- **Signal Blue** (#4DA2FF): the single accent. It marks exactly four things in the build: the second beat of the headline, the primary download action, a measured retrieval score and the 1px left rule on the model's answer. It is also the focus ring color. It never fills a background wash and never appears in a gradient.
- **Signal Lift** (#6BB4FF): the primary button hover only. One step brighter, same hue.
- **Signal Ink** (#06101E): the text color that sits on Signal Blue. Near black with a blue cast so the button reads as a lit key, not as a white-on-blue web button.

### Secondary
- **Allow Green** (#5FD08A): functional only. It marks a status the product grants: the "runs offline" dot, "0 bytes uploaded" and the free-and-MIT price row. It never appears on anything clickable.
- **Refuse Red** (#FF7B72): functional only. It marks something the product refuses or does not have: the refused `.env` line, every struck command chip, the multiplication sign before each denylist entry and the "account required: none" row.

### Neutral
- **Ground** (#0B0D11): the page floor. Also the `theme-color` meta value, so the browser chrome matches.
- **Ground Veil** (rgba(11,13,17,0.82)): the ground at 82% opacity, used once, as the condensed instrument bar's background behind its blur.
- **Panel** (#101319): a raised surface. The body of every bordered panel and the background of inline code.
- **Panel Inset** (#0E1116): the recessed tone, darker than the surface it sits in. Panel head strips, media frame backing, command chips, ghost button hover.
- **Rule** (#1C222B): structural hairlines. Panel borders, panel head underline, section top rules, chip borders, dotted leaders.
- **Rule Soft** (#161B23): interior hairlines. Rows inside a panel and items inside a prose list, so internal division reads quieter than the panel edge.
- **Rule Lift** (#2C3542): ghost button hover border only.
- **Refuse Edge** (#37232A): the border of a struck command chip, and nothing else. Rule tinted toward Refuse Red so a refused token reads as refused at its edge without a red border shouting at full saturation. A deliberate one off: it is recorded so the system is complete, not so it can spread.
- **Ink** (#E7EBF1): primary text, cool white, never pure #FFF.
- **Dim** (#98A3B3): secondary text, which is most of the prose. Ledes, captions, section prose, labels, footer, readout values.

### Named Rules

**The One Blue Rule.** There is one accent hue in this system. Signal blue is a mark, not a material: it appears as a text color, a 1px rule, a focus ring or a solid key cap. It is never a fill behind content, a gradient stop or a glow. If a new element needs emphasis and blue is already on screen nearby, the answer is hierarchy, not a second accent.

**The Functional Color Rule.** Green means allowed, red means refused or absent. Neither is ever decorative, neither ever brands a surface and neither ever colors a control the user can click. A red token in this system is a factual claim about what the product will not do.

**The Dim Default Rule.** Body prose defaults to Dim (#98A3B3), not Ink. Ink is spent on headings and on the specific words inside a sentence that carry the claim, marked with `<b>`. Emphasis is a step up in lightness, never a color change.

## Typography

**Display Font:** system SF stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`)
**Body Font:** the same system SF stack
**Label/Mono Font:** system monospace stack (`ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace`)

**Character:** One sans face and one mono face, both native to the OS the product ships on, so the page renders in exactly the type the app itself uses and fetches nothing. The pairing is not decorative contrast, it is a classification system: if a human wrote it, it is sans; if the machine produced or measured it, it is mono.

### Hierarchy
- **Display** (680, `clamp(40px, 6.6vw, 72px)`, 1.02, -0.032em): the single h1. Capped at 19ch so it always breaks into two beats.
- **Headline** (660, `clamp(28px, 3.8vw, 40px)`, 1.13, -0.028em): section h2s. Capped at 26ch, each one a complete sentence with a period.
- **Lede** (400, 19px, 1.6): the hero prose line only, set in Dim, capped at 66ch.
- **Section prose** (400, 17.5px, 1.65): the paragraph under a section h2, one step below the lede, set in Dim and capped at 68ch.
- **Body** (400, 16px, 1.65): the document base.
- **List** (400, 15.5px, 1.65): prose list items.
- **Action** (600, 15.5px): button labels, the only sans run at weight 600.
- **Fineprint** (400, 14px, 1.7): the licence and unsigned build note under the hero actions.
- **Caption** (400, 13.5px, 1.7): the line under a panel or figure that says what is real and what is illustrative. Dim, capped at 74ch.
- **Data** (mono, 13.5px, 1.75): the session transcript, set `white-space: pre` so recorded output keeps its columns. Drops to 12.5px below 640px.
- **Readout** (mono, 13px): spec sheet rows. Values carry `font-variant-numeric: tabular-nums` so counting digits do not jitter.
- **Meta** (mono, 12.5px, 0.02em): instrument bar, footer, command chips, denylist entries, inline code.
- **Label** (mono, 11.5px, 0.08em, uppercase): panel head titles and row labels. Panel heads run a hair wider at 0.09em.

### Named Rules

**The Mono Is Measurement Rule.** Monospace is reserved for what the machine produced or is measured by: transcript lines, spec values, file names, denylist patterns, version and license chips, inline code. Prose is never mono and a machine value is never sans. A version number in a sentence is still mono, wrapped in the inline code chip.

**The Two Beat Headline Rule.** The h1 is one sentence in two beats, the second broken onto its own line and set in signal blue ("Ask your Mac anything, and let it do the work. / Fully offline."). The 19ch cap enforces the break at every width. Do not write a three beat h1 and do not color more than the final beat.

**The Optical Weight Rule.** Headings are 680 and 660, not 700 and 600. The variable system face renders those a hair lighter, which is what keeps the tight negative tracking from clotting at 72px. Use the exact weights, not the round ones.

## Layout

A single centered column, `max-width: 1000px`, with a 24px gutter that tightens to 18px below 640px. There is no multi-column page grid and no sidebar: every section is the full column width, and horizontal structure exists only inside panels.

Vertical rhythm is deliberately long. Sections sit 118px apart (84px below 640px), the hero opens with 104px of headroom (64px), the session panel sits 64px under the hero, the closing block takes 96px plus a 56px inset below its top rule and the footer takes 80px plus 72px of trailing space. Inside a panel the rhythm collapses hard: rows are 11px to 13px tall vertically with a universal 16px horizontal inset, so the contrast between page air and instrument density is part of the reading experience.

Measure is capped per block rather than by the container: 19ch on the display, 26ch on headlines, 66ch on the lede, 68ch on section prose, 74ch on captions, 56ch on fineprint. Numbers align right with tabular figures and are separated from their labels by a dotted leader that fills the remaining space.

Responsive behavior is one breakpoint at 640px. It tightens the gutter, shortens the section rhythm, hides two chips in the instrument bar, drops the transcript one size, collapses the three column denylist grid to a single column and moves refusal row labels onto their own line. Everything else scales fluidly through `clamp()` type and `ch` caps.

### Named Rules

**The Single Breakpoint Rule.** One media query, at 640px. Above it the page is fluid by construction: `clamp()` type, `ch` measures and a 1000px cap. Do not add a tablet tier or a desktop tier to solve a problem that fluid type already solves.

**The Measure Cap Rule.** Every text block declares an explicit `ch` cap. No paragraph is allowed to run the full 1000px column. If a new block has no cap, it is not finished.

## Elevation & Depth

This system is flat by construction. There is not one `box-shadow`, one gradient or one glow in the entire build. Depth comes from three sources and only these three: a tonal ladder, hairlines and motion.

The tonal ladder has three steps and one direction. Ground (#0B0D11) is the floor. A raised surface is Panel (#101319), the lightest tone. A recess inside that surface is Panel Inset (#0E1116), darker than the surface it sits in: panel head strips, media frame backing and command chips all read as cut into the surface rather than stacked on it. Because the ladder spans only about 6 points of lightness, the hairline is what actually makes the edge visible.

Motion carries the rest. Media frames drift 46px against the scroll while their content stays uncropped, the hero's three elements leave at three different speeds and the spec sheet reads itself out with drawing leaders and counting numbers. That is the depth budget in full. It is also entirely optional: none of it is required to understand the page.

There is exactly one blur in the build. When the page scrolls past 40px the instrument bar condenses onto `backdrop-filter: saturate(160%) blur(14px)` over the ground at 82% opacity and gains its bottom hairline. This is the one place translucency is sanctioned, because the bar is the only element that overlaps content.

### Named Rules

**The No Shadow Rule.** No `box-shadow`, no gradient, no glow, at any elevation, in any state. A surface that needs to lift uses the tonal ladder plus a hairline. A control that needs to respond uses a 2px translate.

**The Hairline Rule.** Every division is exactly 1px, in one of two weights. Rule (#1C222B) draws structural edges: panel borders, panel head underlines, section top rules, chip borders. Rule Soft (#161B23) draws interior divisions: rows inside a panel, items inside a list. Never a 2px border and never a double rule.

**The One Blur Rule.** `backdrop-filter` appears once, on the condensing instrument bar, because it is the only element that overlaps scrolling content. Do not extend it to panels, cards, images or modals. This is a sanctioned exception, not a material.

**The Motion Is Not Structure Rule.** Every animation is applied by JavaScript inside `gsap.matchMedia('(prefers-reduced-motion: no-preference)')`. Nothing starts hidden in CSS, nothing depends on a script to become visible and the one CSS animation (the blinking caret) sits inside the same media query. A blocked script, a failed vendor file or a reduced-motion preference renders a complete, readable page. Verified on the shipped build: 0 hidden elements under reduced motion. Any new animation follows the same construction or it does not ship.

**The Vendored Script Rule.** GSAP 3.15.0 and ScrollTrigger are vendored first party into `site/vendor/` and loaded by relative path. The page's own copy claims it "loads no third party font, script or analytics", so that claim is a build constraint: any future library is vendored into the repo or not added. No CDN tag, no webfont, no analytics snippet, no embedded iframe.

## Shapes

Everything is a rectangle with a hairline border and a radius that climbs with the element. The ladder is 3px on the focus ring, 5px on inline code, 6px on command chips, 9px on buttons, 12px on panels and 14px on media frames. The only circle in the system is the 6px status dot that precedes "runs offline" and "0 bytes uploaded".

Borders are the form language rather than an afterthought. A panel is defined by its 1px edge rather than its fill, and it clips its contents (`overflow: hidden`) so the head strip's fill meets the rounded corner cleanly. The dotted leader in the spec sheet is the one non-solid line in the system: a 1px dotted bottom border, nudged up 3px to sit on the baseline, with `transform-origin: left` so it can draw itself left to right on entry.

### Named Rules

**The Radius Follows Size Rule.** Radius scales with the element it wraps: 5px to 6px on inline chips and code, 9px on buttons, 12px on panels, 14px on media frames. Never a pill, never a fully rounded control, never a circle except the 6px status dot.

## Components

### Buttons
- **Shape:** softly rounded rectangle (9px radius), 13px by 22px padding, 15px at weight 600 with -0.01em tracking, 9px gap to any inline glyph.
- **Primary:** solid Signal Blue with Signal Ink text. It reads as a lit key on a dark panel. It appears twice on the page (once in the hero and once in the close) and both times it is "Download for macOS".
- **Ghost:** transparent fill with a Rule border and Ink text, used for the secondary "View source" action.
- **Hover / Focus:** both variants lift 2px (`translateY(-2px)`) over 200ms on a `cubic-bezier(.4, 0, .2, 1)`. Primary brightens to Signal Lift, ghost gains a Rule Lift border and a Panel Inset fill. Focus is global: a 2px Signal Blue outline at 3px offset with a 3px radius, never removed.

### Cards / Containers
The panel is the system's only container. Nothing else exists.
- **Corner Style:** 12px radius, contents clipped.
- **Background:** Panel body over a Panel Inset head strip.
- **Shadow Strategy:** none. See Elevation & Depth.
- **Border:** 1px Rule on all sides, plus a 1px Rule under the head strip.
- **Internal Padding:** 16px horizontal inset everywhere, 11px vertical in the head and readout rows, 13px in refusal rows, 20px in the transcript body.
- **Head strip:** an uppercase mono label on the left naming what the panel shows ("local session", "denylist", "specification") and a right-hand value that is either the source file it was transcribed from (`file_guards.py`), a version or a green status dot. The head is a citation line, not a title bar.

### Navigation
A sticky instrument bar, 58px tall, mono at 12.5px. The left mark is the OmniDev terminal-prompt logo at 28px followed by lowercase "omnidev" at weight 600. The right side is a row of measurement chips: version, licence, binary type and a green "runs offline" status dot. It starts fully transparent with no border. Past 40px of scroll it condenses: Ground Veil background, `saturate(160%) blur(14px)` and a Rule bottom border, all over 400ms. Below 640px the licence and binary chips drop out. There are no nav links: the bar reports state, it does not navigate.

### Session Transcript (signature)
The page's opening proof. A panel whose body is monospace at 13.5px with `white-space: pre` so recorded columns hold, containing an indexed-paths line, a prompt line with a blinking signal blue caret, a searching line, scored hits and one red refusal line. The model's answer hangs off a 1px Signal Blue left rule at 13px of padding, with its citation in Dim. On entry it performs: the panel rises, the ask line wipes in via `clipPath: inset(0 100% 0 0)`, the result lines stagger at 100ms, then the answer arrives. Under the panel, a caption states exactly which parts are measured and which are illustrative.

### Spec Readout (signature)
A key, a dotted leader and a right-aligned tabular value per row, 13px mono, rows divided by Rule Soft hairlines. The leader is a flexed 1px dotted border that draws itself from `scaleX: 0` on entry while the row staggers up at 55ms and any numeric value counts from zero over 1.5s on an `expo.out` ease. Values that are refusals or absences take Refuse Red, values that are grants take Allow Green, everything else is Dim.

### Token Chips
Small mono chips (12.5px, 6px radius, 2.5px by 8px padding) on a Panel Inset fill with a Rule border, wrapped in a 7px gap flow. The struck variant colors the text Refuse Red and warms the border toward the red side. They are labels, not controls: nothing here is clickable, so they carry no hover state. Rows are prefixed with an 11.5px uppercase mono label in Dim, 104px wide, which drops onto its own line below 640px.

### Media Frames
A 14px rounded, 1px Rule bordered, Panel Inset backed box holding a full-bleed recording. On entry it un-crops from `inset(6% 6% 6% 6% round 14px)` at 0.4 opacity, then drifts from +46px to -46px against the scroll on a 0.6 scrub. Content is never cropped to buy the effect. Every frame is followed by a caption naming what is real in the recording and what was sped up.

### Inline Code
A 12.5px mono chip inside prose: Panel fill, 1px Rule border, 5px radius, 1px by 6px padding. Used for file paths, file modes and filenames inside sentences.

### Footer
A single wrapping row of 12.5px mono links in Dim, separated by 20px, above a 72px trailing space. Links are undecorated with a transparent bottom border that becomes Rule on hover while the text goes to Ink. There is no footer navigation tree and no social row.

### Brand Mark
The OmniDev mark is the terminal-prompt logo: a blue swirl enclosing a dark disc with `>_`. It is sourced from `macos/Sources/OmniDevMac/Resources/AppIcon.png` and extracted to `site/brand/omnidev-logo.png` with a circular alpha, rendered at 28px in the bar and reused as the apple-touch-icon. It is never replaced with the nested-square "LogoMark" tile geometry.

## Do's and Don'ts

### Do:
- **Do** put every machine-produced value in mono and every human sentence in sans. The split is the system's loudest signal.
- **Do** cite the source in the panel head. If a panel shows transcribed data, its right-hand value names the file or version it came from.
- **Do** caption anything that could be mistaken for a mockup, stating plainly which numbers are measured and which are illustrative.
- **Do** cap every text block with an explicit `ch` measure.
- **Do** use the exact optical weights 680 and 660 for display and headline.
- **Do** apply all motion through JS under `gsap.matchMedia('(prefers-reduced-motion: no-preference)')`, so the page is complete with the script blocked.
- **Do** vendor any new library into the repo and load it by relative path, per The Vendored Script Rule.
- **Do** reserve green for what the product allows and red for what it refuses, on non-interactive elements only.

### Don't:
- **Don't** add a `box-shadow`, a gradient or a glow anywhere, in any state.
- **Don't** introduce a second accent hue. One blue, plus the two functional status colors.
- **Don't** load a webfont, a CDN script, an analytics tag or an embedded iframe. The page states that it loads none, and that statement is a build constraint.
- **Don't** extend `backdrop-filter` beyond the instrument bar. It is sanctioned there because the bar overlaps content, and nowhere else.
- **Don't** hide an element in CSS and reveal it with JS. Ship it visible and animate from a visible state.
- **Don't** set prose in monospace or a measured value in sans.
- **Don't** build the four-identical-feature-card grid, the orb or blob backdrop or the hero glow. These are the specific rejections this world was built against.
- **Don't** crop a recording to make a motion effect work. The frame moves, the content stays whole.
- **Don't** use a color for emphasis inside prose. Step from Dim to Ink instead.
- **Don't** swap the terminal-prompt mark for the nested-square LogoMark tile.
