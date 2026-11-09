# Handoff: shared verification engine and evidence network

- **Branch:** `feature/verification-engine` (from `main` at `0e86f3d`). Merge into `main` only after the acceptance checks below pass.
- **Date:** 2026-11-09
- **Status:** planned, not started. No code has been written for this yet.
- **Budget:** about 3 hours of implementation.
- **Source brief:** the product owner's "Architectural Evolution & 3-Hour Implementation Handoff" (summarised here; this file is self-contained).

Read `CLAUDE.md` first. Its rules on scientific integrity, dependencies, tests, commits and explaining each step in plain language still apply to everything below.

---

## 1. The idea in one paragraph

ReSauce today checks one thing well: ICANS onset date and maximum grade in a research record against the clinical notes behind it, with every finding traced to a quoted span. The new direction is **one verification engine, multiple specialised pipelines, one interconnected evidence network**. A small in-process engine receives imported datasets, decides which verification modules can run, runs them, normalises their results into one finding contract (outcome **passed**, **discrepancy** or **unverifiable**), keeps provenance, and streams its progress. The home screen becomes a network that is drawn from those real results: datasets → engine → modules → findings. Selecting a discrepancy shows the affected records, the rule, the source references and the explanation. CAR-T toxicity reconciliation stays the first use case, but nothing in the engine may be CAR-T-specific.

Tagline for the import screen: **Watch every record meet its evidence.**

## 2. Feasibility verdict: CONDITIONAL GO

Achievable in 3 hours with reduced scope. The reasons come from the code:

| Constraint | Where | Consequence |
|---|---|---|
| The ICANS pipeline is **frozen** | `docs/freeze.md` hashes `loader.py`, `models.py`, `extract.py`, `phrases.py`, `engine.py`, `timeline.py` and `baseline_a.py`; `tests/test_freeze.py` fails if any of them changes | Do not edit those files. New code goes in **new files** (the freeze allows this). The ICANS pipeline can only be wrapped. |
| **No dependencies** | `pyproject.toml` has `dependencies = []`; the server is standard library only; `CLAUDE.md` says to ask before adding one | Support **CSV and JSON** only. Parquet needs `pyarrow`: ask the user first, so it is deferred. |
| **Synthetic data only** | The loader rejects files without `"FICTIONAL SYNTHETIC DATA. NOT A REAL PATIENT."`; `PRODUCT.md` forbids real data | The new importer keeps a synthetic/demo gate (see §5). Never invite real patient data. |
| **No tabular ingestion exists** | `src/resauce/loader.py` reads only the strict case-folder JSON format (`docs/data-format.md`) | Tabular import, mapping and three of the four modules are new code. |
| **The current network is case-shaped** | `web/src/components/network/layout.js` `layout(records)` and `web/src/lib/runner.js` `STAGES`/`PATH` assume one fixed path: case → Load → Extraction → Timeline → Rules → outcome | The new graph needs its own layout. `signals.js` (canvas signals), `lib/motion.js`, `lib/spring.js` and the styles can be reused. |

## 3. What already exists and is reused

| Piece | File | Reuse |
|---|---|---|
| Local server, 127.0.0.1 only, no network calls, rejects cross-site writes | `app/server.py` | Add routes; reuse `_api`, `_body`, `_stream` (NDJSON, one event per line as it happens) |
| Workspace, runs, append-only audit log | `app/workspace.py`, `app/workstation.py` | Store new runs beside the old ones; log them in `workspace/audit.jsonl` |
| Frozen ICANS pipeline, staged | `app/pipeline.py` `run_stages()` | Optional adapter module (stretch, §6) |
| ICANS findings with evidence | `app/findings.py` `findings(output)` | Template for mapping ICANS output into the new contract |
| Evidence reference shape | `src/resauce/models.py` `EvidenceRef(document_id, version, start, end, quote)` | The contract's document-quote evidence uses the same fields |
| Front end | `web/` (Vite 8 + React 19, plain JS) | Add one view; keep Pipeline, Review, Audit, Results, About working |
| Design language | `DESIGN.md`, `web/src/styles.css` | Already black on white with red/amber/green tokens; follow it |
| Accessibility rule | `PRODUCT.md` | Outcomes are never shown by colour alone: symbol + word + colour. Honour `prefers-reduced-motion`. |

