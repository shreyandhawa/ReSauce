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
