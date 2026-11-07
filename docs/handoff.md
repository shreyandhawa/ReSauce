# Handoff log

Progress notes between Claude Code sessions, newest entry first. Read this file at the start of a session and add an entry at the end.

Each entry covers:
- **Status:** where the project stands
- **Done:** what was completed
- **Decisions & why:** the choices made and the reasons behind them
- **Next steps:** what to do next
- **Open questions:** anything waiting on the user
- **How to verify:** commands that prove it works

---

## 2026-11-07: Milestone 2 Step 3, dataset plan drafted

**Status:** Milestone 2 Step 3 is drafted. `docs/dataset-plan.md` v0.1 is a draft for user review and is **not approved**. No cases, case text, reference answers or code were written. No `data/` folder exists. `pytest` reports 75 passed (no code changed).

**Done:**
- Wrote `docs/dataset-plan.md` v0.1:
  - 58 scenarios (SC-01 to SC-58), each with expected onset and grade categories (§7) and the rules and assumptions it exercises;
  - a coverage matrix: every onset category (7.1, 7.4–7.7) and grade category (7.2–7.7) appears in both sets;
  - proposed size: 58 development cases, 115 locked cases (100 scored now, 15 waiting on gaps), 42% no-discrepancy among scored locked cases;
  - confidence intervals computed with the Wilson method (calculation shown), and what this size cannot show;
  - construction, realism, safety, leakage-control and quality-check rules;
  - an outline of the reference-answer procedure;
  - 15 gaps where `clinical-methods.md` does not define the correct answer (GAP-1 to GAP-15), not decided.
- Did not edit `clinical-methods.md`, `data-format.md`, code, tests or settings.

**Decisions & why (made by the user before this step):**
1. New order for the rest of Milestone 2: Step 3 dataset plan → Step 4 development cases (plus a small loader fix) → Step 5 reference answers → Step 6 locked evaluation cases. All before Milestone 3. Why: the test data and its answers must exist, and be fixed, before the pipeline is built, so the pipeline cannot be shaped around them.
2. Locked evaluation cases live in a separate private GitHub repository that is never opened in ReSauce Claude Code sessions. Why: sessions that build the pipeline must never see the cases used to measure it.
3. Reference answers: the case author records the intended answer separately; a fresh Claude session, given only the case, `clinical-methods.md` and `data-format.md`, derives answers without knowing the intent; the user reviews every disagreement (case bug or genuine ambiguity, both logged); answers are labelled "not clinician-verified" until expert review. Why: two independent readings catch case-writing mistakes and hidden ambiguities.

**Decisions proposed in the plan (await approval):** case numbers; Pos/Neg/Flag/Gap case types; storage in `data/` and `reference/`; sealing the locked set with a SHA-256 fingerprint recorded in the main repo.

**Next steps:**
- User reviews `docs/dataset-plan.md`.
- Step 4 (development cases) only after approval.
- Carried forward to Step 4: reject whitespace-only note text in the loader.

**Open questions:**
- The 12 open questions in `docs/dataset-plan.md` §11 (approve numbers; who decides gaps; scoring of 7.4/7.5; baselines not yet specified; and others).
- Gaps in `clinical-methods.md` (plan §10), not decided:
  - GAP-1: record says no ICANS, notes document ICANS.
  - GAP-2: record says ICANS, onset or grade empty.
  - GAP-3: record says no ICANS, notes show none (7.7 or 7.4?).
  - GAP-4: record says ICANS, no qualifying finding (onset category).
  - GAP-5: non-attribution ambiguity (conflicts, barriers, phrases) has no category.
  - GAP-6: §7.1 bullets 2 and 4 conflict.
  - GAP-7: 7.3 vs 7.4 when an unassessed period exists.
  - GAP-8: relative time phrases to date ranges; signed difference for a range.
  - GAP-9: unsigned latest version, or no signed version.
  - GAP-10: when a record revision counts as "explained".
  - GAP-11: out-of-scope cases, flag only or also categories.
  - GAP-12: time window for a "coinciding" competing cause.
  - GAP-13: lightly edited copied-forward text.
  - GAP-14: observation window not chosen.
  - GAP-15: ICE 0 without consciousness information when record grade ≤ 2.