## 4. Architecture

All new Python lives in **`src/resauce/verify/`** (a new subpackage: new files, so the freeze is intact, and no reinstall is needed). It must not import from `app/` or `web/`.

```
src/resauce/verify/
  contract.py     Finding, Evidence, RecordRef, Outcome; to_dict()
  ingest.py       CSV/JSON -> Table (rows keep file + row number); rejects what it cannot read
  mapping.py      explicit links between tables; suggestions only, never applied silently
  engine.py       registry + coordinator; yields events as each step finishes
  modules/
    __init__.py   REGISTRY = [structural, reconcile, temporal, evidence]
    structural.py Pipeline A
    reconcile.py  Pipeline B
    temporal.py   Pipeline C
    evidence.py   Pipeline D
```

### 4.1 Finding contract (`contract.py`)

```python
Outcome = Literal["passed", "discrepancy", "unverifiable"]

@dataclass(frozen=True)
class RecordRef:      # one source row
    dataset: str      # e.g. "toxicity_events.csv"
    row: int          # 1-based data row (header excluded), as the user would count it
    key: str | None   # the row's identifier value, if it has one

@dataclass(frozen=True)
class Evidence:       # one value the finding rests on
    record: RecordRef
    column: str
    value: str | None # exactly as read from the file; None means the cell was empty

@dataclass(frozen=True)
class Finding:
    finding_id: str   # stable: f"{module}:{rule_id}:{record keys}"
    module: str       # "structural" | "reconcile" | "temporal" | "evidence"
    rule_id: str      # e.g. "C1-onset-after-infusion"
    outcome: Outcome
    records: tuple[RecordRef, ...]
    datasets: tuple[str, ...]
    explanation: str  # plain words, built from the evidence values; never generated text
    evidence: tuple[Evidence, ...]
```

Outcome rules (non-negotiable):
- **passed**: the rule ran and held. The UI says "Checks passed", never "correct" or "verified as accurate".
- **discrepancy**: at least two traceable values conflict, or one value breaks a stated constraint. The explanation names both values and where they came from.
- **unverifiable**: the rule could not reach a justified answer: missing mapping, unmatched identifier, empty cell needed by the rule, or a clinical definition the module does not support. Never counted or drawn as passed.

### 4.2 Module interface

```python
class Module(Protocol):
    name: str
    rules: tuple[str, ...]
    def requires(self) -> tuple[str, ...]          # roles it needs, e.g. ("patients", "toxicity")
    def can_run(self, ctx) -> str | None           # None, or the reason it cannot run
    def run(self, ctx) -> Iterable[Finding]
```

A module that cannot run produces one `unverifiable` finding per rule with the reason, so the user sees that it was skipped and why. Adding a module = one new file + one line in `REGISTRY`. The engine must not change.

### 4.3 Engine (`engine.py`, aim for under ~100 lines)

`run(tables, mapping)` yields, in order and only as each happens:
`{"event": "dataset", ...}` per table → `{"event": "module_started", "module"}` → `{"event": "module_finished", "module", "seconds", "findings": [...]}` → `{"event": "done", "counts": {...}}`. An exception in one module becomes `{"event": "module_failed", "module", "error"}` and the other modules still run. No sleeps or invented delays in Python. (If the front end slows playback so it can be followed, as the current Pipeline view does, it may only replay events that have already arrived.)

### 4.4 Ingestion and mapping

- `ingest.py`: CSV via `csv.DictReader` (UTF-8, header required), JSON as a top-level array of flat objects. Anything else is **rejected with a reason** (nested objects, no header, duplicate column names, mixed row shapes). Each row keeps its file name and row number.
- Demo gate: each demo file carries a `synthetic` column whose value is `true` on every row, or a JSON object form `{"synthetic": true, "fictional_notice": "...", "rows": [...]}`. Files without the gate are refused with the message that this proof of concept accepts synthetic data only. (Pick one form and document it in `docs/data-format.md` as a new section.)
- `mapping.py`: the user assigns each table a **role** (`patients`, `toxicity`, `ae_reports`) and confirms **links**, e.g. `toxicity.patient_ref → patients.patient_id`. The server may suggest links from identical or near-identical column names, but a suggestion is never used until the user confirms it. **Never assume that the same patient ID in two files is the same person** without a confirmed link.

