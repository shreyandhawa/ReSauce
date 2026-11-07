# ReSauce data format

- **Status:** v0.1.2 (2026-11-07). Milestone 2 Step 2. v0.1.1 only marks §12 Q3 and Q5 as answered; the format itself is unchanged (`schema_version` stays `"0.1"`).
- **Changelog v0.1.1 → v0.1.2:** clinical-methods citation updated from v0.2 to v0.4; §2 no longer says the `data/` folder does not exist; rule 26 now says text must contain visible text, not whitespace only, matching the loader.
- **Implemented by:** `src/resauce/models.py` and `src/resauce/loader.py`.
- **Tested by:** `tests/test_loader.py`, using the fixture in `tests/fixtures/format/valid_dataset/`.
- **Clinical definitions:** `docs/clinical-methods.md` v0.4. Section numbers below (§) refer to that file.

Tags follow `docs/clinical-methods.md`. `[OPERATIONAL]` marks a choice ReSauce makes. Format rules are engineering choices, so most rules here are `[OPERATIONAL]`.

---

## 1. Purpose

This file defines how synthetic input data is stored on disk. It covers:
- clinical documents (notes), with every version kept;
- the research record, with its change history;
- the facts about each case that the pipeline needs.

The loader reads these files and rejects anything that breaks the rules. It lists every problem it finds, with the file path, the field and a plain-English message.

All data is synthetic. Every file says so in two fields (§3). [OPERATIONAL]

### Design principle: no answer leakage

Input files contain only what a real chart export or research database would contain. [OPERATIONAL]
- No pre-tagged findings.
- No pre-extracted event times.
- No grades, labels or "correct answers" in document metadata.

Why: the pipeline must find findings, times and grades in the note text itself. If the input already contained them, a test would only show that the code can copy a field.

---

## 2. Folder layout

```
data/<dataset>/dataset.json
data/<dataset>/cases/<case_id>/case.json
data/<dataset>/cases/<case_id>/record.json
data/<dataset>/cases/<case_id>/documents/<document_id>.v<version>.json
```

- `<dataset>` is any folder name. The loader is given this folder's path.
- `cases/` must exist and contain at least one case folder. [OPERATIONAL]
- Each case folder's name is its `case_id`.
- `documents/` may be absent. An absent folder means the case has no documents.
- There is one file per document **version**.
- Files and folders whose names start with `.` (for example the macOS `.DS_Store` file) are ignored. Any other unexpected file or folder is an error. [OPERATIONAL]
- The top-level `data/` folder holds the synthetic datasets (development cases: `data/dev-v1/`, from Milestone 2 Step 4).

**Reference answers** (the expected results used to score the pipeline) will be stored separately, in a later step. They will never be stored inside a case folder. This keeps answers out of the pipeline's inputs. [OPERATIONAL]

---

## 3. Rules for every JSON file

- Files are read as UTF-8. [OPERATIONAL]
- The top level must be a JSON object (`{ ... }`).
- **Every field listed for a file is required.** A field that may be empty must be written as `null`. It must never be left out. [OPERATIONAL] Why: "left out by mistake" and "deliberately empty" stay distinguishable. This follows the rule that missing ≠ absent (§7.4).
- Fields not listed are rejected as unknown. This catches typos. [OPERATIONAL]
- The same key twice in one object is rejected. [OPERATIONAL]
- `NaN`, `Infinity` and `-Infinity` are rejected (they are not standard JSON). [OPERATIONAL]
- Whole-number fields accept only JSON whole numbers. `true`, `false`, `1.0` and `"1"` are rejected. [OPERATIONAL] (Python treats `true` as the number 1, so the loader checks for it explicitly.)

### Common fields

Every JSON file (dataset, case, record and document version) starts with these three fields.

| Field | Type | Allowed values | Serves |
|---|---|---|---|
| `schema_version` | string | exactly `"0.1"` | reproducibility (`CLAUDE.md`) |
| `synthetic` | boolean | exactly `true`. Not `"true"`, not `1` | synthetic-only rule (`CLAUDE.md`; §8) |
| `fictional_notice` | string | exactly `"FICTIONAL SYNTHETIC DATA. NOT A REAL PATIENT."` | synthetic-only rule (`CLAUDE.md`; §8) |

The loader does not store these fields in the loaded objects. They only gate loading.