- Carried forward: who does the clinician review; Node.js LTS version; no software licence chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 75 passed
git status                                          # expect: docs/dataset-plan.md new, docs/handoff.md changed
```
Open `docs/dataset-plan.md` and check that §2 lists SC-01 to SC-58 and §10 lists GAP-1 to GAP-15.

---

## 2026-11-07: /finish-step skill added

**Status:** Setup change only. No code or research content changed. Milestone 2 status is unchanged (Step 2 complete, see entry below).

**Done:**
- Added the project skill `.claude/skills/finish-step/SKILL.md`. Typing `/finish-step "commit message"` in Claude Code runs the end-of-step routine: run the tests, check which files changed, update this handoff log, commit only the step's files (no AI attribution), push, and show the raw git output.

**Decisions & why:**
- The same commit-and-push routine was written out again in every step prompt. A skill stores it once, so every step closes the same way and nothing is forgotten.
- `disable-model-invocation: true`: only the user can start the skill. Claude cannot decide on its own to commit and push.

**Next steps:**
- Unchanged: Milestone 2 Step 3 (synthetic test cases), once the user approves the scope.

**Open questions:**
- Whitespace-only note text is accepted; fix in the next code step.

**How to verify:**
- In Claude Code, type `/` and check that `finish-step` appears in the list.
- `cat .claude/skills/finish-step/SKILL.md` shows the skill's instructions.

---

## 2026-11-07: Milestone 2 Step 2, data format and loaders

**Status:** Milestone 2 Step 2 is complete. The data format spec (`docs/data-format.md` v0.1), the loader and the tests are written. `pytest` reports 75 passed. No synthetic patient cases, reference answers, extraction or medical logic exist yet.

**Done:**
- Wrote `docs/data-format.md` v0.1. It covers the folder layout, every field of every file, time and offset conventions, the evidence-reference shape, 28 validation rules, what the format leaves out and why, and open questions.
- Added `src/resauce/models.py`: frozen dataclasses for `Dataset`, `ObservationWindow`, `Case`, `DocumentVersion` (with `version_id`), `ResearchRecord` (with `current`), `RecordVersion` and `EvidenceRef`.
- Added `src/resauce/loader.py`: `load_dataset`, `load_case`, `check_evidence_ref`, `study_day` and `DataFormatError`. It collects every problem (file path, field, message) before raising one error.
- Added a valid fixture in `tests/fixtures/format/valid_dataset/`: 2 cases, placeholder text only. It has a document with an amendment (2 versions), a record with 2 versions, and a case with no `documents/` folder.
- Added `tests/test_loader.py` (74 tests). Invalid inputs are made by copying the fixture into a temporary folder and changing one thing.
- One bug found and fixed while testing: an unreadable document file caused an extra, misleading "missing version" message. The loader now skips the numbering check for a document whose file could not be read (spec §10).

**Decisions & why:**
- Confirmed by the user before this step:
  1. Note text is stored inside the JSON file (`text` field), not in separate `.txt` files.
  2. Only documentation time is metadata. Event times stay in the note text for the pipeline to find. There is no "performed at" field.
  3. Dates are fictional calendar dates (ISO 8601). Study day numbers are computed from the infusion date, never stored.
  4. Standard library only. No new dependencies.
- Proposed in the plan and approved by the user:
  - every field must be present; empty values are written as `null`, never left out (keeps "forgotten" and "empty" apart);
  - date and time formats are checked exactly with a pattern before parsing, because Python's own parser also accepts other forms;
  - reason fields must be non-empty if not `null`;
  - hidden files (e.g. `.DS_Store`) are ignored; other unexpected files are errors;
  - documents are sorted by document number, then version;
  - `cases/` must exist and contain at least one case.
- Design principle: inputs hold only what a real chart export or research database would hold. This prevents answer leakage.

**Next steps:**
- Milestone 2 Step 3: write the synthetic test cases. Start only after the user approves the scope.
- Clinician review of assumptions A1–A18 is still pending.

**Open questions:**
- The 8 format questions in `docs/data-format.md` §12 (e.g. must later versions give a reason; must the latest version be signed).
- Carried forward: who does the clinician review; Node.js LTS version; no software licence chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 75 passed
```