## 5. Modules for this demonstration

Build in this order. Stop adding modules when the go/no-go point in §8 says so.

| Module | Rules (initial) | Discrepancy when | Unverifiable when |
|---|---|---|---|
| **A structural** | A1 required columns present; A2 required cells non-empty; A3 dates parse as `YYYY-MM-DD`; A4 grades are whole numbers 0–5; A5 identifier unique within its table | a value breaks the stated format or uniqueness | a role the rule needs was not assigned |
| **B reconcile** | B1 every toxicity row links to exactly one patient; B2 every AE report links to exactly one toxicity row (via confirmed link, e.g. `patient_ref` + `event_type`) | a link points to two candidates | no confirmed link exists; the identifier has no match (orphan) |
| **C temporal** | C1 toxicity onset ≥ infusion date; C2 onset ≤ infusion + observation window (window comes from a dataset setting, not a guess); C3 AE report date ≥ onset | the dates break the constraint | either date is missing, or the rows could not be linked (B) |
| **D evidence** | D1 the max grade in the toxicity table equals the grade in the linked AE report; D2 the onset date equals the AE report's event date | the two linked values differ | no link, or one side is empty |

C and D depend on B's links: they read the confirmed link from the context, not from B's findings, so each module stays independently runnable.

## 6. Stretch: ICANS adapter module

Only if §8's go/no-go allows it. `modules/icans.py` runs the frozen pipeline (`app/pipeline.py` already shows how) on imported case folders and maps its field categories into the contract using `app/findings.py`'s rules: 7.1, 7.2, 7.3, 7.8 → discrepancy; 7.4, 7.5, "review: …", out of scope → unverifiable; 7.6, 7.7 → passed. Its evidence is the document quote (`document_id`, `version`, `start`, `end`, `quote`), so `Evidence` needs an optional `quote` form. This proves the engine coordinates the existing work without changing it. The `src/resauce/verify` package must not import from `app/`, so either move the mapping logic into the new module or keep the adapter in `app/`.

## 7. Demo data

`data/demo-tabular-v1/` with about 40 synthetic CAR-T patients across three CSV files: `patients.csv` (patient_id, infusion_date), `toxicity_events.csv` (event_id, patient_ref, event_type, onset_date, max_grade) and `ae_reports.csv` (report_id, patient_ref, event_type, event_date, grade, reported_at), plus a `README.md` that says in its first line: **DEMONSTRATION DATA. Synthetic. Contains deliberately introduced discrepancies for testing. Not from any real patient or study.**

- Introduce a small, known set of problems: a grade mismatch (D1), an onset before infusion (C1), an orphan AE report (B → unverifiable), an empty grade cell (A2 + D unverifiable), a bad date format (A3).
- **No answer leakage** (as in `docs/data-format.md` §1): the CSVs contain nothing that marks which rows are wrong. The list of introduced problems lives in `tests/fixtures/demo_tabular_expected.json`, never in `data/`.
- A test asserts the engine finds exactly that list (no misses, no extras) and that every finding's evidence values equal the cells in the files. The demonstration must never depend on hardcoded outcomes.
- The UI and README call these "demonstration data", never discoveries.

## 8. Time plan, go/no-go and cut order