---

## 4. `dataset.json`

| Field | Type | Required | Allowed values | Serves |
|---|---|---|---|---|
| `dataset_id` | string | yes | `SYN-DS-` then one or more of `A–Z`, `0–9`, `-` | reproducibility (data version recorded with every result) |
| `dataset_version` | string | yes | non-empty | reproducibility |
| `description` | string | yes | any string (may be empty) | documentation |
| `observation_window` | object | yes | see below | §6.5 |
| `observation_window.start_day` | whole number | yes | ≥ 0 | §6.5 |
| `observation_window.end_day` | whole number | yes | ≥ 0 and ≥ `start_day` | §6.5 |

- Days count from infusion. Day 0 is the infusion date.
- The window is inclusive at both ends.
- The window is declared per dataset (§6.5). This spec does not choose a clinical value for it.
- The loader does not check that documents fall inside the window. Deciding what to do with out-of-window data is pipeline logic.

---

## 5. `case.json`

| Field | Type | Required | Allowed values | Serves |
|---|---|---|---|---|
| `case_id` | string | yes | matches `SYN-` + exactly 4 digits (`^SYN-[0-9]{4}$`); must equal the case folder name | traceability |
| `age_at_infusion` | whole number | yes | 0–120 | §5 (A16) |
| `infusion_date` | date | yes | `YYYY-MM-DD` | Day 0 for §6, §7 |

- The loader does **not** enforce the ≥ 18 scope rule (§5, A16). An out-of-scope age may be a deliberate test case. The pipeline will flag it later. [OPERATIONAL]
- No names, dates of birth, sex, record numbers or any other identifiers. [OPERATIONAL; `CLAUDE.md`]

---

## 6. Clinical document version

One file per version, at `documents/<document_id>.v<version>.json`.

| Field | Type | Required | Allowed values | Serves |
|---|---|---|---|---|
| `case_id` | string | yes | must equal the case folder name | traceability |
| `document_id` | string | yes | `<case_id>-D` + 2 or more digits, e.g. `SYN-0001-D01` | evidence references (`CLAUDE.md`) |
| `version` | whole number | yes | ≥ 1 | §6.3 |
| `status` | string | yes | `signed`, `unsigned` | §6.3 (latest signed version is current) |
| `note_type` | string | yes | `physician_progress_note`, `nursing_note`, `neurology_consult`, `ice_assessment`, `eeg_report`, `imaging_report`, `discharge_summary`, `other` | context for later steps |
| `author_role` | string | yes | `attending_physician`, `resident_physician`, `advanced_practice_provider`, `nurse`, `neurologist`, `radiologist`, `other` | context; §3.4 (clinician statements) |
| `documented_at` | timestamp | yes | `YYYY-MM-DDTHH:MM` | §6.1 (documentation time) |
| `amendment_reason` | string or null | yes | non-empty string, or `null`. Must be `null` when `version` is 1 | §6.3 |
| `text` | string | yes | non-empty; must not contain `\r` | evidence (quoted text) |

Rules:
- The file name must equal `<document_id>.v<version>.json`. For example, `SYN-0001-D01.v2.json` must contain `"document_id": "SYN-0001-D01"` and `"version": 2`.
- Versions of one document must be numbered 1, 2, 3 … with no gaps and no duplicates. A document whose only file is version 2 is rejected (version 1 is missing).
- Earlier versions are kept. They are never overwritten (§6.3).
- `documented_at` must not decrease from one version to the next. Equal times are allowed. [OPERATIONAL]
- `author_role` holds roles only. Never names. [OPERATIONAL]
- `text` is stored and returned exactly as written. It is never stripped, trimmed or normalised. Line breaks must be `\n` only, so that character offsets are the same on every computer. [OPERATIONAL]
- Each loaded version has a derived `version_id`: `<document_id>.v<version>`, e.g. `SYN-0001-D01.v2`. It is computed, not stored.
- Loaded documents are sorted by the number after `-D` (so `D10` comes after `D9`), then by version. [OPERATIONAL]

---

## 7. `record.json`

The research record of one case: the values a research database holds, with an append-only change history.

| Field | Type | Required | Allowed values | Serves |
|---|---|---|---|---|
| `case_id` | string | yes | must equal the case folder name | traceability |
| `record_id` | string | yes | exactly `<case_id>-R` | traceability |
| `versions` | list | yes | non-empty list of version entries, oldest first | §7.6 |

