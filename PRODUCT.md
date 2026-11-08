# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Vite + React (plain JavaScript), built to `web/dist/` and served by a standard-library Python server (`python -m app`). Fonts bundled locally (SIL Open Font Licence) so the demo works offline. Chosen by the user.

## Users
- The project author, presenting a live demo on a laptop and a projector.
- The audience of that demo: clinicians (judge whether the clinical reasoning and evidence are credible), investors (judge whether the idea is worth pursuing), and technical experts (check reproducibility and traceability: that every result can be traced to its source text and re-run).

## Product Purpose
ReSauce is a computational proof of concept. It checks whether clinical research records (onset date and maximum grade of ICANS after CAR-T therapy) agree with the clinical documents behind them, and shows the quoted evidence for every finding. The app shows the measured results against a simpler baseline and runs the frozen pipeline live on one case, stage by stage. Success: the audience can see exactly how a verdict follows from quoted source text, and what the measured results do and do not show.

## Positioning
Every observation and verdict links to the exact quoted text at its offsets in a specific document version; documentation time and event time are kept apart; uncertainty is reported as "needs human review" rather than guessed.

## Operating Context
Live demo, presented by one person, on a laptop screen and a projector (possibly offline). Also used by a technical reviewer reading the results and the methods.

## Capabilities and Constraints
- Synthetic data only. Not a clinical decision tool; results on synthetic data are not clinical validation.
- Every number, label and claim on screen comes from the pipeline, the results files or the docs. No invented statistics, testimonials, logos, users or accuracy claims.
- Reference answers are "intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); not clinician-verified".
- The held-out split is in-repo, not sealed, and "seen". The locked split is not yet evaluated.
- The pipeline is frozen; the app calls it and never changes it.

## Evidence on Hand
`results/report.md`, `results/dev.json`, `results/held_out.json`, the 72 synthetic cases in `data/dev-v1/`, reference answers in `reference/dev-v1/intended/`, `docs/clinical-methods.md`, `docs/evaluation-spec.md`. No users, customers, testimonials, clinician validation or locked-set results exist; none may be shown.

## Product Principles
1. Traceable: every claim can be followed to its quoted source.
2. Honest about limits: disclosures sit next to the numbers they qualify.
3. Uncertainty is shown, never hidden.
4. Measured, not asserted: comparisons only on the same data.

## Accessibility & Inclusion
Keyboard accessible, readable contrast (WCAG AA), light and dark modes, legible on a projector.
