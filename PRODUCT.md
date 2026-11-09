# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Vite + React (plain JavaScript), built to `web/dist/` and served by a standard-library Python server (`python -m app`) on 127.0.0.1 only. Words use the computer's system font; IBM Plex Mono (SIL Open Font Licence) is bundled for IDs, dates and offsets, so it works offline. Chosen by the user.

## Users
- A researcher (or research data manager) on their own computer, checking research records against the documents behind them, often for long sessions.
- Secondary: the project author showing it on a laptop and a projector, and technical reviewers checking reproducibility and traceability.

## Product Purpose
ReSauce is a computational proof of concept and a local researcher workstation. The researcher brings synthetic cases into a workspace folder, runs the frozen pipeline on them, reviews each finding (onset date and maximum grade of ICANS after CAR-T therapy) against the exact source text, records a decision with a note, and exports a report or CSV. Every run and decision goes into an append-only audit log with the pipeline version. The home page is the pipeline itself: imported cases travel through the real stages and resolve into Discrepancy, Needs review or No discrepancy detected. The stored evaluation results are a secondary Results page that shows only the headline percentages, with their caveats. Success: a researcher can go from a case to a recorded, traceable decision without leaving the app, and can see exactly which quoted text each finding rests on.

## Positioning
Every observation and verdict links to the exact quoted text at its offsets in a specific document version; documentation time and event time are kept apart; uncertainty is reported as "needs human review" rather than guessed.

## Operating Context
One person at a desk, for hours, light or dark room; occasionally a projector. Offline, local only; the workspace folder lives inside the project folder in this proof of concept.

## Capabilities and Constraints
- Synthetic data only. Not a clinical decision tool; results on synthetic data are not clinical validation.
- Every number, label and claim on screen comes from the pipeline, the results files or the docs. No invented statistics, testimonials, logos, users or accuracy claims.
- Reference answers are "intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); not clinician-verified".
- The held-out split is in-repo, not sealed, and "seen". The locked split is not yet evaluated.
- The pipeline is frozen; the app calls it and never changes it. Its output is stored as run, never edited; review decisions are stored beside it in the audit log.
- Everything the app writes stays inside the workspace folder; data/ is only read.

## Evidence on Hand
`results/report.md`, `results/dev.json`, `results/held_out.json`, the 72 synthetic cases in `data/dev-v1/` (copied into a workspace on request), reference answers in `reference/dev-v1/intended/` (Validation tab only), `docs/clinical-methods.md`, `docs/evaluation-spec.md`, `docs/freeze.md`. No users, customers, testimonials, clinician validation or locked-set results exist; none may be shown.

## Product Principles
1. Traceable: every claim can be followed to its quoted source.
2. Honest about limits: disclosures sit next to the numbers they qualify.
3. Uncertainty is shown, never hidden.
4. Measured, not asserted: comparisons only on the same data.

## Accessibility & Inclusion
Keyboard accessible (including review shortcuts), readable contrast (WCAG AA), light and dark modes, legible on a projector, prefers-reduced-motion honoured. Discrepancy is never shown by colour alone: symbol + word + colour.
