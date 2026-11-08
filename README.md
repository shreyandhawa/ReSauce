# ReSauce

ReSauce is a computational proof of concept. It checks whether a clinical research record agrees with the medical documents behind it, and shows the exact quoted text for every finding. The first focus is ICANS (immune effector cell-associated neurotoxicity syndrome), a neurological complication that can follow CAR-T cell therapy: for each case, ReSauce checks the record's **ICANS onset date** and **maximum grade** against the clinical notes.

> **Important:** ReSauce works only with synthetic (made-up) data. It is a research proof of concept, not a medical device and not a clinical decision tool. Results on synthetic data are not clinical validation.

## What it is, and what it is not

- **It is** a deterministic pipeline (fixed rules, no machine learning) that reads synthetic clinical notes and a synthetic research record, and reports *potential* discrepancies for a person to review, each with its quoted evidence.
- **It is** measured against a simpler method (Baseline A) on the same cases, with the same scoring.
- **It is not** clinically validated. The reference answers it is scored against are not clinician-verified.
- **It does not** use any real patient data, and must never be given any.

## How it works

1. **Load** a case: every version of every clinical document, every version of the research record, and the observation window (Day 0 = infusion, to Day +28).
2. **Extract** observations from the text (ICE scores, level of consciousness, seizures, motor and raised-pressure signs, symptoms, competing causes, "could not be assessed" statements). Each keeps its exact quote, its position in the document, whether it is present, absent or uncertain, and its event time.
3. **Reconstruct the timeline**, keeping the time an event happened apart from the time it was written down, and applying signed/unsigned and superseded document versions.
4. **Compare** the record's onset date and maximum grade with what the documents support (ASTCT grading, written out in `docs/clinical-methods.md` §3).
5. **Categorise** each field into one of the categories 7.1–7.8 of `docs/clinical-methods.md` §7 (for example "onset date mismatch" or "no discrepancy"), with flags, and list anything the rules cannot decide as "needs human review".
6. **Show** it all in a local web app, including a live run on any case.

The pipeline is frozen (git tag `pipeline-freeze-v1`, see `docs/freeze.md`); `tests/test_freeze.py` checks that its files have not changed.

## Set up (once)

You need Python 3.13 or newer (`python3 --version`) and Git. In a terminal, in the project folder:

```bash
python3 -m venv .venv          # create a private Python environment in .venv/
source .venv/bin/activate      # switch this terminal to it; the prompt starts with (.venv)
pip install -e ".[dev]"        # install ReSauce and its test tool (pytest)
```

In every new terminal, run `source .venv/bin/activate` first.

## Run the demo app

```bash
source .venv/bin/activate
python -m app
```

Then open **http://localhost:8000** in a browser. Stop the app with **Ctrl+C**.

- If port 8000 is already in use, run `python -m app --port 8001` and open http://localhost:8001.
- The app shows the measured results, every case, and an investigation view. In that view, **Run ReSauce** runs the frozen pipeline live on the case and reveals it stage by stage: extraction (highlights at the exact quoted text), timeline, comparison, verdict, then Baseline A and the reference answer. It shows the measured run time and whether the live output matches the stored evaluation run.
- The app needs only Python: the built web page is stored in `web/dist/`.
- Another results file (for example the locked set, after its final evaluation) can be added without code changes:
  `python -m app --results <results file> --data <data folder> --reference <reference folder>`.

**Changing the web page** (only needed for development) needs Node.js (an LTS version):

```bash
cd web
npm install        # once
npm run build      # rebuilds web/dist/ after a change
npm run dev        # optional: live-reloading page at http://localhost:5173 (keep python -m app running)
```

## Run the evaluation and the tests

```bash
pytest                          # the test suite
python -m resauce.evaluate      # scores both methods on the dev and held-out splits
```

Warning: `python -m resauce.evaluate` **overwrites** `results/report.md`, `results/dev.json` and `results/held_out.json`. Run it only when a new, recorded run is intended.

## Results so far

Quoted from `results/report.md`. Synthetic data; reference answers are "intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); not clinician-verified". Counts are fields (onset date and maximum grade, combined). The splits are reported separately and never pooled.

**Dev split (20 cases).** Used to build and debug the pipeline, so these numbers are expected to be optimistic.

| Method | Precision | Recall | F1 | Exact agreement | Misses | False alerts |
|---|---|---|---|---|---|---|
| ReSauce | 1.00 (10/10) | 1.00 (10/10) | 1.00 (20/20) | 1.00 (38/38) | 0 | 0 |
| Baseline A | 0.90 (9/10) | 0.90 (9/10) | 0.90 (18/20) | 0.87 (33/38) | 1 | 1 |

**Held-out split (52 cases), in-repo and not sealed, and "seen":** the pipeline changed after the first held-out run (commit 4ff6c5f). It has the same writer as the dev cases and sits in the same repository, so it is not an independent test.

| Method | Precision | Recall | F1 | Exact agreement | Misses | False alerts | "review: …" results |
|---|---|---|---|---|---|---|---|
| ReSauce | 0.84 (16/19) | 0.80 (16/20) | 0.82 (32/39) | 0.86 (84/98) | 4 | 3 | 5 |
| Baseline A | 0.61 (14/23) | 0.70 (14/20) | 0.65 (28/43) | 0.65 (64/98) | 6 | 9 | 0 |

Out of scope (ReSauce only; Baseline A cannot flag it): dev 1 of 1 and held-out 3 of 3 flagged with the reference's reason. Evidence-quote validity was 1.00 for both methods on both splits. Baseline B (a language model) has not been run.

### Locked-set results: added after the final evaluation

*Placeholder.* The locked set (written after the pipeline freeze, in a separate repository) has not been evaluated yet. No locked-set numbers exist.

## Limitations

- All data is synthetic. Results are not clinical validation.
- Cases and reference answers were written by Claude sessions. A blind re-derivation by another Claude session agreed on every category, but both come from the same model family and the same rules text: this shows the rules are applied consistently, not that either is clinically right. No clinician has verified them.
- A clinician has not yet reviewed the assumptions A1–A35 or the rule gaps listed in `reference/dev-v1/comparison.md` §8.
- The held-out split is not sealed and is "seen"; the dev split was used to build the pipeline.
- The extractor's phrase lists were built from the 20 dev cases and `docs/clinical-methods.md` only. Some misspellings are listed for review; others (swapped letters, short words) are missed without a warning.
- Rules that are not built return "review: …" (needs human review), never a guess.
- Each case holds 3 to 12 documents, so most days in the window have no documented assessment; the "unassessed period" lists are long by design.
- Baseline B is not run. The locked set is not evaluated.

The full list, with sources, is on the app's **Methods & limitations** page and in `docs/evaluation-spec.md` §6.

## Project layout

```
src/resauce/     the pipeline (frozen): loader, extraction, timeline, rules engine, Baseline A, evaluation
app/             the demo app's local web server (Python standard library only); it calls src/, never the reverse
web/             the demo app's web page (Vite + React); web/dist/ is the built page
data/dev-v1/     72 synthetic cases
reference/       reference answers and splits
results/         the evaluation results (report.md, dev.json, held_out.json)
docs/            clinical methods, data format, evaluation spec, freeze record, handoff log
tests/           automated tests
```

## Data and licence

- **Data:** synthetic only, written for this project. Every file carries the notice "FICTIONAL SYNTHETIC DATA. NOT A REAL PATIENT." Never add real patient data.
- **Licence:** no licence has been chosen yet.
- The bundled fonts (Source Serif 4, IBM Plex Sans, IBM Plex Mono) are under the SIL Open Font Licence.
