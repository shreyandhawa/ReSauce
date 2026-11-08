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

## 0. Project plan (user decision, 2026-11-08 07:00)

This replaces the earlier plan of a 3 to 4 hour time box. No "§0 time box" existed in this file before (session 3 noted the same), so there was nothing to delete; this section is the plan from now on.

1. Session 5 (Baseline A and evaluation runner): done.
2. Session 4b: remaining engine rules and extractor gaps.
3. Step 5a: blind answers for the 72 dev-v1 cases.
4. Freeze the pipeline (tagged commit).
5. Step 6: 153 locked cases in a separate private repo, written without access to ReSauce `src/`.
6. Step 5b: blind answers for the locked set, plus adjudication.
7. Baseline B, only if an API key is set up.
8. Final evaluation, once, on the locked set.
9. Session 6: viewer, README, demo script.
10. Rubric extras: cited sources, an untested path-to-impact section, real user feedback recorded as given.

**Held-out labelling:** the session 5 held-out run is the only one made before later pipeline changes. Any later held-out numbers are labelled "seen" (the pipeline has changed since the first run, and the cases are no longer unopened).

---

## 2026-11-08: Step 5a close-out fix (blind-run notes and unclear rules)

- **Status:** the real blind-run report is saved as `reference/dev-v1/independent-run-notes.md` (exactly as given). `comparison.md` §8 lists every unclear rule, one line each with batch and case ID: 13 format gaps (8 settled by a Value convention in `reference/dev-v1/README.md`, 5 open; item 6 is settled for `documented_value` but not for `difference_note`) and 17 rule gaps. `tools/compare_answers.py` produces the same §8; sections 1 to 7 of `comparison.md` are unchanged (checked with `git diff`: one changed hunk, in §8). `src/`, `clinical-methods.md`, `results/` and all answers untouched. The entry below (pipeline frozen) said the notes file was missing; that is corrected there.
- **Clinician open items (rule gaps; numbers are those in `comparison.md` §8; none were listed before):**
  - 14, 15: does "ICE not done, patient off the unit / away from the ward" count as a documented not-assessable period (§7 intro, A7)? (SYN-0011, SYN-0030)
  - 16: how many minutes is "about the same time" in §6.4? (SYN-0009; the answer used 30)
  - 17: can an explicit clinician attribution itself be read as ambiguous under §7.5? (SYN-0029)
  - 18: does a general line such as "A: ICANS post CAR-T" attribute a specific finding (A9)? (SYN-0047; if yes its grade becomes 7.7)
  - 19: does treatment given before the finding remove a competing cause (A30, A35)? (SYN-0063)
  - 20: when does a documented language barrier invalidate an ICE (A10)? (SYN-0069)
  - 21, 22: does an excluded or ungradeable symptom (headache; a symptom with no ICE total) block 7.7 (§7.9(b), A21)? (SYN-0004, 0009, 0038)
  - 23: is subdural or other intracranial hemorrhage a competing cause (A35)? (SYN-0054)
  - 24, 25: is "awakens spontaneously, not drowsy" plus ICE 10/10 a formal Grade 0 assessment, and is the same with drowsiness a gradeable finding for onset (A3, §3.3)? (SYN-0024, SYN-0055)
  - 26: does a changed date in copied-forward text after a documented resolution show a new observation (A31)? (SYN-0034)
  - 27, 28: §7.6(c): does a record version made after the documents count as "revision without new documentation", and can a later general summary support the changed value? (SYN-0027; Batch 5, no case ID given)
  - 29: does a relative-time range containing an earlier formal Grade 0 on the record date count as two readings or one range (§7.5, A26)? (SYN-0060)
  - 30: may a documented resolution then recurrence be split into two episodes when the record looks like a deliberate second onset (A5)? (SYN-0068)
- **Answer-format open items (format gaps with no Value convention yet):**
  - 4, 5, 6: `signed_difference_days` (and, for 6, `difference_note`) for a 7.5 onset (SYN-0023, SYN-0046, SYN-0063).
  - 11, 12: evidence for an out-of-scope case when no note states the trigger (SYN-0001 age only in `case.json`; SYN-0049 record value).
  - 13: where `derivation` goes (top level in 60 files, inside each field in 12).
- **Next steps:** the user decides the format items before the locked answers are written (Step 5b); the rule gaps go to the clinician with A19 to A34. Step 6 as planned.
- **How to verify:** `.venv/bin/python -m tools.compare_answers` then `git diff reference/dev-v1/comparison.md` shows no change; `.venv/bin/python -m pytest -p no:cacheprovider -q` passes.

---

## 2026-11-08: Step 5a close-out and Step 4 (pipeline frozen)

- **Status:** Step 5a is closed and the pipeline is frozen. Tag `pipeline-freeze-v1` is on commit `7c4a449` ("Step 4: pipeline freeze"); the frozen source and the evaluation are at `ec7519e`. `pytest`: 176 passed. `python -m resauce.evaluate` was run once (dev and held-out), 0 method errors.
- **Done:**
  - **Corrected afterwards (see the entry above):** the first save of `reference/dev-v1/independent-run-notes.md` was the wrong text (a message saying the notes were missing). It was replaced by the real blind-run report, and `comparison.md` §8 now lists 30 items. The statements in this entry that the notes file was missing, that §8 had no lines and that no rule gaps were added are no longer true.
  - Adjudication (decided by the user): no category disagreements (144 of 144; the 4 out-of-scope cases differ only in reason wording), no real value disagreements. The intended answers stay the reference, unedited.
  - `reference/dev-v1/README.md`: new "Value conventions (from Step 5a)" section (grade 0 or undetermined, 7.5 and 7.4 fields, unchanged record history, five fixed out-of-scope strings: `age under 18`, `CAPD assessment`, `record Grade 5`, `documented death`, `developmental delay`, the strings the engine uses).
  - Reference label changed in `docs/evaluation-spec.md` §2 and in `evaluate.py` to "intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); not clinician-verified".
  - `evaluate.py`: `--split-name NAME --data DIR --reference DIR` scores every case folder in DIR as one split called NAME (no `splits.json`). It writes `<out>/NAME.json` and `<out>/report-NAME.md` (so `report.md` is never overwritten). No scoring rule changed. The held-out section now says "seen: the pipeline changed after the first held-out run (commit 4ff6c5f)". One test added.
  - Also corrected one sentence in the report's limitations (spelling variants are now handled since session 4b; see "Open" below). `docs/freeze.md` and `tests/test_freeze.py` (recomputes the SHA-256 of the seven frozen files) added.
- **The freeze rule** (`docs/freeze.md`): frozen are `loader`, `models`, `extract`, `phrases`, `engine`, `timeline`, `baseline_a` (hashed) and the scoring rules of `evaluate.py` (protected by the rule, not hashed). Allowed after the freeze: new files (e.g. `baseline_b.py`) and `evaluate.py` changes that only add a method or a split. A change to a frozen file breaks the freeze and must be disclosed with every later result.
- **Headline numbers, quoted from `results/report.md`** (synthetic data, intended answers not clinician-verified, not clinical validation; combined onset and grade fields):
  - **Dev (20 cases), optimistic because the pipeline was built from these cases:** ReSauce precision 1.00 (10/10), recall 1.00 (10/10), exact agreement 1.00 (38/38). Baseline A precision 0.90 (9/10), recall 0.90 (9/10), exact agreement 0.87 (33/38).
  - **Held-out (52 cases, in-repo, not sealed; seen: the pipeline changed after the first held-out run, commit 4ff6c5f):** ReSauce precision 0.84 (16/19), recall 0.80 (16/20), exact agreement 0.86 (84/98); 5 "review: …" results; 3 false alerts, 4 misses. Baseline A precision 0.61 (14/23), recall 0.70 (14/20), exact agreement 0.65 (64/98); 9 false alerts, 6 misses. Out of scope: 3 of 3 flagged with the matching reason.
  - The score tables are the same as in the run before this entry; only the evidence counts, label and commit differ. Not yet run: Baseline B.
- **Decisions & why:**
  - One commit for A–B plus results, as asked. So the run metadata in `results/` says "uncommitted changes in code or data: yes" and names the previous commit (`c03e7a4`); the code was committed immediately after in `ec7519e`.
  - The `--split-name` report goes to `report-NAME.md` so a locked run cannot overwrite the dev/held-out report.
  - Out-of-scope strings follow the engine and the intended answers, not the longer wording of the independent answers.
