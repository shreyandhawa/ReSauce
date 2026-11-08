---
name: ReSauce
description: A local researcher workstation for checking synthetic research records against the documents behind them.
colors:
  shell: "#0f3a44"
  shell-raised: "#17505d"
  shell-ink: "#f1f7f8"
  shell-muted: "#a9c5cb"
  ground: "#f2f5f5"
  surface: "#ffffff"
  surface-2: "#f6f8f8"
  ink: "#1b2326"
  ink-2: "#4c5a61"
  ink-3: "#6b7a80"
  line: "#dbe2e3"
  line-strong: "#b8c5c8"
  accent: "#146a78"
  accent-hover: "#0f5966"
  accent-ink: "#ffffff"
  accent-text: "#11606d"
  accent-soft: "#e1f0f2"
  alert: "#b2390d"
  alert-soft: "#fcefe8"
  alert-line: "#ecc2ab"
  mark-obs: "#e4f1f3"
  mark-obs-line: "#3d8f9c"
  mark-cite: "#b9dde3"
  mark-flash: "#ffd8a8"
  mark-hover: "#9fd2da"
  banner: "#e7ecec"
typography:
  display:
    fontFamily: "Atkinson Hyperlegible Next Variable, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "1.625rem"
    fontWeight: 700
    letterSpacing: "-0.01em"
  headline-id:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
    fontSize: "1.375rem"
    fontWeight: 500
  title:
    fontFamily: "Atkinson Hyperlegible Next Variable, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
  body:
    fontFamily: "Atkinson Hyperlegible Next Variable, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tnum"
  note:
    fontFamily: "Atkinson Hyperlegible Next Variable, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: "Atkinson Hyperlegible Next Variable, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
  section-label:
    fontFamily: "Atkinson Hyperlegible Next Variable, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 700
    letterSpacing: "0.07em"
  mono:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
    fontSize: "0.92em"
    fontWeight: 400
rounded:
  tag: "4px"
  sm: "6px"
  lg: "10px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "14px"
  lg: "20px"
  xl: "28px"
  page-x: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
    height: "38px"
  button-quiet:
    textColor: "{colors.accent-text}"
    rounded: "{rounded.sm}"
    padding: "7px 8px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "7px 10px"
    height: "38px"
  nav-link-active:
    backgroundColor: "{colors.shell-raised}"
    textColor: "{colors.shell-ink}"
  plate:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "14px 16px"
  plate-alert:
    backgroundColor: "{colors.alert-soft}"
---

# Design System: ReSauce

## Overview

**Creative North Star: "The Hospital Signpost"**

ReSauce looks like the wayfinding of a well-run hospital: a deep petrol sign panel down the left, a calm cool-grey corridor behind the work, and white boards where the reading happens. Every status is a fixed sign made of one symbol, one word and at most one colour, so a reviewer who has been at the desk for hours, or watching on a projector, always knows where they are and what is waiting for them.

Density is that of a working tool, not a dashboard: tables, document text and finding plates sit close together, and hierarchy comes from type size, weight and a 68ch reading measure rather than from nested boxes. Colour is scarce on purpose. Teal means "you can act here" or "this is selected"; orange-red means "discrepancy" and never appears without its diamond and its word. Everything else is ink on neutral. The light and dark themes share one token set (`web/src/styles.css`, `:root` plus the dark overrides), toggled by `data-theme` or the system preference.

**Key Characteristics:**
- Petrol sign-panel sidebar with white legends; neutral ground; white work surfaces.
- One action accent, one discrepancy signal, nothing else saturated.
- A fixed status vocabulary (the sign) reused in every table, queue and plate.
- Atkinson Hyperlegible Next for words, IBM Plex Mono for IDs, dates and offsets; tabular figures everywhere.
- One motion token set; every animation names its job and has a reduced-motion form.

## Colors

A cool, low-chroma neutral world with two signal colours that each mean exactly one thing.

