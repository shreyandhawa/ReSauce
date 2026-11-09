---
name: ReSauce
description: A local researcher workstation where the verification pipeline is the interface; synthetic research records travel through the real stages and resolve into three outcomes.
colors:
  bg: "#ffffff"
  bg-2: "#f3f3f3"
  ink: "#000000"
  ink-2: "#2e2e2e"
  ink-3: "#636363"
  rule: "#000000"
  hair: "#d6d6d6"
  stage: "#000000"
  stage-ink: "#ffffff"
  stage-ink-2: "#a8a8a8"
  stage-ink-3: "#828282"
  stage-line: "#262626"
  stage-line-2: "#4d4d4d"
  red: "#d70015"
  red-vivid: "#ff3b30"
  amber: "#995a00"
  amber-vivid: "#ffb020"
  green: "#00703c"
  green-vivid: "#30d158"
  blue: "#0058e6"
  blue-vivid: "#4a93ff"
typography:
  hero:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.5rem, 0.9rem + 4vw, 4.9rem)"
    fontWeight: 800
    lineHeight: 0.94
    letterSpacing: "-0.04em"
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2rem, 1.2rem + 2.4vw, 3.4rem)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "-0.035em"
  title:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    letterSpacing: "-0.025em"
  body:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.47
    letterSpacing: "-0.006em"
  label:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
  mono:
    fontFamily: "IBM Plex Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "0.9em"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  control: "12px"
  surface: "16px"
  pill: "999px"
spacing:
  side: "clamp(16px, 4vw, 56px)"
  group: "10px"
  section: "28px"
  block: "44px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.bg}"
    rounded: "{rounded.pill}"
    padding: "8px 20px"
    height: "42px"
  button-default:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "8px 20px"
    height: "42px"
  button-invert:
    backgroundColor: "#ffffff"
    textColor: "#000000"
    rounded: "{rounded.pill}"
  input:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 13px"
    height: "44px"
  gate:
    backgroundColor: "{colors.stage}"
    textColor: "{colors.stage-ink-2}"
    rounded: "{rounded.pill}"
  gate-done:
    backgroundColor: "{colors.stage-ink}"
    textColor: "#000000"
  inspector:
    backgroundColor: "{colors.bg}"
    rounded: "{rounded.surface}"
---

# Design System: ReSauce

## Overview

**Creative North Star: "The pipeline is the application."**

The home page is a black stage on which every imported case is a mark. The marks fan into four real stages (Load, Extraction, Timeline, Rules engine), and each one resolves into one of three destinations. Discrepancies branch off into a red network under a turning beacon; uncertain or out-of-scope cases branch into an amber network; cases with no discrepancy converge on a grounded plug and socket. Everything else on the site is set in the same voice: jet black and pure white, bold system type, strong rules, and very few colours, each with exactly one meaning.

The look follows Apple's interface principles (the `apple-design` skill): the platform's system font, size-specific tracking, translucent chrome over content, critically damped springs, motion that starts where it was interrupted, and reduced-motion forms that keep the information. It is not a dashboard. There are no card grids, KPI tiles or pastel tints, and numbers stay in the background until the researcher asks for them.

**Key characteristics:**
- Jet black and pure white as the main pair; a full-bleed black stage in both themes.
- Four accents, one meaning each, always paired with a shape and a word.
- Large, heavy display type with tight tracking; hierarchy from size and weight, separation from 2px black rules and hairlines.
- Motion that reports real events and is paced for viewing, never invented.

## Colors

### The main pair
- **Jet Black** (`ink`, `stage`, `rule`): text, primary buttons, rules, and the stage. In the dark theme the page itself is black and white rules frame the stage.
- **Pure White** (`bg`, `stage-ink`): the page, inverted buttons on black, and finished stages on the stage.
- **Greys** (`ink-2`, `ink-3`, `hair`, `stage-ink-2`, `stage-ink-3`, `stage-line*`): secondary text, metadata, hairlines and idle paths. All text greys meet WCAG AA on their ground.

### Accents (each has a white-ground form and a vivid black-ground form)
- **Signal Red** (`red` / `red-vivid`): discrepancy only. The ◆ mark, the red branch and network, the beacon, the discrepancy sign, form problems and "differs from stored run".
- **Vivid Amber** (`amber` / `amber-vivid`): needs review only. The ▲ mark and the amber branch and network. (The open-review dot in the navigation is review state, so it is white ink.)
- **Vivid Green** (`green` / `green-vivid`): no discrepancy detected only. The ● mark, the converging wires and the seated socket.
- **Electric Blue** (`blue` / `blue-vivid`, `focus`): focus rings, the traced path of the selected record, the selection ring, and linked hover in documents.