Each entry in `versions`:

| Field | Type | Required | Allowed values | Serves |
|---|---|---|---|---|
| `version` | whole number | yes | entries are numbered 1, 2, 3 … in list order | §7.6 |
| `recorded_at` | timestamp | yes | `YYYY-MM-DDTHH:MM`; strictly later than the previous entry | §6.1 (record time) |
| `icans_reported` | boolean | yes | `true` or `false` | §1 |
| `onset_date` | date or null | yes | `YYYY-MM-DD` or `null` | §1(a), §7.1 |
| `max_grade` | whole number or null | yes | 1–5, or `null` | §1(b), §7.2, §7.3 |
| `change_reason` | string or null | yes | non-empty string, or `null`. Must be `null` for version 1 | §7.6 |

Rules:
- If `icans_reported` is `false`, `onset_date` and `max_grade` must both be `null`.
- If `icans_reported` is `true`, `onset_date` and `max_grade` may still be `null`. This represents a record with missing values. [OPERATIONAL]
- `max_grade` 5 can be stored only so the pipeline can flag it later. ReSauce does not assign Grade 5 (§8).
- The loaded record has a `current` property: the latest version.
- The loader does not compare record values with documents. That is pipeline logic.

---

## 8. Time conventions

| Kind | Format | Example | Used for |
|---|---|---|---|
| Date | `YYYY-MM-DD` | `2030-03-01` | `infusion_date`, `onset_date` |
| Timestamp | `YYYY-MM-DDTHH:MM` | `2030-03-04T14:00` | `documented_at`, `recorded_at` |

- All dates are fictional calendar dates. [OPERATIONAL]
- Timestamps are local time with **no timezone** and no seconds. `2030-03-04T14:00+01:00`, `2030-03-04T14:00Z` and `2030-03-04T14:00:00` are rejected. [OPERATIONAL]
- Formats are checked exactly. Other forms Python would accept, such as `20300301`, are rejected. Impossible dates such as `2030-02-30` are rejected. [OPERATIONAL]
- Only **documentation time** (`documented_at`) and **record time** (`recorded_at`) are metadata (§6.1). There is no "performed at" field.
- **Event times stay in the note text.** The pipeline must find them there later (§6.1).
- **Study days are computed, never stored.** `study_day(case, d)` returns calendar days from `infusion_date`. Day 0 is the infusion date. A timestamp counts by its calendar date. Dates before infusion give negative numbers. Plain date arithmetic only. [OPERATIONAL]

---

## 9. Evidence references

Later steps cite note text with an evidence reference. Every extracted observation must carry one (`CLAUDE.md`).

| Field | Type | Meaning |
|---|---|---|
| `document_id` | string | the document cited |
| `version` | whole number | the exact version cited |
| `start` | whole number | first character of the quote |
| `end` | whole number | one past the last character of the quote |
| `quote` | string | the exact quoted text |

### Offset conventions

- Offsets are 0-based, end-exclusive Python string indices into the version's `text`. [OPERATIONAL]
- They count Unicode code points (Python string characters), not bytes.
- So `text[start:end]` must equal `quote` exactly.
- Example: in `"Placeholder note"`, the word `note` has `start` 12 and `end` 16.

`check_evidence_ref(case, ref)` raises a `DataFormatError` if:
- `version`, `start` or `end` is not a whole number (booleans are rejected), or `quote` is not a string;
- the document version does not exist in the case;
- `start` < 0 or `end` > the length of the text;
- `start` ≥ `end`;
- `quote` is not equal to `text[start:end]`.

---

## 10. Validation rules (complete list)

The loader enforces every rule below. It collects **all** problems in a dataset (across all its cases) before raising one `DataFormatError`. `load_case` does the same for one case. Each problem names the file or folder path, the field and a plain-English message. [OPERATIONAL]

Files and folders:
1. `dataset.json`, `cases/`, and in each case `case.json` and `record.json` must exist.
2. `cases/` must contain at least one case folder, and only case folders.
3. `documents/` may be absent. If present, it must be a folder containing only files named `<something>.v<number>.json`.
4. Names starting with `.` are ignored everywhere the loader lists a folder.