| Phase | Minutes | Output |
|---|---|---|
| 1. Confirm | 15 | Read `app/workstation.py` (`verify`, `verify_all`), `web/src/views/Pipeline.jsx`, `components/network/Network.jsx`, `lib/runner.js`. Confirm the plan holds; write any change into this file. |
| 2. Engine + modules | 65 | contract → ingest → mapping → engine → A → B → C → D, with the demo data and the tests in §7. **Go/no-go at minute ~110 total:** if A–D pass their tests, consider the ICANS adapter (§6); otherwise skip it. |
| 3. API + front end | 65 | `POST /api/verify/import` (file text in JSON → recognised structure, suggested links); `POST /api/verify/run` (stream of §4.3 events). New **Verify** view as the home route; existing views stay in the nav. |
| 4. Verify + document | 35 | `pytest` (including `test_freeze.py`); drive the whole flow in a browser; `npm run build` to refresh `web/dist/`; README section; entry in `docs/handoff.md`. |

**Cut order when short of time, cut first at the top:** visual polish → ICANS adapter → detailed motion → module D. **Never cut:** the engine, real modules, traceable evidence, honest unverifiable outcomes.

## 9. Front end

Follow `DESIGN.md` (white, black type, system font, IBM Plex Mono for IDs and dates, minimal colour). The owner's benchmark is Apple-level restraint: no dashboards of statistics, no oversized cards, no gradients, no decorative borders. One prominent import action. ReSauce wordmark top left, navigation across the top (the existing header already does this).

1. **Import.** Headline "Watch every record meet its evidence." One Import button (file picker, several files). Each file then shows as one line: name, rows, columns, recognised role, or the reason it was refused. Then a compact mapping step to confirm roles and links. A "Use demonstration data" link loads `data/demo-tabular-v1/` and is labelled as such.
2. **Network.** Datasets on the left → engine node → one node per module → findings. Built in a new `web/src/lib/graph.js` from the run's events, not from `layout.js`. A module node lights when its `module_started` arrives and settles on `module_finished`. Signals (reuse `signals.js`) travel only along edges whose events have arrived. Nothing is drawn as passed before `done`.
3. **Results.** Outcome marks: **passed** (restrained green, check symbol), **discrepancy** (red, slow pulse like a warning beacon; no blue, no fast flashing), **unverifiable** (amber/neutral, distinct symbol). Records are aggregated per dataset × module until a finding is selected. Selecting a finding highlights its edges (dataset → module → finding) and opens a panel showing: rule ID and wording, explanation, and a small table of the evidence cells (dataset, row, column, value). Nothing behind a generated summary.

Reduced motion: no travelling signals, no pulse; state changes are immediate, with the same symbols and words.

## 10. Acceptance checks (what "done" means)

1. `pytest` passes, including `tests/test_freeze.py` (frozen files unchanged).
2. The engine runs at least two modules (target: four) that are each runnable on their own.
3. The demo data produces exactly the expected findings from `tests/fixtures/demo_tabular_expected.json`, found by the engine.
4. Every finding has module, rule ID, records, datasets, explanation, outcome and evidence whose values match the source cells.
5. Missing links and empty cells show as **unverifiable**, never as passed.
6. In a browser: import → map → run → network resolves → select a discrepancy → see its rows, rule, sources and explanation, with its edges highlighted.
7. The network contains only nodes and edges that exist in the run result.
8. The existing Pipeline, Review, Audit, Results and About pages still work.
9. No new dependency, no network call, no claim beyond "runs on this computer, makes no network calls, synthetic data only".

## 11. Decisions already made (change only with the user)

- **Parquet:** deferred (needs `pyarrow`; ask before adding).
- **Privacy wording:** only what the code supports: listens on 127.0.0.1, makes no network calls. No "fully private" or compliance claims.
- **Market claims:** none. Show technical capability only.
- **Commits:** follow `CLAUDE.md` (stage files by explicit path, one clear message, **no AI attribution lines**, push the branch). Commit to `feature/verification-engine`, not `main`.
- **Tests:** only for code that decides answers (modules, engine, mapping, ingestion rejection), a few focused tests per rule.

## 12. Open questions for the user

1. Is the per-row `synthetic` column an acceptable demo gate, or should the gate be a sidecar `dataset.json` like the existing format?
2. Which observation window should temporal rule C2 use for the demo (the existing ICANS data uses Day 0 to Day +28)?
3. Should the new Verify view replace the Pipeline view as home, or sit beside it until the merge?
4. Is Parquet wanted badly enough to add `pyarrow`?
