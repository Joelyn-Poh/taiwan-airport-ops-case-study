---
name: Taiwan Airport Ride-Hailing Operations Case Study
description: An auditable operations evidence dossier that traces synthetic airport ride data into a guarded campaign decision.
colors:
  deep-navy-ink: "#131c19"
  layered-navy: "#183b5c"
  menu-state: "#112233"
  rail-rule: "rgba(255,255,255,0.12)"
  dossier-paper: "#f3f4f1"
  cool-paper: "#e8ecec"
  cool-paper-deep: "#dbe1e2"
  exhibit-white: "#fbfcfa"
  muted-slate: "#5e6b73"
  fine-rule: "#cbd1d4"
  section-rule: "#aeb8bd"
  signal-green: "#09bb66"
  signal-green-text: "#067a42"
  signal-green-pale: "#e3f8ed"
  verification-green: "#27734d"
  verification-green-pale: "#dfeee6"
  focus-blue: "#1769aa"
typography:
  base:
    fontSize: "17px"
    compactFontSize: "16px"
    lineHeight: 1.7
  display:
    fontFamily: '"Barlow Condensed", "Noto Sans TC", sans-serif'
    fontSize: "clamp(3.3rem, 6vw, 6rem)"
    fontWeight: 800
    lineHeight: 0.88
    letterSpacing: "-0.025em"
  headline:
    fontFamily: '"Barlow Condensed", "Noto Sans TC", sans-serif'
    fontSize: "clamp(2.25rem, 4vw, 4rem)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-0.025em"
  title:
    fontFamily: '"Barlow Condensed", "Noto Sans TC", sans-serif'
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "0.02em"
  body:
    fontFamily: '"Noto Sans TC", Arial, sans-serif'
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  label:
    fontFamily: '"Roboto Mono", Consolas, monospace'
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
rounded:
  square: "0px"
  circular: "50%"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.25rem"
  2xl: "1.5rem"
  3xl: "2rem"
components:
  primary-action:
    backgroundColor: "{colors.deep-navy-ink}"
    textColor: "{colors.exhibit-white}"
    typography: "{typography.title}"
    rounded: "{rounded.square}"
    padding: "0.7rem 1rem"
    height: "2.9rem"
  primary-action-hover:
    backgroundColor: "{colors.layered-navy}"
    textColor: "{colors.exhibit-white}"
    typography: "{typography.title}"
    rounded: "{rounded.square}"
    padding: "0.7rem 1rem"
  exhibit:
    backgroundColor: "{colors.exhibit-white}"
    textColor: "{colors.deep-navy-ink}"
    rounded: "{rounded.square}"
    padding: "clamp(1.25rem, 2.4vw, 2rem)"
  exhibit-tab:
    backgroundColor: "{colors.deep-navy-ink}"
    textColor: "{colors.exhibit-white}"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
    padding: "0 1.1rem 0 0.7rem"
    height: "1.85rem"
  language-switch-active:
    backgroundColor: "{colors.deep-navy-ink}"
    textColor: "{colors.exhibit-white}"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
    padding: "0.42rem 0.62rem"
  breach-row:
    backgroundColor: "{colors.signal-green-pale}"
    textColor: "{colors.signal-green-text}"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
    padding: "0.4rem 0.7rem"
---

# Design System: Taiwan Airport Ride-Hailing Operations Case Study

## Overview

**Creative North Star: "Operations Evidence Dossier"**

This system makes an operating decision feel earned. Cool-gray dossier paper, deep navy ink, square exhibit tabs, and fine rules organize the page like a reviewed case file; dark verification green confirms evidence, while bright signal green marks breaches, quarantine, overspend, and the final hold decision.

The visual density is analytical rather than decorative. Condensed headlines deliver conclusions, mono labels identify measurements and procedural evidence, and the workhorse sans keeps explanations readable in English and Traditional Chinese. The system explicitly rejects the generic portfolio dashboard: evidence remains sequential, traceable, and visibly tied to the decision.

**Key Characteristics:**

- Three-part dossier shell with a persistent evidence index, central case file, and decision rail.
- Flat paper surfaces separated by fine rules rather than floating dashboard cards.
- Square controls and clipped exhibit tabs with restrained industrial geometry.
- Dark verification green and bright signal green used only to communicate evidence state.
- Responsive evidence navigation, reduced-motion support, and visible keyboard focus.