### Primary
- **Sign-Panel Petrol** (shell): the sidebar background; the darkest, most fixed thing on screen. Raised petrol (shell-raised) marks the current page. Legends are near-white (shell-ink); inactive links are a muted mist (shell-muted).
- **Action Teal** (accent): primary buttons, the tab underline, progress fills, done-stage dots, checkbox fill, the focus ring. Its darker text form (accent-text) is used for links and quiet buttons; its pale form (accent-soft) for selected rows, chosen decisions, the pressed segment and evidence hover.

### Secondary
- **Discrepancy Signal** (alert): the discrepancy sign, field problems, failed stages, unsigned documents, "no match". Its pale fill (alert-soft) and border (alert-line) build the alert plate and alert callout.

### Neutral
- **Corridor Grey** (ground): page background, tab strip, sticky form foot.
- **Board White** (surface) and **Board Shade** (surface-2): work surfaces; the shade is used for table heads, callouts and hover rows.
- **Ink** (ink, ink-2, ink-3): primary text, secondary text, tertiary metadata and axes.
- **Rule lines** (line, line-strong): hairline dividers and card borders; the strong rule for control borders.
- **Banner grey** (banner): the persistent synthetic-data banner.

### Evidence marks
Four tints mark text in documents: observation (mark-obs with a mark-obs-line underline), cited evidence (mark-cite), hover link (mark-hover) and the one-time evidence-jump flash (mark-flash, warm, used only for that flash).

### Named Rules
**The Accent Means Act Rule.** Teal appears only on things you can press, the thing that is selected, or progress you caused. Never on decoration, headings or charts that are not ReSauce's own method.

**The Never Colour Alone Rule.** Orange-red is always paired with the filled diamond symbol and a word ("Discrepancy", "Discrepancy to review"). A red element without its symbol and word is a bug.

## Typography

**Body Font:** Atkinson Hyperlegible Next (variable, bundled locally), falling back to system-ui.
**Label/Mono Font:** IBM Plex Mono 400 and 500, falling back to ui-monospace.

**Character:** a typeface designed for legibility carries every word, so the screen reads cleanly from the back of a room; the mono face marks anything a reviewer might copy or compare: case IDs, dates, offsets, durations, counts.

### Hierarchy
- **Display** (700, 1.625rem, -0.01em): page titles only.
- **Headline ID** (Plex Mono 500, 1.375rem): the case ID at the top of the case workspace.
- **Title** (700, 1.25rem): section titles, document titles, dialog and empty-state headings, the queue item label.
- **Body** (400, 1rem, 1.5): default text; tabular numbers on.
- **Note** (400, 1.0625rem, 1.75): clinical document text and note entry, held to a 68ch measure. Prose pages use 72ch at 1.65.
- **Label** (700 for signs, 600 for field labels and buttons, 0.875rem): signs, form labels, table text.
- **Section label** (700, 0.8125rem, uppercase, 0.07em): the small headings of the workspace side panel and queue groups.

### Named Rules
**The Measure Not Boxes Rule.** Reading text is held to 68ch (`--measure`); hierarchy is made with size and weight, not extra containers.

**The Copyable Is Mono Rule.** IDs, dates, offsets and counts set in Plex Mono at 0.92em; words never do.

## Layout

A two-column shell: a 236px sticky sidebar and a fluid main column. The main column starts with the synthetic-data banner, then the page (26px 32px padding, max 1360px). The case workspace fills the viewport height: a header with ID, facts and actions; a stage strip; then documents left (fluid) and a side panel right (400px to 540px). The review queue is a list (280px to 380px) beside one focused card.

Spacing is set in literal pixels on a loose 2px rhythm; the recurring steps are 6, 8, 14, 20 and 28px, with 32px page sides.

Responsive: under 1100px the workspace and queue stack into one column and the document scroll caps at 70vh. Under 760px the sidebar becomes a horizontal scrolling strip without icons or footer, grids collapse to one column, and page sides drop to 16px. Print hides the sidebar and banner.

## Elevation & Depth

Flat by default, depth by tone. The petrol shell, corridor ground and white boards make the layers; hairline borders separate surfaces. One shadow token exists and is used only for things that float above the work: the focused queue card and modal dialogs (with a petrol-tinted backdrop). The dark theme uses a deeper version of the same token.

