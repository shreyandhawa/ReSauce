# Review of `docs/evolution-handoff.md` and coordination notes

- **Date:** 2026-11-09
- **Status:** not yet applied to the handoff. Read this together with `docs/evolution-handoff.md` before building.
- **Source:** an independent review by a separate agent that saw only the handoff and the code, not the discussion that produced the plan. Its claims were spot-checked against the files. Some of its line numbers are approximate.

## 1. Coordination: state of the branches (checked 2026-11-09 ~09:00 CT)

| Branch | Tip | Note |
|---|---|---|
| `main` (origin) | `a1fb712` "Results: explain why Baseline B … scores higher" | |
| `feature/verification-engine` (origin) | `c73dc11`, the same Results change as `a1fb712`, committed on top of the handoff commit `14739a1` | Unrelated work landed on the feature branch. Expect a duplicate-change merge later; the `web/dist/` asset hashes may conflict. |
| `v2-architecture` (origin) | `98bd60e` "Add pipeline v2 line: text clean-up before extraction" | **Overlaps this plan.** It adds `src/resauce/v2/` and changes `app/pipeline.py`, `app/server.py`, `app/workstation.py`, `web/src/api.js` and `CaseWorkspace.jsx`, the same server and API files this plan extends. |

Proposed working agreement (to confirm with the user):
1. Only verification-engine work is committed on `feature/verification-engine`. Other fixes go to `main` (or their own branch).
2. Decide whether this plan builds on `main` or on `v2-architecture`. If v2 merges first, rebase this branch onto it before Phase 3 (server and API).
3. New engine code stays in new files (`src/resauce/verify/`), which do not clash with `src/resauce/v2/`. Shared files (`app/server.py`, `app/workstation.py`, `web/src/api.js`, `web/src/App.jsx`) are edited by one agent at a time.
4. Two agents never run git commands in this folder at the same time.

## 2. Verdict

**Sound with changes.** The freeze strategy and outcome rules hold. Fix the outcome semantics for link-dependent rules, the server's stream entry point and the time plan before building.

## 3. Errors in the handoff

1. **Go/no-go at "minute ~110" is wrong.** Phases 1 and 2 end at minute 80, and the four phases add up to 180, so the ICANS adapter has no time. Move it to a later session.
2. **`app/findings.py` cannot be the template for "passed".** `findings()` skips clear categories (7.6/7.7, findings.py ~line 112). It also ignores `role` on evidence and leaves out `review_items` and `other_flags`.
3. **`_stream` (app/server.py ~91-94) catches only `NotFound` before the first event.** A `BadRequest` from the body or the mapping drops the connection with no message. Mid-run errors are sent as `{"event":"failed"}`, not `module_failed`.
4. **`api.stream` (web/src/api.js) always sends an empty `'{}'` body**, so a run request cannot carry the mapping until it is changed.
5. **`Network.jsx` is coupled, not only `layout.js`.** It imports `PATH`/`onHop` (runner.js) and `COLUMN`/`NODE_INFO` (route.js). Its renderer is not reusable as is; `signals.js`, `parts.jsx` (marks/beacon) and `motion.js` are.
6. **`DESIGN.md` conflicts with the new brief.** It specifies a full-bleed **black stage** (§ around line 109) and **blue** for the selected path (line ~130). The owner's new brief asks for a white background and "no blue light". **Open decision for the user.**

## 4. Risks and required changes, most severe first

1. **Checks that wrongly show as passed.** Add a rule to §5: anything unparseable, ambiguous, zero-row, or from a failed module is **unverifiable**.
   - Link resolution is one shared function in `mapping.py` that returns exactly-one / none / many.
   - B2 with two candidate events of the same type is **ambiguity → unverifiable**, not discrepancy.
   - State on purpose why an orphan is unverifiable but a duplicate identifier is a discrepancy.
2. **Finding granularity.**
   - Discrepancy and unverifiable findings are per row, keyed by dataset + row number, never by key values (keys can be empty or duplicated).
   - Passed findings are one per rule per dataset, with a row count.
   - The expected fixture lists every knock-on finding, e.g. an orphan AE report also makes C3, D1 and D2 unverifiable.
3. **Server and API.**
   - Import writes the files to `workspace/datasets/<id>/` with SHA-256 hashes.
   - The run takes `{import_id, mapping}`; read and validate the body **before** the stream starts.
   - Add `POST /api/checks/demo`.
   - Each run stores the file hashes and the mapping, for provenance.
   - Note: a file picker can read any file on the computer, which departs from the "folders inside the project only" rule (`app/workspace.py`). Say so in the docs.
4. **Phase 3 (65 min) will overrun.**
   - Reuse `parts.jsx` marks.
   - The mapping step is a "confirm the suggestions" form.
   - Put the new view at its own route `#/verify`; `App.jsx` hard-wires `#/pipeline` in several places.
   - New cut order: ICANS adapter (do not start) → travelling signals → replay pacing → upload of own files (keep the demo) → module D.
5. **Integrity rules (`CLAUDE.md`).**
   - The C2 window and A4 "grades 0–5" are clinical choices: label them `[OPERATIONAL]` as `engine.py` does.
   - C2 stays unverifiable until a window is supplied in the mapping request.
6. **Naming.** Rename `verify/engine.py` → `verify/coordinator.py` (next to the frozen `engine.py`), and use `/api/checks/*` instead of `/api/verify/*` (next to the existing `/api/verify-all`). The freeze test cannot match files in subfolders, so this is about clarity, not breakage.

## 5. Edits to apply to the handoff

- §4.1:
  - `Evidence.kind` is `cell` | `quote`, with optional `document_id`, `version`, `start`, `end`, `quote` and `role`.
  - `records` may be empty for document-based findings.
  - `finding_id` is built from dataset + row number.
- §4.3: `run(tables, mapping, modules=REGISTRY)`, so an adapter living in `app/` can be injected. A failed module emits one unverifiable finding per rule.
- §4.4:
  - Fix the JSON contradiction: "a top-level array" vs the gate's object form. Pick the object form.
  - The CSV gate also requires the `FICTIONAL_NOTICE` text.
  - Add `verify/__init__.py` to the tree.
- §5:
  - Add a column for unparseable / ambiguous / zero-row cases (all unverifiable).
  - Rename module D to **cross-check**, because "evidence" means quoted text in this product.
- §7: generate the demo data with a deterministic, seeded script that writes both the CSVs and the expected fixture.
- §8: schedule the demo endpoint, the `api.stream` body change, the new `data-format.md` section and `/code-review` (`CLAUDE.md`).
- §9: depends on the user's design decision (§3 item 6).
- §10.8: also check that the case view, New case and Export still work.

## 6. Keep as is

- New files only, so the freeze test is unaffected.
- No new dependencies; Parquet deferred.
- Unverifiable is never shown as passed.
- A suggested link is never applied without confirmation.
- No invented delays.
- The expected answers live in `tests/`, not `data/`.
- Symbol + word + colour.
- Narrow test scope.