- **Next steps:** Step 6: write the 153 locked cases in a separate private repo, without access to ReSauce `src/` (§0). Then Step 5b (blind answers for them), Baseline B if an API key exists, and the final evaluation once on the locked set with `--split-name locked`.
- **Open questions:** (1) (answered: the notes file is now saved) (2) The sentence in `docs/evaluation-spec.md` §6 about misspelt words is still the old one (it is outdated since session 4b); `docs/` is not frozen, so it can be corrected. (3) The limitation lines "answers are not independently verified" in `evaluation-spec.md` §6 now partly conflict with the new label; the report text was left as is. (4) Clinician items from session 4b and the assumptions A19 to A34 are still unanswered.
- **How to verify:**
  ```bash
  .venv/bin/python -m pytest -p no:cacheprovider -q    # expect 176 passed
  git show pipeline-freeze-v1 --stat | head            # the tag exists
  shasum -a 256 src/resauce/engine.py                  # compare with docs/freeze.md
  ```

---

## 2026-11-08: Step 5a (independent answers and comparison)

- **Status:** 72 independent (blind) answers are in `reference/dev-v1/independent/` and compared with the intended answers by `tools/compare_answers.py`; the result is `reference/dev-v1/comparison.md`. Nothing in `src/` changed, no tests added (tool only), `pytest` and `python -m resauce.evaluate` not run. No answer file was changed. Nothing is adjudicated yet.
- **How the independent answers were made (as reported by the user in the task; I did not see the run):**
  - Written by Claude Opus in a separate folder, `~/Projects/ReSauce-blind`. It held only the cases, `clinical-methods.md`, `data-format.md` and the answer-format README. It held no intended answers, plan, briefs, handoff, code or results.
  - 72 cases in 6 batches of 12, each batch in a separate subagent. The run was interrupted by a usage limit and resumed.
  - The provenance of the first five batches' files does not record the model. The user states all 72 were written by Opus.
  - Batch 3: the subagent saw only the header lines (format, case_id, kind, status) of `answers/SYN-0001.json`, no answer content. Batch 6: the first subagent hit a rate limit and wrote nothing before a fresh one ran.
  - The files are not uniform: `derivation` is a top-level object in 60 files and written inside each field in 12; `documented_value` for 7.4, 7.5 and no-ICANS fields is written as an "undetermined" object, "none found", `null`, a range or grade 0.
- **Problems found when starting:**
  1. The 72 answers were in `~/Projects/ReSauce-blind/answers/`, not in `reference/dev-v1/independent/`. I **copied** them (byte-identical, checked with `diff -r`); the originals are untouched.
  2. `reference/dev-v1/independent-run-notes.md` does not exist (not in the repo, not in the blind folder, not found by a disk search). So it was not read or committed, and the list of "unclear rules" (format gap / rule gap) was **not produced**; `comparison.md` §8 says so. The batch 3 and batch 6 facts above come from the task text, not from that file. **Needs the user:** supply the notes file; the section can then be added.
- **Result (numbers exactly as `comparison.md` shows them; synthetic data, neither side clinician-verified):**
  - All 72 cases: out of scope 72 of 72 agree; onset category 72 of 72 agree; max grade category 72 of 72 agree; category overall 144 of 144 agree.
  - Documented value, where both sides are in scope: onset 68 cases: 67 agree, 1 differ only in form, 0 real disagreement; max grade 68 cases: 64 agree, 4 differ only in form, 0 real disagreement; overall 136 comparisons: 131 agree, 5 differ only in form, 0 real disagreement.
  - Dev split (20 cases): category 40 of 40 agree; value 38 comparisons: 37 agree, 1 form only, 0 real. Held-out split (52 cases, not sealed): category 104 of 104 agree; value 98 comparisons: 94 agree, 4 form only, 0 real.
  - Evidence quotes: 451 checked, 0 not found exactly once. Files missing, unreadable or incomplete: none.
  - The 5 form-only rows: SYN-0016 (intended Grade 0, independent no value), SYN-0018, SYN-0047, SYN-0069 (intended "undetermined", independent a grade range) and SYN-0063 (onset: independent "undetermined", intended a date). All five are in categories that agree.
- **Decisions & why:**
  - Out-of-scope "same reason" is judged by which of the five §5 triggers the text names (the two sides word it differently); both texts are shown.
  - Value groups follow the task: agree / form only (a grade or date missing on one or both sides, or written differently) / real. A grade or date present on one side only counts as "form", as instructed, so those five are listed in `comparison.md` §7 for a person to look at, not dismissed.
  - Two "undetermined" values with different reason text count as agreeing. `signed_difference_days` is not compared.
  - Check of the tool: a temporary copy with one category and one grade changed was flagged as one category row and one real-value row; the temporary copy is not kept.
- **Caution:** complete agreement is between two answer sets written by Claude models from the same rules text. It shows the rules are applied consistently by them, not that either is clinically right. The shared assumptions (A19 to A34) still await the clinician.
- **Next steps:** adjudication (decide the 5 form-only rows and anything the clinician must settle), then freeze the pipeline (§0). Add the "unclear rules" section once the notes file is available.
- **Open questions:** where is `independent-run-notes.md`?
- **How to verify:**
  ```bash
  .venv/bin/python -m tools.compare_answers   # rewrites reference/dev-v1/comparison.md; expect 0 file and 0 quote problems
  diff -r ~/Projects/ReSauce-blind/answers reference/dev-v1/independent   # expect no output
  ```

---

## 2026-11-08: Milestone 3 session 4b (remaining engine rules and extractor gaps)

- **Status:** engine and extractor gaps from session 4 and 3 are closed or listed. `pytest`: 174 passed. Only the 20 dev cases and their intended answers were opened (a scratch script read `reference/dev-v1/splits.json`). `python -m resauce.evaluate` was **not** run; `results/` is unchanged. No case IDs in `src/`. The session 5 held-out run is still the only run made before these pipeline changes; later held-out numbers must be labelled "seen" (§0).
- **Done, engine (`engine.py`):**
  - Items with no rule in clinical-methods now return **"review: no rule (§3.3: …)"**, only when the choice would change the category (A23 logic unchanged): edema with no stated extent (options Grade 3 or 4), posturing not named decerebrate or decorticate, status epilepticus with no stated duration, a seizure duration range that spans 5 minutes, and motor findings other than hemiparesis, hemiplegia, paraparesis and paraplegia (weakness, focal weakness, drift, monoparesis, quadriparesis …).
  - **Fix:** plain "posturing" used to be read as Grade 3 or 4. Table 6 lists posturing only at Grade 4 (decerebrate or decorticate), so its options are now "not counted" or Grade 4.
  - **Spelling variants are readings:** a graded finding (consciousness, seizure, motor, ICP) read through a spelling variant has the options "not counted" or "graded as the list word". If that changes the category the result is "review: spelling variant (…)". Otherwise the shared category stands (A23). Variants never count as a confirmed qualifying finding for the unassessed-days flag. Every variant is listed in `review_items`.
  - **§6.5 recurrence** is now compared by moment, not by calendar day: a formal Grade 0 between two findings of the same day is flagged when the times show the order; without times there is no flag. One episode per infusion within the window is unchanged.
  - **§7.10:** all 13 flags already existed. None was missing, so "one new flag" is the same-day recurrence refinement above.
  - **1024-reading limit:** kept as a backstop, but choices that provably cannot change a result (a later, lower-grade finding with a date after the fixed onset) no longer count towards it. Flags still use all choices.
- **Done, extractor (`extract.py`, `phrases.py`):**
  - "Day 5:" is read as Day +5 (colon required; "Day 5:30" and "day 5 of steroids" are not read).
  - "1900"/"0730" are clock times at the start of a line, after an ISO date or Day +N (optional comma, "at"), or after "at". Not when followed by a unit (mg, mL, units …), joined to a date or another number, or equal to a year of the note, its documentation date or the infusion date.
  - Spelling variants: a word of 6+ letters exactly one letter from a closed-list word (list words of 6+ letters, taken from the finder patterns; no list of misspellings). It counts only if putting the list word in its place makes a finder match, and only one list word does. The observation is always "uncertain" (also when negated, e.g. "no seizre"), with the note "spelling variant of <word>" and `status_without_variant` kept in `details`. "Generalised seizure" is not a variant because "seizure" already matches without a correction.