## Colors

The palette is a cool, low-saturation paper-and-ink system with two tightly controlled semantic accents.

### Primary

- **Deep Navy Ink:** The governing ink for the navigation field, primary action, exhibit tabs, code panel, and strongest rules.
- **Layered Navy:** The interactive navy used for primary-action and navigation hover states and quantitative bars.

### Secondary

- **Verification Green:** Passed checks, retained data, positive lift, and validated evidence.
- **Verification Green Pale:** The restrained background for judgment notes that carry an evidence-backed recommendation.

### Tertiary

- **Bright Signal Green:** Breaches, quarantined records, budget overrun, active exhibit markers, and the final redesign-before-scale stamp.
- **Signal Green Pale:** Breach-row background that exposes risk without overpowering the ledger.

### Neutral

- **Dossier Paper:** Main case-file field behind exhibits.
- **Cool Paper:** Page canvas, disclosure bands, and low-emphasis tracks.
- **Cool Paper Deep:** Denser neutral track used for the budget threshold figure.
- **Exhibit White:** Primary reading surface for exhibits and the decision rail.
- **Muted Slate:** Secondary copy, captions, and labels.
- **Fine Rule:** Repeated dividers and exhibit boundaries.

### Named Rules

**The Evidence-State Rule.** Dark green means verified or passing; bright signal green means breach, quarantine, cost, or stop. Labels, position, and shape reinforce the distinction so color is never the only cue.

**The Navy Authority Rule.** Deep navy owns structure and primary action; it is not a generic accent sprayed across data.

## Typography

**Display Font:** Barlow Condensed (with Noto Sans TC and sans-serif fallbacks)  
**Body Font:** Noto Sans TC (with Arial and sans-serif fallbacks)  
**Label/Mono Font:** Roboto Mono (with Consolas and monospace fallbacks)

**Character:** The condensed face reads like a decisive case-file heading, the sans face preserves clarity across both languages, and the mono face marks measurements, SQL, docket metadata, and procedural evidence.

### Hierarchy

- **Display** (800, fluid 3.3–6rem, 0.88): First-screen operating decision; keep the English measure near 12 characters wide.
- **Headline** (700, fluid 2.25–4rem, 0.98): Exhibit conclusions, balanced and usually capped near 18 characters wide.
- **Title** (700, 1.25rem, 1.05): Rail heads, brands, and compact structural headings; uppercase where the interface already does so.
- **Body** (400, 15px, 1.65): Explanations and evidence narrative, generally limited to 68–70 characters.
- **Label** (400, 0.75rem): Docket values, measurements, SQL metadata, exhibit numbering, and status labels.

### Named Rules

**The Measurement Voice Rule.** Mono is reserved for code, counts, dates, thresholds, and evidence metadata; it does not replace body copy.

**The Decision-First Rule.** Condensed type states the conclusion before the body face explains it.

## Layout

The desktop shell is a bounded three-column grid: a 17rem sticky evidence index, a fluid central case file, and an 18rem sticky decision rail. Exhibits sit in the central paper field with fluid 1.25–2rem padding, a 1.35rem vertical interval, and internal grids that pair narrative with proof rather than making interchangeable dashboard tiles.

At 1260px, the index narrows to 14.5rem and the decision rail disappears. At 860px, the shell becomes one column: a 3.7rem sticky mobile header and a horizontally scrolling evidence navigation replace the desktop index while exhibit subgrids collapse. At 560px, body copy drops to 14px, actions stack, ledgers simplify, and dense plots become single-column reading sequences.

The data-cleaning flow is the signature spatial moment: raw and trusted totals frame a dense narrowing line field, while the quarantine branch exits in bright signal green. On mobile, the flow rotates into a vertical chain without changing its evidence order. Print removes navigation, controls, and the decision rail, leaving flat, break-safe exhibits.

**The Evidence-Order Rule.** Responsive changes may reflow evidence but must not reorder the path from decision to cleaning, experiment, guardrails, budget, SQL, and artifacts.

## Elevation & Depth