---

## 2026-11-07: Claude Code project settings added

**Status:** Setup change only. No code or research content changed. Milestone 2 status is unchanged (see entry below).

**Done:**
- Added `.claude/settings.json`:
  - turns off commit and pull-request attribution (`attribution.commit` and `attribution.pr` set to empty strings, `sessionUrl` set to false);
  - lets only `.venv/bin/python -m pytest`, `git status`, `git diff` and `git log` run without a permission prompt.
- Added `.claude/settings.local.json` (personal settings) to `.gitignore`.

**Decisions & why:**
- A setting is enforced by Claude Code itself. A CLAUDE.md rule is only an instruction Claude reads and could miss. The CLAUDE.md attribution rule stays as a backup.
- Used the empty-string form from the docs, not `"attribution": false`, because the docs say the `false` form needs Claude Code v2.1.281 or later. The empty-string form works on all versions.
- Only read-only commands and the test command are pre-approved. Commits, pushes, deletions and installs still ask first.
- Source: https://code.claude.com/docs/en/settings (and its settings-reference and permissions pages), read 2026-11-07.

**Next steps:** Unchanged. Clinician review of assumptions A1–A18, then Step 2 after user approval.

**Open questions:** None.

**How to verify:** Open `.claude/settings.json`. Run `git check-ignore -v .claude/settings.local.json`. It should print the `.gitignore` line.

---

## 2026-11-07: Milestone 2 Step 1, clinical methods drafted and internally reviewed

**Status:** Milestone 2 Step 1 is drafted and internally reviewed. `docs/clinical-methods.md` v0.2 is committed. A clinician has not reviewed it yet. Step 2 has not started.

**Done:**
- Read the primary source in full: Lee et al. 2019, ASTCT ICANS/CRS consensus grading (PMID 30592986, doi:10.1016/j.bbmt.2018.12.758).
  - Version used: the NIH author manuscript (PMC12180426), retrieved from PubMed Central's official OAI service.
  - The publisher's version could not be accessed.
- Wrote `docs/clinical-methods.md` (v0.1, commit 59133fe). Every claim is tagged SOURCE, OPERATIONAL or ASSUMPTION — EXPERT REVIEW.
- Applied internal review fixes (v0.2):
  - consciousness wording in two examples;
  - corrected cross-references (age cutoff, A3, A7);
  - new assumptions A15–A18;
  - checked the §8 citation to §Grade 2 CRS. It is correct and was left unchanged.

**Decisions & why:**
- Pediatric pathway excluded (adults ≥18 only): the source is inconsistent at age 12, and the CAPD tool cannot separate Grade 1 from Grade 2.
- Missing ≠ absent:
  - an over-graded record is reported as "not supported", never "wrong";
  - a narrative normal neurological note does not rule out ICANS.
- Attribution to other causes is taken only from clinician statements. ReSauce does not judge it.

**Next steps:**
- Clinician review of assumptions A1–A18 in `docs/clinical-methods.md` §9. This is the agenda for that review.
- Step 2 (synthetic data format) only after the user approves it.

**Open questions:**
- Who will do the clinician review?
- Carried forward: Node.js LTS version; no software licence chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
git log --oneline -3     # expect the review-fix commit on top
pytest                   # expect: 1 passed (no code changed)
```

---

## 2026-11-07: Milestone 1 complete (summary)

**Status:** Milestone 1 (project foundation) is complete and verified. Milestone 2 is proposed below and awaits user approval.

**What works (checked 2026-11-07):**
- `python -m resauce` prints the name, version 0.1.0 and Python 3.14.3, then exits without errors.
- `pytest` reports 1 passed.
- Git ignores `.venv/` and `.env`. Only the project files are tracked.
- The project lives at `~/Projects/ReSauce`, outside iCloud.
- The code is on GitHub at `https://github.com/shreyandhawa/ReSauce` (private, branch `main`). GitHub matches the local copy.
- `CLAUDE.md` holds the scientific integrity and engineering rules. `README.md` has the beginner setup guide.