- **Development check (not a result):** the engine matches the intended category on **40 of 40** fields of the 20 dev cases, the same as before session 4b. Expected to be optimistic (phrase lists and answers were built from these cases). Changes since the session 4 snapshot, one line each: (1) SYN-0027, SYN-0047: the listed readings are fewer, because later lower-grade choices are no longer enumerated (categories, values and evidence identical); (2) SYN-0027: one new review item, "'Infectious' read as a spelling variant of 'infections' (competing_cause); not used as evidence" (a **false variant**: a real word one letter from a list word; context kinds are never used by the engine); (3) SYN-0044: one new review item, "'headace' read as a spelling variant of 'headache'" (an excluded symptom, so no grade effect); (4) SYN-0044 had that typo missed silently before. Nothing else differs.
- **Still "review: …" or not built, and why:**
  - Everything under "no rule" above: clinical-methods gives no rule; nothing was invented.
  - "review: unresolved event date (§6.1)": unchanged.
  - **§6.4 / A13, A31 partial copy-forward:** not built. A31 describes a note that repeats an earlier note; a repeated line such as "ICE 10/10" cannot be told apart from a new assessment with the same result, and the methods give no way to do so. Only whole-note copies are detected. The copy check does not read "1900" as a time (small gap).
  - **Reading limit:** still 1024 readings (after dropping inert choices).
  - Not built at all (unchanged): CTCAE grading and Grade 5 (§8).
  - Variants of competing-cause, attribution, barrier, hemorrhage and out-of-scope words are only listed, never used. So a misspelt sedative can hide a competing cause.
- **Limits of the spelling rule:** swapped letters ("seziure") are two changes and are not matched (decided with the user). Words with optional parts or stems (`unarousable`, `hallucinat…`) are not covered. Misspellings of negation or hedge words are not found. The stored value of a variant is the list word (the quote is always the exact source text).
- **[OPERATIONAL] choices made here (not in clinical-methods; for clinician and user review):** "Day 5:" without a sign; colon-less clock times and their context rule (ISO dates and Day +N only, so "03/06/2030 0730" is not read; "Day 5: dexamethasone" is read as study day +5); the spelling rule; same-day ordering for the recurrence flag by time; dropping inert choices from the readings.
- **New clinician questions:**
  - Should generic or focal weakness, monoparesis or quadriparesis map to Table 6 Grade 4? (still unanswered from session 4)
  - Edema with no stated extent: Grade 3, Grade 4, or neither?
  - Posturing not named decerebrate or decorticate: Grade 4, or not graded?
  - Status epilepticus without a duration: does it mean the Grade 4 ">5 minutes" criterion?
  - A seizure duration range that spans 5 minutes (for example "3 to 6 minutes"): which grade?
  - Should a repeated assessment line in a later note (partial copy-forward) be treated as copied?
  - Should a misspelt word ever count as a certain finding if the same note repeats it correctly spelt elsewhere?