The interface is flat by default. Tonal paper changes, 1px rules, filled navy fields, and clipped tabs create hierarchy; existing exhibits do not use drop shadows. A single ambient navy shadow token exists in the stylesheet for restrained lifted treatment, but it is not applied to the current case-file surfaces.

### Shadow Vocabulary

- **Ambient Dossier Shadow** (`0 18px 44px rgba(11, 36, 64, 0.12)`): Existing reserved token; do not apply it to ordinary exhibits or ledger rows.

### Named Rules

**The Flat Evidence Rule.** Evidence rests on paper and rules; it does not float in a stack of generic cards.

## Shapes

The system is overwhelmingly square: exhibits, actions, switches, ledger rows, code panels, and file badges use 0px corners. Exhibit tabs introduce one clipped diagonal edge, and the decision stamp adds a slight one-degree rotation to feel manually reviewed. Circles appear only as compact status markers and pass/breach indicators, never as container language.

**The Square Dossier Rule.** Preserve hard corners and fine borders; rounded pills and soft dashboard cards contradict the case-file form.

## Components

### Primary Action

- **Shape:** Square dossier tab with a compact inline arrow and a minimum 2.9rem height.
- **Color:** Deep navy ink with exhibit-white text; hover shifts to layered navy.
- **Typography:** Condensed, bold, uppercase title treatment.
- **Focus:** Global 3px focus-blue outline with 3px offset.
- **Responsive behavior:** On narrow phones, it stretches to the available width and keeps the arrow at the far edge.

### Language Switch

- **Shape:** Two square mono segments inside one fine navy border.
- **State:** Active language is filled deep navy with white text; the mobile header inverts the active segment to white on navy.
- **Behavior:** JavaScript updates the document language, title, visible language nodes, pressed state, and persisted preference.

### Evidence Navigation

- **Style:** Deep navy rail with fine internal rules, compact line icons, label and sublabel, and mono exhibit numbers.
- **Hover / Active:** Hover uses layered navy; the active item gains a deeper navy field and a 3px bright-green marker.
- **Behavior:** IntersectionObserver updates the active location while scrolling; mobile converts the rail into a horizontal sticky evidence strip.

### Exhibits and Exhibit Tabs

- **Corner Style:** Square exhibit paper with a 1px fine-rule border and stronger navy top edge.
- **Background:** Exhibit white on dossier paper.
- **Tab:** Navy tab anchored to the upper-left edge, with one clipped diagonal end and uppercase condensed labeling.
- **Depth:** Flat; hierarchy comes from paper tone and rules, not shadow.

### Evidence Ledgers

- **Style:** Rule-separated rows, sans labels, mono values, and condensed totals.
- **Pass / Breach:** Dark verification green marks passing status; a pale signal-green row and bright-green values mark a breach.
- **Responsive behavior:** Columns compress at tablet width, then the status moves to a full-width final line on narrow phones.

### Decision Stamp

- **Style:** Two-pixel bright-green border with accessible dark-green text, bold condensed uppercase copy, centered with a slight counter-clockwise rotation.
- **Purpose:** The final operating disposition only; it is not a reusable promotional badge.

### SQL Evidence Panel

- **Style:** Deep navy code field with a ruled toolbar, mono code, and pale blue-green syntax text.
- **Copy control:** Square transparent button with a light border; hover fills with layered navy, and completion appears in a short 180ms toast.
- **Behavior:** Clipboard failure falls back to selecting the code and prompting a manual copy.

## Do's and Don'ts

### Do:

- **Do** lead with the operating decision, then keep every visual claim traceable through the evidence sequence.
- **Do** reserve dark verification green for passed or trusted evidence and bright signal green for risk or stop states.
- **Do** keep exhibits flat, square, ruled, and visibly part of one dossier.
- **Do** preserve keyboard focus, reduced-motion behavior, bilingual type fallbacks, and the mobile evidence order.

### Don't:

- **Don't** turn the case study into a generic portfolio dashboard of rounded, floating cards.
- **Don't** use either green as decorative brand color without evidence-state meaning.
- **Don't** add pill controls, soft gradients, decorative texture, or unsupported input and dialog patterns.
- **Don't** hide the synthetic-data disclosure or separate a conclusion from its underlying repository evidence.