Reading:
5. Files must be valid UTF-8.
6. Files must be valid JSON. The message gives the file path, line and column.
7. The top level must be a JSON object.
8. No duplicate keys in any object.
9. No `NaN` or `Infinity`.

Fields:
10. Every listed field must be present. Unknown fields are rejected. This applies to nested objects too (`observation_window`, each record version).
11. Common fields: `schema_version` = `"0.1"`; `synthetic` = `true` (boolean); `fictional_notice` = the exact notice.
12. Types and allowed values as in the tables in §4–§7.
13. Whole numbers must be real whole numbers; booleans are rejected.
14. Dates and timestamps must match the exact formats in §8 and be real.

Identity:
15. `case_id` in `case.json` matches `^SYN-[0-9]{4}$` and equals the folder name.
16. `case_id` in `record.json` and in every document equals the folder name.
17. `record_id` = `<case_id>-R`.
18. `document_id` matches `<case_id>-D` + 2 or more digits.
19. Document file name = `<document_id>.v<version>.json`.

Versions:
20. Document versions: 1..n, no gaps, no duplicates.
21. `documented_at` does not decrease across versions of one document.
22. `amendment_reason` is `null` for document version 1.
23. Record versions: numbered 1..n in list order; list not empty.
24. `recorded_at` strictly increases across record versions.
25. `change_reason` is `null` for record version 1.

Content:
26. `text` contains visible text (not empty, not whitespace only) and contains no `\r`.
27. If `icans_reported` is `false`, `onset_date` and `max_grade` are `null`.
28. `observation_window`: both days ≥ 0, `start_day` ≤ `end_day`.

If a document file cannot be read, or its `document_id` or `version` is invalid, rule 20 is not checked for that document. That file's own problem is still reported. Why: the loader cannot know which version the broken file was meant to be, so a "missing version" message would mislead. [OPERATIONAL]

---

## 11. What the format deliberately does NOT contain

| Not included | Why |
|---|---|
| Names, dates of birth, sex, record numbers, addresses, any identifier | Synthetic-only rule; no identifiers (`CLAUDE.md`). Not needed for the task. |
| Pre-tagged findings, ICE scores, consciousness levels, seizures etc. as fields | Answer leakage. The pipeline must find them in the text (§1 above). |
| Event times ("performed at", "observed at") | Event times live in the note text (§6.1). Storing them would leak the answer. |
| Grades or labels on documents | Answer leakage. |
| Stored study-day numbers | Computed from `infusion_date`, so they can never disagree with the dates. |
| Reference answers / expected results | Stored separately in a later step, never in a case folder. |
| Attribution to other causes as a field | Only clinician statements in the text count (§3.4, A9). |
| A "current version" flag on documents | Derived by the pipeline (§6.3: latest signed version). Storing it could disagree with the data. |
| Separate `.txt` files for note text | Text is inside the JSON (`text` field), so one file holds one version. |
| CRS fields, treatments, lab values | Out of scope (§8). Any such information appears only in note text. |

---

## 12. Open questions

1. Must every document version ≥ 2 give an `amendment_reason`, and every record version ≥ 2 a `change_reason`? Not enforced in v0.1.
2. May `note_type` or `author_role` change between versions of one document? Not enforced in v0.1.
3. **Answered (provisionally) by `clinical-methods.md` v0.3 §6.3 (A27).** Must the latest version of a document be `signed`? No. The format keeps allowing unsigned versions. The pipeline never uses unsigned content for onset or grade: a later unsigned version gets the flag "unsigned later version", and a document with no signed version is not used as evidence and gets the flag "unsigned document". The loader is unchanged.
4. Should the loader check that the dataset folder name equals `dataset_id`? Not enforced in v0.1.
5. **Answered (provisionally) by `clinical-methods.md` v0.3 §6.5 (A32).** Should documents or record dates outside the observation window be rejected, or flagged by the pipeline? Flagged, not rejected. Both datasets declare Day 0 to Day +28. Documents outside the window are not used for categories and get the flag "outside observation window". Record values are compared as they are. The loader is unchanged.
6. Should `onset_date` before `infusion_date` be rejected? Not enforced; it may be a deliberate test of the pipeline.
7. The file format for reference answers is not yet defined (later step).
8. Is a whole-number age enough, or will any test need finer age detail? Not needed for §5 as written.