**What does not exist yet:** any scientific or medical logic, any data, and the web interface. This is intentional.

**Milestone 2 (proposed, not yet approved): synthetic data foundation**

Goal: decide what our synthetic inputs look like and load them reliably. No extraction or medical algorithms yet.
1. Agree with the user on a simple file format (likely JSON) for two input types:
   - a *clinical document*: an ID, a date, a type, and the full text
   - a *research record*: the documented ICANS fields that we will later check against the documents
2. Write a small, clearly labelled set of hand-made synthetic examples. No real patient data.
3. Write Python code in `src/resauce/` that loads these files and reports clear errors for malformed input.
4. Write tests for loading both valid and invalid files.
5. Record which fields exist and why in `docs/`, so later milestones can trace evidence back to an exact document and location.

Scope, format and data fields must be confirmed with the user before any implementation.

**Open questions (carried forward):**
- Confirm or change the Milestone 2 scope above.
- Node.js 25 is a short-support release. Consider an LTS version before the frontend milestone.
- No software licence has been chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
source .venv/bin/activate
python -m resauce
pytest        # expect: 1 passed
```

---

## 2026-11-07: Milestone 1 verification and project move

**Status:** Milestone 1 re-verified. The program runs and `pytest` reports 1 passed.

**Done:**
- A verification run found `python -m resauce` and `pytest` failing with "No module named resauce", even though both had passed at setup.
- Cause: the project was in `~/Documents`, which iCloud syncs. macOS added the "hidden" flag to `.venv/`, and Python 3.14 skips hidden `.pth` files. That broke the link to `src/`. The code itself was fine: with `PYTHONPATH=src` the program ran and the test passed.
- Moved the project to `~/Projects/ReSauce`, which is not synced, and rebuilt `.venv`. All checks pass.

**Decisions & why:**
- Keep the project out of iCloud-synced folders. Syncing also risks conflicts inside `.git/` and `.venv/`.

**How to verify:**
```bash
cd ~/Projects/ReSauce
source .venv/bin/activate
python -m resauce
pytest        # expect: 1 passed
```

---

## 2026-11-07: Milestone 1, project foundation

**Status:** Milestone 1 complete. The project installs, the program runs, and the one test passes.

**Done:**
- Renamed the project from "Elenchra" to "ReSauce".
- Created a Git repository on branch `main`.
- Created the Python project: `pyproject.toml`, the `src/resauce/` package and `tests/`.
- Added a minimal program (`python -m resauce`) that prints the project name, version and Python version. It contains no scientific or medical logic.
- Added one automated test (`tests/test_main.py`).
- Added `CLAUDE.md`, `README.md`, `.gitignore` and this file.

**Decisions & why:**
- Python's built-in `venv` with `pip` and `pyproject.toml`: already on the machine, the most standard approach, and nothing has to be installed system-wide.
- `pytest` is the only dependency. It is the most widely used Python testing tool.
- "src layout": the scientific core sits in `src/resauce/`, separate from the future web interface.
- `requires-python >=3.13`: the machine has Python 3.14.3 (Homebrew, used for `.venv`) and 3.13.12 (python.org).
- Deliberately not added yet: uv, conda, Poetry, Docker, linters, CI and web frameworks. Add them only when there is a real need.

**Environment found:** macOS 26.6.2 (Apple Silicon), Git 2.50.1, Python 3.14.3, Node.js 25.8.0 and npm 11.11.0 (not used yet), and VS Code with the Python extension.

**Next steps:**
- Define Milestone 2 with the user. Pipeline step 1 (reading synthetic documents and research records) is the natural starting point.

**Open questions:**
- Node.js 25 is a short-support release. Consider a long-term-support (LTS) version when the frontend milestone starts.
- No software licence has been chosen yet.

**How to verify:**
```bash
source .venv/bin/activate
python -m resauce
pytest        # expect: 1 passed
```