### Black and white islands
Components inside `.on-dark` (top bar, stage, the case's mini pipeline, the phone menu) and `.on-light` (the stage tooltip) pick up the matching token set automatically, so a sign on black uses the vivid accent and a sign on white uses the darker one.

### Named rules
**The One Meaning Rule.** Red is discrepancy, amber is needs review, green is no discrepancy detected, blue is focus and selection. Nothing else is coloured. Review state (open, reviewed) is the reviewer's to-do list, not a finding, so it is set in ink.

**The Never Colour Alone Rule.** Every status is a drawn shape + a word + at most one colour: ◆ Discrepancy, ▲ Needs review, ● No discrepancy detected, ○ Not verified yet, ✕ Could not run.

## Typography

**Words:** the system font (SF Pro on Apple platforms, Segoe UI on Windows), which already carries optical sizing and tracking tables. **Data:** IBM Plex Mono (bundled, SIL OFL) for case IDs, dates, offsets, durations and counts, with tabular figures.

### Hierarchy
- **Hero** (800, up to 4.9rem, 0.94, −0.04em): the pipeline page's one statement.
- **Display** (800, up to 3.4rem, −0.035em): page titles, the import sheet, Results splits.
- **Percentage** (800, up to 5.4rem, −0.04em, tabular): Results only.
- **Title** (800, 1.25–1.5rem, −0.02em): section titles, destinations on the stage, the inspector's sections.
- **Body** (400, 1.0625rem, 1.47): default text.
- **Label** (650–700, 0.8125–0.9375rem): buttons, signs, table heads, field labels.

**Rule:** tracking never goes below −0.04em; small text is tracked at 0 or slightly positive.

## Layout

- **Top bar:** a full-width translucent black bar (blur and saturate) with the logo and wordmark on the left, the five destinations in the centre (Pipeline, Review, Audit, Results, About) with an indicator that travels between them, and **Import data** plus the theme switch on the right. It sits on the slim, permanent synthetic-data line. There is no sidebar.
- **Pipeline:** a compact two-column hero (statement left; lede and the one primary action right), then the full-bleed black stage with its toolbar (status in words; filters; Numbers; Network/List), then a ruled legend. Under 760px the stage turns vertical: the same flow runs top to bottom.
- **Pages:** max 1360px with `side` padding, a heavy title above a 2px black rule, and content separated by rules rather than boxes.
- **Inspector:** a parallel sheet beside the stage (no scrim; the stage stays usable); a draggable bottom sheet on phones.

## Elevation and depth

Flat by default. Depth comes from the black stage against white, the translucent bar, and the few things that float: the inspector, the import sheet, dialogs and the toast. Each declares elevation once: a soft offset shadow in light mode; a 1px white ring in dark mode, where a shadow cannot show.

## Shapes

12px on inputs and wells, 16px on floating surfaces and documents, pills on buttons, segmented controls and chips. On the stage: pill-shaped gates, diamond, triangle and circle marks, and an original logo, socket and beacon drawn as SVG. Icons are authored on a 20×20 grid with a 1.75 round stroke; the outcome shapes are filled.

## Components

- **Gate:** a stage pill. Idle: grey outline. Active: white outline while records are inside it. Done: solid white with black text. A bar inside fills with the share of records that have passed. A ✕ badge marks a stage where a record stopped.
- **Mark:** one case. Input marks are white while waiting and hollow once they have left. Destination marks are filled while their findings are open and outlined once all are decided. A small dot means a clean case still carries flags.
- **Beacon:** a red lamp with a slow turning sweep (one turn per 2.6s, no strobe) while any discrepancy is undecided; it is still once all are decided, or when paused.
- **Socket:** the grounded endpoint. Green wires converge on a plug that seats when the run completes.
- **Inspector:** a case's outcome, its two fields (record vs documents), its path with measured times, and its findings with quoted evidence; or a destination's meaning, finding types and cases.
- **Buttons:** primary black pills, default outlined pills that invert on hover, and white pills on black. All scale to 0.97 when pressed.

## Motion

Every animation names its job in a comment (feedback, orient, show progress, connect cause and effect, prevent a jarring change, explanation, delight).

- **Tokens:** fast 150ms, base 220ms, slow 300ms, layout 420ms. `--ease-out` (0.23, 1, 0.32, 1) to enter and leave; `--ease-in-out` (0.77, 0, 0.175, 1) to move on screen; `--ease-drawer` for sheets. Never ease-in on UI.
- **Springs:** `lib/spring.js` turns Apple's damping and response into CSS `linear()` curves (ui 1.0/0.3, move 1.0/0.42, sheet 0.86/0.36). Zoom and pan use an interruptible rAF spring.
- **The authored moment, the run:** records launch from the input, travel each segment on a canvas signal with a speed trail, and land in their destination. The display is paced for viewing and a record never moves before its real stage result exists.
- **Arrival and landing:** imported records arrive with a stagger and their paths draw in. On the first visit the hero rises and the stage opens.
- **Elsewhere:** the inspector materialises with blur and offset, and a mark flies from the stage into it. Page changes cross-fade, the nav indicator glides, the Numbers layer slides in, and Results bars fill once.
- **Reduced motion:** nothing travels or scales. Steps become short fades, the beacon is a static lamp, and the run is announced in text.
- **The one exception:** a record landing in its destination uses a slightly underdamped spring (damping 0.84), because it arrives with momentum. Nothing else overshoots.

## Do's and Don'ts

### Do
- Draw only real things on the stage: real cases, real stages, real outcomes. Where the data says nothing (links between records, a folder before import), draw nothing and say so on the About page.
- Keep numbers behind **Numbers**, hover and the inspector. Words and shapes carry the default view.
- Put every new status into the shape + word + colour vocabulary.
- Set dark values in both the system-preference block and the `data-theme="dark"` block.

### Don't
- Don't add card grids, KPI tiles, gradient text, decorative glow or pastel tints.
- Don't use a colour for a second meaning, or show any status by colour alone.
- Don't use coloured side stripes on lists, plates or callouts; the sign carries the meaning.
- Don't animate keyboard-triggered actions beyond a short ease-out, and never with ease-in.