### Named Rules
**The Only Floaters Lift Rule.** A surface carries the shadow only if it sits above the page (the focused review card, a dialog). Cards in the flow stay flat with a border.

## Shapes

Gently rounded and rectangular: 6px on controls, callouts and nav links; 10px on boards (tables, panels, plates, documents, the queue card, dialogs); 4px on small tags and keycaps; full pill only for counts in the sidebar; circles only for stage dots and timeline marks. Borders are 1px hairlines; the form's version blocks use a dashed rule. The authored icon set sits on a 20 by 20 grid with a 1.75 round stroke; the discrepancy diamond is the only filled status icon.

## Components

### Buttons
- **Shape:** gently rounded (6px), 38px minimum height; small variant 30px.
- **Primary:** Action Teal with white text; one primary per view ("Verify" in the workspace).
- **Default:** white with a strong rule border; hover darkens the border.
- **Quiet:** borderless, teal text, for secondary actions in text.
- **Press:** scales to 0.97 on the fast duration; disabled is 55% opacity.

### Signs
The one status vocabulary: a 16px icon plus a bold 0.875rem word, colour limited to ink, teal (reviewed) or orange-red (discrepancy, error). Finding signs: Discrepancy, Needs review, Needs human review, Flag, Out of scope, No alert. Case signs: Not run, No findings, Findings to review, Discrepancy to review, Reviewed, Run failed, Invalid case folder.

### Sign plates (findings)
- **Corner Style:** 10px. **Padding:** 14px 16px. **Border:** hairline.
- **Default:** white board. **Alert:** alert-soft fill with alert-line border.
- Carries the field, record vs document values, a decision tag, and a list of evidence rows; each evidence row quotes its text and jumps to it.

### Inputs / Fields
- **Style:** white, strong rule border, 6px, 38px minimum; note textareas use the Note size.
- **Focus:** border turns teal with a 3px accent-soft halo.
- **Error:** border turns orange-red and a bold orange-red problem line with the warning-triangle icon appears beside the field.

### Navigation
Sidebar links in muted mist on petrol; hover lifts to a faint white wash; the current page gets raised petrol, bold white text and a 3px pale-teal bar on its left edge. A mono pill shows queue counts.

### Choice chips and segmented controls
Decision choices are bordered 6px chips; the checked one turns teal-bordered on accent-soft. Segmented filters share one border; the pressed segment goes accent-soft with teal bold text.

### Document reader and evidence jump (signature)
Documents are tabbed (moving 3px teal underline) and set on a white board at the 68ch measure. Observations are tinted with an underline; absent or uncertain ones are grey-underlined. Choosing evidence on a plate scrolls the text into place, flashes it once in the warm flash tint over the layout duration, then holds it as a steady cited mark with a teal underline.

### Timeline
One fixed Day 0 to +28 scale for every case, in mono 11px ticks; observations are circles in the observation teal, hollow when absent, grey when uncertain; the record value is a dashed ink line. Hovered or focused events grow 1.5x and turn teal.

## Do's and Don'ts

### Do:
- **Do** take every duration and curve from the motion tokens (fast 150ms, base 200ms, slow 250ms, layout 320ms; ease-out to enter, ease-in to leave, ease-move to travel in place; 18ms stagger) and say in a comment what job the motion does (orient, guide attention, show progress, connect cause and effect).
- **Do** give every movement a reduced-motion form that keeps the information as an opacity or colour change, via the token overrides or `lib/motion.js`.
- **Do** use the sign component for any new status, with an icon, a word and at most one colour.
- **Do** keep the synthetic-data banner on every page.
- **Do** set dark-theme values in both the system-preference block and the `data-theme="dark"` block.

### Don't:
- **Don't** show discrepancy, or any status, by colour alone.
- **Don't** use teal for anything that cannot be acted on or is not selected.
- **Don't** add bounce, shake or spring curves; entering eases out, leaving eases in.
- **Don't** add shadows to in-flow cards; use the border.
- **Don't** add KPI tiles or headline numbers; every figure on screen comes from the pipeline, results files or docs.
