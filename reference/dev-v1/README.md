# Reference material for the development set (dev-v1)

**Provisional: may be revised in Step 5.** Milestone 2 Step 4 (2026-11-07).

This folder holds what the pipeline must **never** read: the case-ID ordering, the writing briefs and the intended answers for `data/dev-v1/`. The pipeline core (`src/resauce/`) must not read anything here (`docs/dataset-plan.md` §7.3). Only the tools in `tools/` and, later, evaluation code may.

Every answer here is **"not clinician-verified"**. Answers rest on `docs/clinical-methods.md` v0.4, including assumptions A19–A34, which are provisional user decisions awaiting clinician review. Results on these synthetic cases are not clinical validation.

## Files

| File | What it holds | Made by |
|---|---|---|
| `ordering.json` | The seed (20261107), the generator (`random.Random`), the input order SC-01 … SC-72, and which case ID belongs to which scenario (plan §7.2). | `tools/make_briefs.py` |
| `briefs.json` | One writing brief per case: scenario, expected categories (from the plan), and the dataset-wide features assigned with the same seeded generator. It also holds the rules every case follows, the feature totals and the fingerprint (SHA-256) of the plan it was made from. | `tools/make_briefs.py` |
| `intended/<case_id>.json` | The case author's intended answer for one case (plan §8.1, §8.2 step 1). | Written by hand; offsets filled by `tools/fill_offsets.py` |
| `independent/<case_id>.json` | A second, blind answer for each of the 72 cases (`answer_kind` `"independent"`). Made by Claude Opus in a separate folder (`~/Projects/ReSauce-blind`) that held only the cases, `clinical-methods.md`, `data-format.md` and the answer-format README, never the intended answers, plan, briefs, handoff, code or results. Same format as the intended answers, plus a `derivation` text (top-level in most files, inside each field in 12). Copied here unchanged. **Not clinician-verified.** | Written blind (Step 5a) |
| `comparison.md` | Independent against intended answers: agreement counts and a list of the differences. Nothing is adjudicated in it. | `tools/compare_answers.py` |

Re-create the first two with `.venv/bin/python -m tools.make_briefs`. The same seed and the same plan give identical files.

## Intended-answer format (provisional)

One JSON object per case. All keys are always present; empty values are `null` or `[]`.

| Key | Content |
|---|---|
| `answer_format` | `"0.1-provisional"` |
| `case_id`, `scenario_id` | e.g. `"SYN-0010"`, `"SC-01"` (must agree with `ordering.json`) |
| `scenario_label` | Short description of the scenario |
| `case_type`, `tags` | `Pos` / `Neg` / `Flag` / `OOS`; tags such as `"plain"`, `"no ICANS"` |
| `status` | Always `"not clinician-verified"` until expert review |
| `answer_kind` | `"intended"` (later steps add `"independent"` and `"adjudicated"`) |
| `provenance` | Versions of clinical-methods, data-format and dataset plan used; `dataset_id`, `dataset_version`; ordering seed; date written |
| `out_of_scope` | `null`, or `{reason, source, evidence}` for an out-of-scope case |
| `fields.onset`, `fields.max_grade` | One object per field (below) |
| `case_flags` | Case-level flags (§7.10), given once per case; `null` for an out-of-scope case |
| `other_flags` | Every other extra flag: `{flag, field, detail, evidence}`; `field` is `"onset"`, `"max_grade"` or `null` (case) |
| `ambiguity_notes` | What is uncertain and why, including every reading (A23) |
| `depends_on_open_points` | Open points from plan §10.2 that the answer depends on (normally `[]`) |
| `author_checks` | The author's §9 checklist: distractors, negated and positive findings, brief features used |

**Each field object** (`fields.onset` / `fields.max_grade`):

| Key | Content |
|---|---|
| `category` | `"7.1"` … `"7.8"`, or `"out of scope (<reason>)"` |
| `record_value` | The current record value (date, grade, or `null` for empty / no ICANS) |
| `documented_value` | Onset: `{"date", "study_day"}`, `{"range": [first, last], "study_days": [...]}` or `"none found"`. Grade: `{"grade"}`, `{"range": [low, high]}` or `{"undetermined": reason}` |
| `signed_difference_days` | Onset only: record date minus documented date, in days (negative = record earlier; for a range, measured to the nearest end). `null` where §7.9 says no difference is given, or for the grade field |
| `difference_note` | e.g. `"record has no onset"`, `"no documented onset"`, or `null` |
| `readings` | For 7.5, or when readings agree (A23): `[{reading, value, category}]` |
| `evidence` | Evidence references for every deciding observation (below) |
| `record_history` | For a multi-version record: `{"a", "b", "c", "explanation"}` (7.6 conditions, plan §5.1); otherwise `null` |

**Evidence reference:** `{"role", "document_id", "version", "quote", "start", "end"}`. The author writes `document_id`, `version` and `quote`; `tools/fill_offsets.py` finds the quote (it must occur exactly once in that version) and fills in `start` and `end` (0-based, end-exclusive, as in `docs/data-format.md` §9). `role` says why the quote matters.

**Case-level flags:**
- `unassessed_period`: `days_without_gradeable_assessment` (study days 0–28 with no gradeable assessment, A34) and `not_assessable_periods` (`[{days, evidence}]`, A7). Present in every in-scope case; lists may be empty.
- `ungradeable_neurological_symptom`: `[{day, evidence}]`, empty if none.

**Out-of-scope cases** get only the out-of-scope flag: no category for either field, no case-level flags (A29 "flag only"; plan §8.2: case-level flags apply only to in-scope cases).

## Conventions used in the answers

- Study days count from the infusion date (Day 0), as `resauce.loader.study_day` does.
- "Gradeable assessment" (A34): an ICE total documented for that day, or a qualifying finding. Normal EEG or imaging reports and narrative normal exams are not gradeable assessments.
- Signed difference for onset: record minus documents, e.g. record Day +4 and documented onset Day +6 gives −2 (`clinical-methods.md` §7.1 example).

## Value conventions (from Step 5a)

Adjudication (decided by the user, 2026-11-08): the intended and independent answers have no category disagreements (144 of 144; the 4 out-of-scope cases agree and differ only in the wording of the reason) and no real value disagreements. **The intended answers stay the reference, unedited.** The five "form only" rows in `comparison.md` §7 are differences of how a value is written, and the conventions below settle them for all future answers.

- **Grade with no qualifying finding:** `{"grade": 0}` if a formal Grade 0 assessment exists in the window, otherwise `{"undetermined": reason}`. **Onset with no qualifying finding:** `"none found"`.
- **Category 7.5 (ambiguous) field:** `documented_value` is `{"undetermined": reason}`. Each reading's value goes in `readings`.
- **Category 7.4 onset with a documented onset:** give `signed_difference_days` (clinical-methods §7.1); otherwise `null`.
- **Unchanged field in a multi-version record:** `record_history` is `{"a": false, "b": null, "c": null, "explanation": "field unchanged across record versions"}`.
- **Out-of-scope reasons:** one fixed string per reason in clinical-methods §5 (A29), the same strings the engine uses:

  | Reason (§5) | Fixed string |
  |---|---|
  | Age under 18 at infusion | `age under 18` |
  | A CAPD assessment in any note | `CAPD assessment` |
  | A record maximum grade of 5 | `record Grade 5` |
  | A documented death | `documented death` |
  | Documented baseline developmental delay | `developmental delay` |
