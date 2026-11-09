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
6. **Review** in a local workstation app: run the pipeline on your cases, check each finding against the source text, record decisions in an audit log, and export.

The pipeline is frozen (git tag `pipeline-freeze-v1`, see `docs/freeze.md`); `tests/test_freeze.py` checks that its files have not changed.

## Set up (once)

You need Python 3.13 or newer (`python3 --version`) and Git. In a terminal, in the project folder:

```bash
python3 -m venv .venv          # create a private Python environment in .venv/
source .venv/bin/activate      # switch this terminal to it; the prompt starts with (.venv)
pip install -e ".[dev]"        # install ReSauce and its test tool (pytest)
```

In every new terminal, run `source .venv/bin/activate` first.

## Use the workstation (step by step)

The workstation is a local web app: it runs on your own computer, listens only on this computer (127.0.0.1), makes no network calls and works offline. It works on a **workspace folder** that holds your cases, every verification run, the audit log and exports. The default is `workspace/` in the project folder (never committed to git).

1. **Start it.**
   ```bash
   source .venv/bin/activate
   python -m app
   ```
   Open **http://localhost:8000** in a browser. Stop it with **Ctrl+C**. If port 8000 is taken: `python -m app --port 8001`. Another workspace folder (inside the project folder): `python -m app --workspace my-workspace`.
2. **Bring cases.** The home page is the **Pipeline**: imported cases on the left of a black stage, the four real stages (Load, Extraction, Timeline, Rules engine) in the middle, and three destinations on the right. On first start the workspace is empty: press **Import data** (top right, or on the stage) and choose **Import examples** to copy the 72 fictional cases from `data/dev-v1` (the originals are only read). The same sheet copies valid case folders from **a folder in this project** (type its path) or opens **Enter a case by hand**: a form for case details, documents (paste the note, drop a `.txt` file onto it or load one; add later versions with an amendment reason) and research record values. Saving asks you to confirm the case is fictional, writes it in the data format and checks it with the pipeline's own loader; any problem appears next to its field.
3. **Verify.** Press **Verify all cases** (or **Verify new cases**). Each case is run through the frozen pipeline and travels across the stage as its real stage results arrive. The pipeline finishes a case in milliseconds, so the display is slowed to be followed (it says "Paced for viewing"); **Pause** and **Show result now** control it, and a case never moves before its real result exists. Each case lands in one destination, decided only from its two field categories: **Discrepancy** (red, 7.1, 7.2, 7.3 or 7.8), **Needs review** (amber: 7.4, 7.5, a "review: …" result, or out of scope) or **No discrepancy detected** (green, both fields 7.6 or 7.7; when the run ends the plug seats in its socket). A red beacon turns while any discrepancy has no review decision. Numbers stay hidden until you press **Numbers** (or `N`): counts per stage and destination and the measured stage times. **List** shows the same cases as a table. Tick **Also run Baseline A** to run the simpler method as well.
4. **Check the evidence.** Click any mark on the stage (or a destination's title) to open the inspector beside it: the case's two fields with record and documented values, its path through the stages with measured times, and every finding with its quoted evidence. **Open case** shows the documents: click a quote and the text scrolls to it and marks it; hover a timeline event to see its text, and the reverse. For the example cases, the case page also says whether the live output matches the stored evaluation run.
5. **Review.** **Review** lists every open finding, most serious first (discrepancy alerts 7.1, 7.2, 7.3, 7.8; then 7.4, 7.5 and "needs human review"; then other flags). For each: **Confirm discrepancy**, **Dismiss** or **Needs clinician**, with a required note. Your name is asked once per browser session. Keys: `J`/`K` next and previous, `C`/`D`/`L` choose a decision and jump to the note, `Ctrl`+`Enter` (or `⌘`+`Enter`) to record it. A decision never moves a case on the stage; it only marks it as decided.
6. **Audit.** **Audit** shows every run and decision (time, reviewer, case, field, decision, note, pipeline version with the frozen-file hashes), filterable. It is stored append-only in `workspace/audit.jsonl`. The pipeline output is never edited; decisions sit beside it.
7. **Export.** From **Audit**, **Export reports and CSV** writes a printable case report (open it and use the browser's Print to make a PDF) and a CSV of all findings and decisions, both into `workspace/exports/`. The inspector's **Case report** and the pipeline's **Export all findings (CSV)** do the same in place.
8. **Results** shows only the headline percentages of the stored evaluation runs (precision, recall, exact agreement; ReSauce beside Baseline A, per split) with their caveats; **How these were measured** opens the exact fractions. **About** says what ReSauce is and is not, and what the pipeline view does not show.

The app needs only Python: the built web page is stored in `web/dist/`. Another results file for the Results page (for example the locked set, after its final evaluation) can be added without code changes: `python -m app --results <results file> --data <data folder> --reference <reference folder>`.

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

The full list, with sources, is on the app's **About & limitations** page and in `docs/evaluation-spec.md` §6.

## Project layout

```
src/resauce/     the pipeline (frozen): loader, extraction, timeline, rules engine, Baseline A, evaluation
app/             the workstation's local server (Python standard library only); it calls src/, never the reverse
web/             the workstation's web page (Vite + React); web/dist/ is the built page
workspace/       your workspace (created on first start; git-ignored)
data/dev-v1/     72 synthetic cases
reference/       reference answers and splits
results/         the evaluation results (report.md, dev.json, held_out.json)
docs/            clinical methods, data format, evaluation spec, freeze record, handoff log
tests/           automated tests
```

## Data and licence

- **Data:** synthetic only, written for this project. Every file carries the notice "FICTIONAL SYNTHETIC DATA. NOT A REAL PATIENT." Never add real patient data.
- **Licence:** no licence has been chosen yet.
- The bundled font IBM Plex Mono is under the SIL Open Font Licence. All other text uses the computer's own system font.