- **Docs to update later (not edited, outside this commit's scope):** `docs/evaluation-spec.md` §6 still says misspelt finding words are missed without a warning; that is no longer true.
- **Next steps:** Step 5a (blind answers for the 72 dev-v1 cases), then freeze the pipeline (§0).
- **How to verify:**
  ```bash
  .venv/bin/python -m pytest -p no:cacheprovider -q                 # expect 174 passed
  .venv/bin/python -m resauce.extract data/dev-v1/cases/SYN-0044    # 'headace' is uncertain, note "spelling variant of headache"
  .venv/bin/python -m resauce.engine data/dev-v1/cases/SYN-0044     # review_items lists the variant
  ```

---

## 2026-11-08: Evaluation re-run after scoring fix (pipeline unchanged)

**Bug:** `reference_class()` in `src/resauce/evaluate.py` returned None for reference categories written with a reason, e.g. "7.5 (attribution)". Those fields were silently left out of the class counts and exact agreement. Fix: score by the leading code (full text kept in the per-case output); a reference category that is not 7.1 to 7.9 (in-scope cases) is now a reference error, listed in the report. A first version of the fix wrongly rejected "out of scope (…)" categories; fixed in a second commit. Two focused tests plus one for that case. Engine, extractor, phrases and Baseline A unchanged.

**Numbers changed (old → new, from results/report.md), held-out split (the other split's tables did not change):**
- Review-class fields, ReSauce onset / max_grade / combined: 8 / 5 / 13 → 11 / 7 / 18. Baseline A: same.
- Baseline A review results: onset 5 → 8, max_grade 3 → 4, combined 8 → 12.
- ReSauce exact agreement, all fields: onset 0.78 (38/49) → 0.84 (41/49); max_grade 0.84 (41/49) → 0.88 (43/49); combined 0.81 (79/98) → 0.86 (84/98).
- Reference category 7.5 fields: 2 → 7 (of which a review flag: 1 → 6).
- Unchanged: precision, recall, F1, detections, misses, false alerts, positive-only agreement, out-of-scope results.

Not checked: which split each table above belongs to was read from line positions in the report; confirm against results/report.md. Results are on synthetic data with unverified intended answers, not clinical validation.

**Next steps:** none from this fix.

---

## 2026-11-08: Milestone 4 (reduced), session 5 (Baseline A and evaluation runner)

- **Status:** Baseline A (`src/resauce/baseline_a.py`) and the evaluation runner (`src/resauce/evaluate.py`, `python -m resauce.evaluate`) are built. The official run happened once, after the code commit `aca0884` was pushed. Results are in `results/report.md`, `results/dev.json` and `results/held_out.json`. `pytest`: 163 passed. I opened only the 20 dev cases and their intended answers. Held-out cases and answers were touched only by the runner; I did not open `results/held_out.json`, only `results/report.md`. Nothing in the engine, extractor, phrase lists or Baseline A was changed after the held-out numbers appeared.
- **Done:**
  - `baseline_a.py`: evaluation-spec §4. It uses the same extractor observations (status `present` only), the latest version of each document whether signed or not, the `documented_at` date as the time, the current record version only, no window, no attribution. It grades only the §4 sources and outputs only 7.1/7.2/7.3/7.7/7.8. It has its own Table 6 constants (it does not import the engine). It outputs the same field format as the engine.
  - `reference/dev-v1/splits.json`: the 20 dev IDs. The held-out split is every other case folder. `src/` contains no case IDs.
  - `evaluate.py`: scoring per evaluation-spec §3 as pure functions (`score_method`), run per split, with the results written to `results/<split>.json` and `results/report.md`. A method error on a case is recorded as "error" with the message, counted, and the run carries on. Neither split had any.
  - Tests: 6 scoring tests, plus 1 for an errored case (`tests/test_evaluate.py`), and 4 small Baseline A tests (`tests/test_baseline_a.py`; the task said "scoring only", but Baseline A decides answers, so CLAUDE.md allows them).
- **Choices where §4 was silent** (all [OPERATIONAL], for review):
  1. Partial ICE counts only if all five items are scored; the extractor's item sum then acts as the total ("same ICE parsing"). Otherwise it is not graded.
  2. ICE 0 → Grade 3, as the §4 table says, with no consciousness context (ReSauce's A33 is not applied).
  3. Hemiplegia and paraplegia count with hemiparesis and paraparesis (Grade 4). §4 names only the "-paresis" words.
  4. No hemorrhage exclusion for edema (§4 has no exclusion step).
  5. A seizure is Grade 4 only when it is documented as over 5 minutes (a lower bound above 5 minutes, or "over 5 minutes") or repetitive without return to baseline. A range that starts at 5 minutes, an unstated duration and "status epilepticus" without a duration stay Grade 3.
  6. "Awakens spontaneously" is Grade 1 with no drowsiness condition (that is ReSauce's A3).
  7. The 7.8 check comes before "no finding → 7.7", following the order of the §4 list.
  8. `documented_value` is "none found" when there is no Grade 1+ finding.
- **Choices in the runner where evaluation-spec §3 was silent** (also stated in the report):
  - An errored case counts its positive fields as misses (and its fields as disagreements), so a method cannot look better by crashing. There were none in this run.
  - F1 = 2PR/(P+R), written with counts as 2·det ÷ (2·det + false alerts + misses). It is 0 when there are no detections but precision and recall are both defined, and undefined when either is undefined.
  - Evidence validity is checked over every evidence reference in a method's output, including out-of-scope cases and flags.
  - An out-of-scope reason matches the reference after lower-casing and trimming whitespace.
  - Reference out-of-scope cases are not scored for Baseline A at all.
- **Test change to flag:** `tests/test_tools.py::test_core_does_not_use_tools_or_reference` forbade any mention of `reference/` in every module of `src/resauce`. I exempted `evaluate.py` only, because it is the sanctioned reader of reference answers (`reference/dev-v1/README.md`), and I added assertions that no other module mentions or imports `resauce.evaluate`. Please check you agree.
- **Headline counts, exactly as `results/report.md` shows them** (fields; each in-scope case has onset and maximum grade; combined = both fields pooled; the splits are not pooled):

  | Split | Method | Positive | Detections | Misses | False alerts | Alerts on review fields | "review: …" | Precision | Recall | F1 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | dev (20 cases: 19 in scope, 1 out of scope) | ReSauce | 10 | 10 | 0 | 0 | 0 | 0 | 1.00 (10/10) | 1.00 (10/10) | 1.00 (20/20) |
  | dev | Baseline A | 10 | 9 | 1 | 1 | 1 | 0 | 0.90 (9/10) | 0.90 (9/10) | 0.90 (18/20) |
  | held-out (52 cases: 49 in scope, 3 out of scope; in-repo, not sealed) | ReSauce | 20 | 16 | 4 | 3 | 1 | 5 | 0.84 (16/19) | 0.80 (16/20) | 0.82 (32/39) |
  | held-out | Baseline A | 20 | 14 | 6 | 9 | 8 | 0 | 0.61 (14/23) | 0.70 (14/20) | 0.65 (28/43) |

  - Exact-category agreement, all in-scope fields / positive fields only: dev ReSauce 1.00 (38/38) / 1.00 (10/10); dev Baseline A 0.87 (33/38) / 0.90 (9/10); held-out ReSauce 0.81 (79/98) / 0.80 (16/20); held-out Baseline A 0.65 (64/98) / 0.70 (14/20).
  - Held-out ReSauce misses: 4, of which 2 got a review flag (7.4/7.5) and 2 got a "review: …" result. Held-out Baseline A misses: 6, none with a review flag (it cannot give one).
  - Out of scope (ReSauce): dev 1 of 1 flagged with the matching reason; held-out 3 of 3 flagged with the matching reason; 0 in-scope cases wrongly flagged on either split.
  - Evidence-quote validity: 1.00 on both splits for both methods (dev 135/135 and 68/68; held-out 391/391 and 147/147).
  - Errors: 0 on both splits for both methods.
  - These are scores against intended answers that are not independently verified and not clinician-verified, on synthetic data. They are not clinical validation. The extractor's phrase lists were built from the 20 dev cases, so the dev split is not an independent test of the extractor. The held-out split is not sealed.
- **Not done / open items:**
  - The held-out misses, false alerts and `review: …` results have not been looked at case by case, on purpose (held-out rule). Any error analysis would have to be planned with the held-out status in mind (looking at them would use them up as a held-out set).
  - Misses and review flags are tabled for the combined fields only, not per field.
  - Baseline B (LLM) is still deferred (no API key).
  - Step 5 (independent answers) is still to do. Those answers will replace the intended answers, and earlier results are kept.
  - Clinician review of the Baseline A choices above, and of the open questions from session 4.
- **How to verify:**
  ```bash
  .venv/bin/python -m pytest -p no:cacheprovider -q                 # expect 163 passed
  .venv/bin/python -m resauce.baseline_a data/dev-v1/cases/SYN-0017 # a dev case only
  # results/report.md: the code commit shown is aca0884654fef34582274ea647c353c6ca7ec111
  ```
  Do not re-run `python -m resauce.evaluate` unless a new, recorded run is intended: the run is written over `results/`.

---

## 2026-11-08: Milestone 3 session 4 (rules engine)

- **Status:** `src/resauce/engine.py` + `src/resauce/timeline.py` turn extractor observations into a maximum grade, an onset, a §7 category per field, §7.10 flags and out-of-scope, one result per case in the intended-answer field format. `python -m resauce.engine <case folder>` prints it as JSON. `pytest`: 150 passed. Only the 20 dev cases and their intended answers were opened.
- **Done:**
  - Content (§6.3, A27, A32, A13/A31): latest signed version is current; unsigned content never used ("unsigned later version" / "unsigned document" flags); window per observation; whole-note copy-forward left out; unresolved event dates never given a date.
  - Grading (§3.3–3.4, §4): ICE (ICE 0 by consciousness context, A33), mapped consciousness only ("awakens spontaneously" only with documented drowsiness, A3), seizures (>5 min, repetitive without baseline), deep focal motor, ICP/edema (hemorrhage excludes overlapping edema), excluded symptoms, EEG slowing not graded.
  - Uncertainty as readings: each uncertain finding is a choice; every combination is a reading. Same category in every reading → that category (A23); otherwise the deciding choices give 7.5 (attribution, conflicting assessments, assessment barrier, consciousness wording), 7.4 (A6, A33) or "review: …".
  - Categories §7.1–7.9 incl. record-earlier rule (formal Grade 0 needed), A25, 7.9(a)–(c), 7.8; §7.6 on the last record change (a/b/c) with "revision without new documentation"; flags: outside window, text-only ICP, time-imprecise, relative time, A24, recurrence, superseded-version match, unassessed period, ungradeable symptom. Unparsed extractor text is listed in `review_items`.
  - Extractor: posturing now has the value "decerebrate or decorticate posturing" or "posturing (type not stated)".
  - Docs: evaluation-spec §3 ("review: …" results are neither alerts nor review flags, reported separately) and §4 (Baseline A grades mapped consciousness categories; unmapped words stay ungraded); dataset-plan status line → v0.3.2.
  - /code-review fixes: partial ICE was graded when its range fell in one grade (A6: now never a total); "over 5 minutes" seizures were Grade 3; generic/focal weakness could create a false formal Grade 0; flags without evidence; the reading cap was labelled as §7.5.
- **Development check (not a result):** 40 of 40 field categories match the intended answers on the 20 dev cases; documented values, signed differences and unassessed-day lists also match. No mismatches to explain. This is expected to be optimistic: the extractor's phrase lists were built from these same 20 cases, and the same writer wrote cases and answers. The held-out 52 cases were not run.
- **Rules not implemented** (each returns "review: not implemented (§…)" only when it would change the category; none was triggered on the dev cases):
  - §3.3: edema with no stated extent; posturing not named decerebrate/decorticate; motor findings other than hemiparesis/hemiplegia/paraparesis/paraplegia (weakness, focal weakness, drift, monoparesis …); status epilepticus with no stated duration; a seizure duration range that spans 5 minutes.
  - §6.4 / A13, A31: partial copy-forward (only whole-note copies are detected).
  - §7.5 readings above 1024 combinations (an engine limit).
  - Not built at all: CTCAE grading (§8, out of scope), Grade 5 (§8).
  - Separate review result: an unresolved event date that would change a category → "review: unresolved event date (§6.1)".
- **Decisions & why** (all [OPERATIONAL], for clinician review):
  - A clinician statement settles attribution only if it is in the same clause as the finding (naming ICANS keeps it; naming a listed cause or "unrelated" excludes it). A general "A: ICANS" line elsewhere settles nothing, so it cannot hide a competing cause.
  - A competing cause applies to every finding near it, ICE included. The §7.5 lorazepam example keeps ICE 8, so the engine gives one more reading than the example (same category). Cautious choice, as A30.
  - Only competing causes with status present count ("r/o infection" does not).
  - Conflicting assessments: ICE totals from different documents within 60 minutes with different grades.
  - An "assessment" (for ICE 0 context, A3 drowsiness, formal Grade 0) = same document version, same event date.
  - Onset ranges come only from A26 range phrases ("overnight"); a documentation-time date is a single date flagged time-imprecise (§6.1).
  - Out-of-scope mentions (CAPD, death, developmental delay) count in any document version, signed or not.
- **Next steps:** Baseline A implementation and scoring code (evaluation-spec §3–4) on the dev split, then the held-out split reported separately; Step 5 independent answers.
- **Open questions for the clinician:**
  - The extractor's own date rules d (date earlier in the line) and e (note header) are ReSauce choices, not §6.1 rules.
  - Unmapped consciousness words (drowsy, sleepy, lethargic, somnolent, obtunded) are never graded; they only serve as A3 drowsiness context. They need an approved mapping (A15).
  - Should generic or focal weakness ever map to Table 6 Grade 4?
  - The attribution-statement rule, the 60-minute conflict window and present-only competing causes above.
  - Does a competing cause such as a sedative affect the ICE score too, or only depressed consciousness (§3.4 vs the §7.5 example)?
- **How to verify:**
  ```bash
  .venv/bin/python -m pytest -p no:cacheprovider -q                 # expect 150 passed
  .venv/bin/python -m resauce.engine data/dev-v1/cases/SYN-0017     # grade 7.2, documented Grade 3 (ICE alone too low)
  .venv/bin/python -m resauce.engine data/dev-v1/cases/SYN-0047     # grade 7.5, reason attribution (lorazepam)
  ```

---

## 2026-11-08: Milestone 3 session 3 (evaluation spec, rule-based extraction)

- **Status:** `docs/evaluation-spec.md` v0.1 is written before any results exist. `src/resauce/extract.py` + `src/resauce/phrases.py` form the first pipeline stage (deterministic, standard library only, no grading). `pytest`: 123 passed. Only the 20 dev cases and their intended answers were opened.
- **Done:**
  - Evaluation spec: dev split = the 20 cases, held-out (in-repo, not sealed) = the other 52, reported separately. Scoring per plan §8.3, which also settles its three open points. Baseline A (conventional validation on the same extraction output). Baseline B deferred. Limitations.
  - `dataset-plan.md`: v0.3.2 changelog line only (the user no longer skims dev cases).
  - Extractor: observations of 16 kinds, each with document, version, signed status, offsets, exact quote (checked with `check_evidence_ref`), status (present / absent / uncertain), event time and its source.
  - Dev results (scratch check, not committed): 462 observations; 104 of 104 intended-answer evidence quotes are covered by an observation; 5 clauses unrecognised ("call if ICE drops below 7", "provider informed of ICE change", "arousal reduced beyond what the ICE score alone shows", 2 × "ICE decline after CAR-T"); 1 unresolved time (SYN-0006-D05 "headache 2/10" inherits a time from a "yesterday" clause, which lands after the documentation time).
- **Decisions & why:**
  - User (this session): no "§0 time box" exists in this file, so the session proceeded without one. Added assessment barriers (A10) and out-of-scope mentions (§5/A29). Plan edit = changelog line only, so the plan's status line still says v0.3.1 (the evaluation spec says so).
  - Time rules d (date or time earlier in the same line) and e (note header) are [OPERATIONAL] choices, not §6.1 rules. Two different dates or two different A26 phrases in a clause → "unresolved", except when one date sits right next to the finding ("8/10 on DATE").
  - Negation: "not" stops at a comma; list negations ("no X, Y, Z") cross commas. "ICE drops / change / decline" are no longer treated as non-scores, so they surface as unrecognised instead of vanishing.
  - Consciousness words with no approved mapping (drowsy, lethargic, somnolent, obtunded) are reported with empty candidates (A15 gives no mapping).
  - Fixed after /code-review: relative-phrase choice by table order, comma negation, over-broad "not assessable", "repetitive" from unrelated words ("multiple myeloma"), item scores lost when a total appeared elsewhere.
- **Next steps:** rules engine (onset, grade, categories, flags) on the extraction output; Baseline A implementation; OOS by age and record Grade 5 (not extraction); Step 5 independent answers.
- **Open questions:**
  - Known extractor limits: misspelt words are missed silently (e.g. SYN-0044 "headace"); unsigned study days ("Day 5:") are not read as dates; 4-digit times without a colon ("1900-2300") are not read.
  - Review follow-ups not done (judgement calls): `_Reader` is long; kind/status are strings checked at creation rather than their own types; the quote is the whole clause, so several observations can share one quote.
  - The consciousness phrase list needs clinician approval (A15).
- **How to verify:**
  ```bash
  .venv/bin/python -m pytest -p no:cacheprovider -q            # expect 123 passed
  .venv/bin/python -m resauce.extract data/dev-v1/cases/SYN-0047  # lorazepam + "awakens only to tactile stimulus", with quotes
  ```

---

## 2026-11-07: Milestone 2 Step 4 parts 4 and 5 (development cases batches 4 and 5)

- **Status:** 72 of 72 development cases and intended answers are written (`dataset_version` 1.0.0); no case was stopped. `tools.check_dev` reports 0 errors, 0 warnings (320 evidence references). `pytest` was not run (no code changed).
- **Decisions:** the answer files for these 35 cases follow the README format; where it left details open I chose them (provenance keys, `readings` for 7.5 and same-category cases, `documented_value` `{"grade": 0}` where formal Grade 0 assessments exist and `{"undetermined": ...}` for 7.4 cases, signed difference given for 7.4 onsets that have a documented onset). Check these against batches 1 to 3 for consistency.
- **Next steps:** the user's readability skim of all 72 cases (plan §9 check 10), then Step 5 (independent answers, comparison, disagreement log).
- **Open questions:** SC-47's grade depends on NEW-12 (marked in its answer); NEW-11 to NEW-18 are still undecided. All answers are "not clinician-verified".
- **How to verify:** `.venv/bin/python -m tools.check_dev`; `.venv/bin/python -m tools.show_case SYN-0040` (any case ID).

---

## 2026-11-07: Milestone 2 Step 4 part 3 (plan v0.3.1, development cases batch 3)

**Status:**
- `dataset-plan.md` is v0.3.1, approved.
- 37 of 72 development cases are written; `data/dev-v1/dataset.json` is `dataset_version` 0.3.0.
- `pytest` reports 97 passed; `tools.check_dev` reports 0 errors and 0 warnings (173 evidence references in 37 answer files).
- Not committed (the user runs `/finish-step`).

**Done:**
- **`dataset-plan.md` v0.3 → v0.3.1** (changelog entry added; the scenario table is unchanged):
  - §1 new order;
  - §7.4: when locked cases are written, unchanged protections, new change-log protection;
  - §7.5: trade-off disclosed;
  - §4.2: workload, batches of about 17, skimming;
  - §9 check 10: skimming;
  - status line.
- **Checked:** make_briefs reads exactly the same 72 scenario rows, and a fresh run would differ from the stored `briefs.json` only in the recorded plan fingerprint (sha256).
- **Stopped as instructed**, because `test_stored_briefs_match_a_fresh_run` failed on that fingerprint.
  - The user chose to edit that test. It now compares everything except the fingerprint. A new test, `test_plan_scenario_rows_match_the_stored_briefs`, checks that the plan's scenario rows equal those in the briefs.
  - `briefs.json` is unchanged; it still records the v0.3 fingerprint it was made from.
- **17 new cases:**

| Case | Scenario | Content |
|---|---|---|
| SYN-0061 | SC-14 | ICE 0 in an awake patient with global aphasia; record Grade 3; record onset corrected without new documentation. |
| SYN-0039 | SC-15 | Unarousable (voice, shaking, sternal rub) with ICE 0, two hours after eating breakfast and chatting; record Grade 3. |
| SYN-0052 | SC-16 | ICE 0/10 with no consciousness information that day; record Grade 4. |
| SYN-0002 | SC-18 | Partial ICE without a total plus new tremor on the record's onset date; first qualifying finding the next day. |
| SYN-0058 | SC-19 | Partial ICE (writing declined) with a total stated by the examiner; record matches; record re-entered unchanged; one off-unit "not assessable" day. |
| SYN-0069 | SC-20 | English-only ICE 4/10 with a documented language barrier; interpreter-assisted ICE 8 and 9; record Grade 1. |
| SYN-0024 | SC-21 | Record onset day has "awakens spontaneously", not drowsy, ICE 10/10; first finding the next day. |
| SYN-0055 | SC-22 | Daytime drowsiness with spontaneous waking (Grade 1) on the record's onset date; 3 documents. |
| SYN-0018 | SC-23 | "Opened eyes when name called loudly while RN tapped arm at same time": voice (Grade 2) or touch (Grade 3); record Grade 2. |
| SYN-0030 | SC-24 | ICE 8 at 23:30, written up at 00:50; record uses the event date; one off-ward "not assessable" day. |
| SYN-0019 | SC-25 | Untimed ICE 8 in a day-shift summary; record uses the documentation date. |
| SYN-0060 | SC-26 | "Overnight" ICE 7 in a Day +6 note; ICE 10 on both days of the range; record onset Day +5; record grade corrected without new documentation. |
| SYN-0066 | SC-28 | EEG recorded Day +7, signed Day +10: one 3-minute non-convulsive seizure, ended after levetiracetam, back to baseline; record Grade 2 never revised; out-of-window clinic visit. |
| SYN-0033 | SC-29 | Late entry (documented Day +11, between record versions) shows ICE 8 on Day +4; record onset revised. |
| SYN-0005 | SC-30 | Progress note v1 ICE 5 corrected in signed v2 to ICE 8; record Grade 2 matches the superseded v1. |
| SYN-0022 | SC-31 | Signed addendum adds a witnessed 40-second seizure with return to baseline; record Grade 2 not updated. |
| SYN-0041 | SC-33 | Record revised from Grade 2 to 3 with no supporting documentation; normal EEG. |

None of the 7.3 cases (SC-30, SC-33) has a documented "not assessable" period.

**Decisions & why:**
- **User decisions (2026-11-07):**
  1. **Locked cases are written after the pipeline (Milestone 3) and before any evaluation (Milestone 4).** The protections stay (fresh writer session in the private repository, no pipeline code or development text, frozen catalogue and scoring definitions, baseline specification before locked results). New protection: changes to `clinical-methods.md` or the plan are logged with whether pipeline work prompted them. The trade-off is disclosed in plan §7.5: the locked set is no longer fixed before pipeline work.
  2. **The remaining development cases are written in batches of about 17.**
  3. **The user skims every development case** (about 2 minutes each: plausible notes, nothing that gives the answer away). Locked sampling is unchanged.
  4. **Test change (this session):** compare stored briefs without the plan fingerprint, rather than editing or regenerating `briefs.json`. Why: the briefs are byte-identical apart from the fingerprint, and keeping the original file keeps the seeded record intact.
- **Lessons from review, applied in all 17 cases:**
  - every seizure states its duration and return to baseline;
  - depressed consciousness is shown at a time when the patient had been awake shortly before;
  - an excluded symptom (tremor) is followed by an ICE the next day.
- **Signed onset difference** is also given for a 7.4 onset when it is defined (SYN-0002: −1), following plan §8.1.
- **Checks during writing:**
  - a script compared the new cases with the 20 earlier cases (only new text printed; earlier files not opened). Shared prose and ICE item-score phrasing were reworded until no 8-word run was shared;
  - a script checked ICE item sums and found one wrong line, now fixed;
  - typos that had slipped into negations or deciding observations were removed.

**Next steps (new order):**
1. Step 4 parts 4 and 5: the remaining 35 development cases, about 17 each, in fresh conversations; `dataset_version` 0.4.0, then 1.0.0.
2. Step 5: independent two-stage answers, comparison and adjudication for the 72 development cases.
3. Milestone 3: the pipeline.
4. Step 6: locked cases (fresh session, private repository).
5. Milestone 4: evaluation.

**Open questions:**
- Start the change log for `clinical-methods.md` and the plan (v0.3.1 §7.4): where should it live (e.g. `docs/rule-change-log.md`), and should it start with the v0.3.1 change itself?
- `briefs.json` still records the v0.3 plan fingerprint. This is intended (the briefs were made from v0.3), but it could be noted in `reference/dev-v1/README.md` next time that file is edited.
- Known limitation (from part 2): the unassessed-period lists are long by design.
- Carried forward:
  - `data-format.md` §6 says "non-empty";
  - OOS flag reading;
  - the answer format is provisional;
  - NEW-11 to NEW-18;
  - clinician involvement;
  - baseline specification before locked results;
  - scoring details;
  - Node.js LTS version;
  - no licence.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 97 passed
.venv/bin/python -m tools.check_dev                 # expect: 37 case(s) ... Result: PASSED
git diff docs/dataset-plan.md                       # only the v0.3.1 edits; no scenario-table line changed
```

---

## 2026-11-07: Milestone 2 Step 4 part 2 (4 pilot fixes, batch 2 of development cases)

**Status:**
- 20 of 72 development cases are written; `data/dev-v1/dataset.json` is now `dataset_version` 0.2.0.
- No code, tests, settings, `briefs.json` or other docs were changed.
- `pytest` reports 96 passed; `tools.check_dev` reports 0 errors and 0 warnings (104 evidence references in 20 answer files).
- Not committed (the user runs `/finish-step`).

**Done: review fixes to 4 pilot cases.** Briefs and every intended category are unchanged; answers and offsets were updated.
1. **SYN-0021 (EEG report).**
   - Change: now 3 discrete non-convulsive seizures, each under 2 minutes, with "the background returned to its baseline" between them, still "resolved after IV levetiracetam"; "c/w encephalopathy" removed.
   - Why: "recurrent electrographic seizures" with no return to baseline could be read as Grade 4, and "encephalopathy" is a free descriptive word (plan §6, NEW-13).
2. **SYN-0017.**
   - Change: the "awakens only to tactile stimulus" check moved from 06:15 to 14:40, 25 minutes after the patient was seen awake and talking. The documents were renumbered by documentation time (physician note D04, CT D05, ICE check D06); all other facts kept.
   - Why: at 06:15 the finding could be read as normal sleep.
3. **SYN-0038.**
   - Change: the word-finding complaint moved to 21:40 on Day +4 (no ICE that day), and the ICE assessment moved to 06:10 on Day +5. Still 6 documents; categories still 7.7 / 7.7. The unassessed-day list changed (Day +5 now assessed, Day +6 not).
   - Why: a new neurological symptom followed by no ICE for 2 days was implausible.
4. **SYN-0027.**
   - Change: corrected "medicatons" in the sedating-medications negation, and also "dificulty" and "asymetry", which were typos inside negations too.
   - Why: part 1 rule A (no typos in negations). The other typos stay for the style.

**Done: 10 new cases (batch 2).**

| Case | Scenario | Content |
|---|---|---|
| SYN-0044 | SC-02 | Brief Grade 1 only (ICE 8 one day), recorded correctly; 3 documents. |
| SYN-0026 | SC-03 | A single ICE 6 is the only abnormal finding; record says Grade 1. Includes a physical therapy note (`other` / `other`, first use). |
| SYN-0037 | SC-04 | Record Grade 3; notes show ICE 5 and awakens to voice only; normal MRI. |
| SYN-0008 | SC-06 | Record onset 2 days after the first finding; out-of-window clinic visit on Day +35. |
| SYN-0013 | SC-08 | ICE 8 with arousal only to a light touch at a daytime check (patient seen awake earlier); record correctly Grade 3; out-of-window baseline on Day −5. |
| SYN-0003 | SC-09 | Domain chosen: a single self-limited generalized seizure (about 50 s, no benzodiazepine); record correctly Grade 3. |
| SYN-0065 | SC-10 | CT report states diffuse cerebral edema; record Grade 3 (matches the ICE 2 only). |
| SYN-0054 | SC-11 | Record Grade 3 counts a subdural hematoma (excluded, Table 6 footnote #; no surrounding edema); other findings Grade 2. |
| SYN-0056 | SC-12 | Record Grade 3 counts EEG slowing with FIRDA (no seizures); other findings Grade 2. Record onset corrected without new documentation; signed medication-list amendment. |
| SYN-0006 | SC-13 | Record Grade 4 rests on projectile vomiting with headache (text-only ICP sign, flagged); Table 6 findings Grade 2; papilledema, abducens palsy and posturing documented absent; no Cushing's triad. |

None of the four 7.3 cases (SC-04, SC-11, SC-12, SC-13) has a documented "not assessable" period (A25).

**Decisions & why:**
- **SC-09 domain = clinical seizure.** It is the domain least likely to need an imaging or EEG report, which the brief forbids as a normal-report extra. No sedative was given, so A30 is not triggered.
- **The arousal-only-to-touch findings (SYN-0013, and SYN-0017 after the fix) are at daytime checks**, with the patient documented awake shortly before. Why: so a reader cannot take them for sleep.
- **No pilot wording reused.** New cases were checked by script for any 8-word run shared with the 10 pilot cases (the plan §9 check 5 threshold). The first run found two borrowed prose phrases and several ICE item-score lines; all were reworded, and the final run found none. Only my own new text was printed; the pilot files were not opened.
- **Part A answers were edited directly**, not by re-running the part 1 helper script, which would have rewritten all pilot answers.

**Next steps:**
1. The user reads the 4 fixed and 10 new cases with `show_case`.
2. The assistant reviews the user's comments and fixes the cases and answers.
3. Part 3: the next 10 scenarios, in a fresh conversation, following `reference/dev-v1/briefs.json`; set `dataset_version` 0.3.0.

**Open questions:**
- **Known limitation (to disclose in the evaluation limitations):** each case is a selection of 3 to 12 documents, so most days in the 29-day window have no documented assessment. The unassessed-period list is therefore long by design. It reflects the selection of documents, not real clinical monitoring practice.
- Carried forward:
  - `data-format.md` §6 still says text must be "non-empty" (rule 26 says "visible text");
  - confirm that out-of-scope cases carry no other flags;
  - the answer format is provisional (Step 5);
  - NEW-11 to NEW-18;
  - clinician involvement;
  - baseline specification before Milestone 3;
  - scoring details;
  - Node.js LTS version;
  - no software licence yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 96 passed
.venv/bin/python -m tools.check_dev                 # expect: 20 case(s) ... Result: PASSED
git status                                          # data/dev-v1, reference/dev-v1/intended and docs/handoff.md changed
```

---

## 2026-11-07: Milestone 2 Step 4 part 1 (loader fix, authoring tools, briefs, 10 pilot cases)

**Status:** Step 4 part 1 of about 7 is done:
- `dataset-plan.md` v0.3 is marked approved.
- 10 of the 72 development cases exist in `data/dev-v1/` (`dataset_version` 0.1.0), each with an intended answer in `reference/dev-v1/intended/`.
- `pytest` reports 96 passed. `tools.check_dev` reports 0 errors and 0 warnings.
- Not committed (the user runs `/finish-step`).

**Done:**
- **Loader fix:** note text that is only whitespace (spaces, tabs, line breaks) is now rejected with a clear message. 3 new tests.
- **Docs** (only the edits the user allowed):
  - `data-format.md` v0.1.2: citation now clinical-methods v0.4; line 49 now says `data/` exists; rule 26 says text must contain visible text. All three are in the changelog line.
  - `dataset-plan.md`: status line "v0.3, approved by the user (2026-11-07)"; §11.2 item 1 marked approved. Done *before* generating the briefs, so the recorded fingerprint is the approved plan.
- **`tools/`** (new top-level package; the core never imports it):
  - `make_briefs.py` writes `ordering.json` and `briefs.json`;
  - `fill_offsets.py` fills in quote positions;
  - `check_dev.py` prints the check report;
  - `show_case.py` prints a case as readable text.
  - `pyproject.toml` gained `pythonpath = ["."]`, so pytest can import `tools`.
- **`reference/dev-v1/`:**
  - `ordering.json`: seed 20261107, `random.Random`, input order SC-01…SC-72, ID-to-scenario map;
  - `briefs.json`: 72 briefs, rules for all cases, totals, plan SHA-256;
  - `README.md`: the provisional answer format;
  - `intended/` for the 10 pilot cases.
- **Feature totals in `briefs.json`:**
  - styles: 12 each of 6;
  - documents: 3:4, 4:12, 5:13, 6:13, 7:12, 8:10, 9:3, 10:2, 11:2, 12:1;
  - infusion years: 2031–2036, 12 each; every month 6 times;
  - one case under 18 (SC-54, age 14);
  - out-of-window document 7; amended note 15 (20.8%); multi-version record 16; normal report 18 (9 EEG, 9 imaging); "not assessable" period 5 (2 required + 3 extra); unsigned version 6 (2 required + 4 extra); ungradeable symptom 5.
- **Pilot cases:** SYN-0001 (SC-54), SYN-0010 (SC-01), SYN-0017 (SC-07), SYN-0021 (SC-27), SYN-0027 (SC-17), SYN-0038 (SC-52), SYN-0043 (SC-59), SYN-0047 (SC-41), SYN-0067 (SC-32), SYN-0070 (SC-05). 64 documents, 52 evidence references.
- **New tests** (`tests/test_tools.py`, 18 tests):
  - fill_offsets: one, none and several matches; file unchanged on failure;
  - make_briefs: deterministic; stored files match a fresh run; plan has 72 scenarios (28/24/16/4); forced and forbidden features respected;
  - check_dev: passes on `data/dev-v1`; banned word is an error, "pH 7.4" only a warning;
  - show_case: time order, no answers;
  - `src/resauce/` never imports `tools` or reads `reference/`.

**Decisions & why:**
- **User decisions this step:**
  - 3 extra "not assessable" periods, with a non-sedation reason, after the documented onset, never on the day of the maximum grade, never on the record's onset date, and at least 2 days from any finding;
  - 4 harmless unsigned versions (plan §7.1 needs unsigned versions outside SC-32/68 too);
  - check_dev also checks brief conformance and answer/case pairing;
  - `dataset_version` 0.1.0, raised each part, 1.0.0 when all 72 are done;
  - "with typos" never touches numbers, scores, times, negations or deciding observation words;
  - SC-17: sedation for a non-neurological reason, no mental-status words except ICE and Table 6 findings;
  - category numbers in `data/` are warnings, not errors.
- **Rules derived from the plan for the briefs** (listed in `briefs.json` → `rules_for_all_cases`):
  - SC-54 age 13–17: avoids CAPD ages and the age-12 conflict in the source;
  - no out-of-window document in OOS cases or SC-60: in SC-60 an out-of-window Grade 0 ICE would be the only formal assessment;
  - no normal EEG/imaging report in SC-09–13, 27, 28: there an EEG, imaging, seizure or edema finding decides the answer;
  - extra amendments change nothing neurological and, in multi-version-record cases, come before record v1, so no accidental 7.6;
  - extra record versions use only the three §5.1 patterns, and only "same values re-entered" in "no ICANS" records;
  - an extra document is added only if 3 documents stay for the scenario;
  - unsigned extras are never placed in scenarios that already need an amendment (this was found and fixed during the step: it made the amendment total 14 instead of 15).
- **Pilot-case choices** (each recorded in that answer's `ambiguity_notes`):
  - SC-27: the EEG seizures resolve after IV levetiracetam (an antiseizure drug, not a sedative), so A30 is not triggered.
  - SC-41: lorazepam was given "PRN for sleep". The word "anxious" was avoided, because it could read as a free symptom word.
  - SC-52: the word-finding difficulty sits in a note with no ICE and no consciousness wording, on a day with no ICE assessment (NEW-13, NEW-14).
  - OOS answers carry only the out-of-scope flag (A29 "flag only"; plan §8.2).
- **Checks caught real mistakes:**
  - check_dev found that SYN-0017 had an amendment its final brief did not ask for (removed);
  - fill_offsets found a wrong date in one SYN-0017 answer quote (fixed);
  - two discharge-summary phrases that made the unassessed-day list unclear were reworded.
- Case JSON and answer JSON were produced by small throwaway helper scripts (outside the repo) from hand-written text. The files in `data/` and `reference/` are the source of truth.

**Next steps:**
1. User reads the 10 pilot cases with `show_case` (readability check, plan §9 check 10) and reports anything implausible.
2. The assistant reviews the user's comments and fixes the cases and answers.
3. Parts 2 to 7: about 10 cases each, in fresh conversations, following `reference/dev-v1/briefs.json` (and its `rules_for_all_cases`). Raise `dataset_version` each part.
4. Then Step 5 (independent two-stage answers, comparison, adjudication). The answer format may be revised there.

**Open questions:**
- `data-format.md` §6 table still says text must be "non-empty". Only rule 26 was changed, as allowed, so the two now differ slightly.
- Note type `other` and author role `other` are not used yet (plan §5.1 needs all 8 types and 7 roles across the set). Later parts should use them.
- The answer format is provisional (Step 5), including where non-case-level flags live (`other_flags` with a `field` key).
- Confirm the reading that out-of-scope cases carry no flags other than "out of scope (reason)".
- `briefs.json` was generated with Python 3.14.3. The test `test_stored_briefs_match_a_fresh_run` will show if another Python version gives a different shuffle.
- Carried forward: NEW-11 to NEW-18 (plan §10.2); clinician involvement; baseline specification before Milestone 3; scoring details; Node.js LTS version; no software licence chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 96 passed
.venv/bin/python -m tools.check_dev                 # expect: 0 error(s) ... Result: PASSED
.venv/bin/python -m tools.make_briefs               # rewrites briefs/ordering; git diff should show no change
.venv/bin/python -m tools.show_case SYN-0010        # read a case (no answers shown)
git status                                          # new: data/, reference/, tools/, tests/test_tools.py
```

---

## 2026-11-07: Milestone 2 Step 3 final review round (NEW-1 to NEW-10 decided provisionally)

**Status:** Documents only. `docs/clinical-methods.md` is now v0.4 and `docs/dataset-plan.md` v0.3. This was the last planning round before Step 4. The plan is **not approved yet**; the case numbers are proposed for final approval. `data-format.md`, code, tests and settings are unchanged. No cases, case text, reference answers or code were written. No `data/` or `reference/` folders exist. `pytest` reports 75 passed. Not committed (the user runs `/finish-step`).

**Done:**
- `clinical-methods.md` v0.4:
  - v0.3 → v0.4 changelog;
  - NEW-1 to NEW-10 written into the rules, tagged `[ASSUMPTION — EXPERT REVIEW]`;
  - existing assumptions amended where they cover the topic (A7, A15, A21–A26, A28–A30, A32; each marked "*Amended in v0.4*" in §9);
  - one new assumption, A34 (gradeable assessment);
  - new "Terms used in this section" in the §7 introduction;
  - new case-level flag "ungradeable neurological symptom";
  - cross-references checked: A1–A34 each defined once, no "not decided" text left.
- `dataset-plan.md` v0.3:
  - NEW-1 to NEW-10 moved to the resolved table (§10.1);
  - edge-rule scenarios SC-65 to SC-71 (1 + 1 cases each);
  - second "no ICANS" Neg scenario SC-72;
  - new flags placed as distractors in named scenarios (§2.1);
  - sizes recomputed by script;
  - §2.1, §5.1, §8.1, §8.2 updated;
  - user answers recorded (§11.1);
  - 8 new open points, NEW-11 to NEW-18, each with an avoid rule (§10.2).

**Decisions & why (made by the user; the clinical ones are provisional, pending clinician review):**
- NEW-1: ICANS recorded, no qualifying finding, plus a "not assessable" period → A25 wins, grade 7.4. Why: an unassessed period could hide the recorded grade.
- NEW-2: ungradeable symptoms do not block 7.7 in a "no ICANS" record; a new flag lists them. Why: keeps A21 as decided while making the symptoms visible. The clinician is asked whether they should block 7.7.
- NEW-3: 7.5 only when the readings lead to different categories. Why: consistent with A33; an answer that every reading agrees on is not hidden as a review flag.
- NEW-4: definitions of "gradeable assessment" (A34) and "documented 'not assessable' period" (A7). Why: several categories depend on them.
- NEW-5: the unassessed-period flag is case-level, on every in-scope case. Why: one consistent rule instead of special cases.
- NEW-6: the "record date matches" flag is added for any onset category. Why: the reviewer sees the likely reason for the record's date.
- NEW-7: 7.6 condition (c) tests the last change. Why: that change produced the current value.
- NEW-8: the window is applied per observation, by event date; a death makes the case out of scope whatever its date. Why: late entries about in-window events are real evidence.
- NEW-9: onset is the earliest possible date; A30 for ranges counts back from the end of the range. Why: the cautious choice; more results become ambiguous, none are hidden.
- NEW-10: baseline developmental delay is a fifth out-of-scope trigger. Why: §5 already excluded it.
- Open-question answers:
  - overlap threshold: 8 words;
  - out-of-window documents in about 10% of cases: agreed;
  - locked adjudicator: the user, and the 25% sample stays;
  - non-Claude writer: not now;
  - format Q1: the format stays, but every later version in the datasets gives a reason;
  - SC-52 concentration: solved by the new SC-72;
  - edge scenarios: 1 + 1 cases each, an exception because they test rules rather than categories.
- §10.3 consequences accepted; SC-52 stays not "plain".
- Proposed numbers (for final approval):
  - 72 development cases; 153 locked cases (146 scored, 7 OOS);
  - 40.4% Neg; 27.1% of Neg are "no ICANS";
  - 2 extra "no ICANS" Neg cases (1 each in SC-52 and SC-72). The minimum was 1; 2 lets the extras be spread across both scenarios.

**Next steps:**
- User approves `dataset-plan.md` v0.3.
- Then Step 4: development cases (72), plus the loader fix rejecting whitespace-only note text.

**Open questions:**
- `dataset-plan.md` §10.2, NEW-11 to NEW-18 (on the clinician agenda; cases avoid them). Notably:
  - NEW-12: §7.3's second clause could make any ungradeable symptom a 7.3. SC-47's grade depends on this reading and is marked so; it is the only case that depends on an open point.
  - NEW-13: whether "confused" is an ungradeable symptom when the note also has an ICE score. Until it is decided, free symptom words are kept out of most cases, which costs some realism.
- `dataset-plan.md` §11.2:
  - final approval of the numbers;
  - clinician involvement (A1–A34, scenario realism, the A21 question, NEW-11 to NEW-18);
  - a baseline specification before Milestone 3;
  - scoring details.
- §3.3 lists 6 rules that still have no scenario (e.g. NEW-1, NEW-7, NEW-10). The evaluation will not measure them.
- Carried forward:
  - `data-format.md` line 6 still cites clinical-methods v0.2;
  - Node.js LTS version;
  - no software licence chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 75 passed
git status          # expect: 3 changed docs (clinical-methods, dataset-plan, handoff), no new folders
git diff --stat     # only docs/ files
```
In `docs/clinical-methods.md`, check that §9 ends with A34 and that the changelog starts with "v0.3 → v0.4". In `docs/dataset-plan.md`, check that §2 lists SC-01 to SC-72, §10.1 lists NEW-1 to NEW-10 and §10.2 lists NEW-11 to NEW-18.

---

## 2026-11-07: Milestone 2 Step 3 review fixes, gaps decided provisionally

**Status:** Documents only. `docs/clinical-methods.md` is now v0.3, `docs/dataset-plan.md` v0.2 and `docs/data-format.md` v0.1.1. The dataset plan is still a draft and **not approved**. No cases, case text, reference answers or code were written. No `data/` or `reference/` folders exist. Code, tests and settings are unchanged. `pytest` reports 75 passed. Not committed (the user runs `/finish-step`).

**Done:**
- `clinical-methods.md` v0.3:
  - changelog at the top;
  - the user's 15 provisional gap decisions written as rules in the right sections, tagged `[ASSUMPTION — EXPERT REVIEW]`, and added to §9 as A19–A33;
  - new category 7.8; 7.5 renamed "Ambiguous evidence";
  - new §7.9 (record-level situations) and §7.10 (all extra flags);
  - shared principle stated in §7: documents can show ICANS did not occur only through formal Grade 0 assessments;
  - cross-references checked: A1–A33 each defined once; §7.1–§7.10 all exist.
- `dataset-plan.md` v0.2:
  - Gap type removed; former Gap scenarios re-categorised; SC-54 to 56 are type OOS;
  - new scenarios SC-59 to SC-64;
  - sizes recomputed by script;
  - record history rule (§5.1), case-ID seed (§7.2), two-stage independent answer (§8.2), scoring definitions (§8.3), readability sampling (§9);
  - §10 now holds the "resolved" table, 10 new open points (NEW-1 to NEW-10) and consequences to confirm.
- `data-format.md` v0.1.1: §12 Q3 and Q5 marked answered (pointing to A27 and A32). The format itself is unchanged.

**Decisions & why (made by the user; all provisional, pending clinician review):**
- **The 15 gap decisions, A19–A33:**
  - A19: a "no ICANS" record is Grade 0 with no onset (GAP-1).
  - A20: new category 7.8 Missing recorded value (GAP-2).
  - A21: a "no ICANS" record is 7.7 only with at least one formal Grade 0 assessment and no "not assessable" period, otherwise 7.4 (GAP-3).
  - A22: ICANS recorded with no qualifying finding (GAP-4).
  - A23: 7.5 widened with reasons (GAP-5).
  - A24: on the record's onset date, a Grade 0 assessment beats a symptom (GAP-6).
  - A25: a "not assessable" period gives 7.4, undocumented days give 7.3 plus a flag (GAP-7).
  - A26: relative-time table (GAP-8).
  - A27: unsigned content not used (GAP-9).
  - A28: three conditions for 7.6 (GAP-10).
  - A29: out of scope means flag only (GAP-11).
  - A30: 24-hour competing-cause window (GAP-12).
  - A31: lightly edited copies count as copied forward (GAP-13).
  - A32: observation window Day 0 to +28 (GAP-14).
  - A33: ICE 0 with no consciousness information gives Grade 3–4 (GAP-15).
  - Why: reference answers need a definite rule for every scenario. Each choice is listed with "why it matters" and "if wrong" so a clinician can review it.
- **Two-stage independent answers:** the checker derives the documentation-based values before seeing `record.json`. Why: seeing the record first could anchor it towards agreeing.
- **Readability sampling:** the user reads every development case, and for locked cases a random 25% (seeded) plus every case with a disagreement. Why: less work, and less exposure to locked content.
- **Scoring definitions fixed before results:**
  - discrepancy alert = 7.1/7.2/7.3/7.8;
  - review flag = 7.4/7.5;
  - false alert = a discrepancy alert on a 7.6/7.7 field;
  - review flags are counted separately;
  - OOS cases are scored only on flagging.
  - Why: definitions chosen after seeing results could be tuned to them.
- **Proposed in the plan (await approval):**
  - 64 development and 144 locked cases (138 scored, 6 OOS);
  - 40.6% Neg; 25% of Neg are "no ICANS" (12 extra SC-52 cases);
  - the 4-case rule kept only for SC-51 and SC-64;
  - out-of-window documents in about 10% of cases.

**Next steps:**
- User reviews and approves `dataset-plan.md` v0.2 (and the v0.3 rules).
- Then Step 4: development cases, plus the loader fix rejecting whitespace-only note text.

**Open questions:**
- `dataset-plan.md` §11 (12 questions), especially:
  - approval of the numbers;
  - NEW-1 to NEW-10 (§10.2), e.g. NEW-4 "gradeable assessment" is not defined precisely;
  - whether to add scenarios for rules not yet covered (§3.3);
  - SC-52 holding 14 of the 56 locked Neg cases.
- `dataset-plan.md` §10.3: confirm the consequences of A25 (the §7.4 example and SC-49 grade changed to 7.7), and that SC-52 is not labelled "plain".
- `data-format.md` line 6 still cites clinical-methods v0.2 (this step changed only §12 Q3/Q5 and the version line).
- Carried forward: who does the clinician review (now A1–A33); format Q1; Node.js LTS version; no software licence chosen yet.

**How to verify:**
```bash
cd ~/Projects/ReSauce
.venv/bin/python -m pytest -p no:cacheprovider -v   # expect: 75 passed
git status          # expect: 4 changed docs, no new folders
git diff --stat     # only docs/ files
```
In `docs/clinical-methods.md`, check that §9 ends with A33 and that §7 has subsections 7.1 to 7.10. In `docs/dataset-plan.md`, check that §2 lists SC-01 to SC-64 and that §10.2 lists NEW-1 to NEW-10.

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
