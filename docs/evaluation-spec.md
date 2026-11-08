# ReSauce evaluation specification

- **Status:** v0.1, draft (2026-11-08). Milestone 3 session 3. Written **before** any pipeline result exists, so the definitions cannot be chosen to suit the results.
- **Builds on:** `docs/clinical-methods.md` v0.4.1 (cited as §), `docs/dataset-plan.md` v0.3.1 with its v0.3.2 changelog entry (cited as "plan §"), `docs/data-format.md` v0.1.2.
- Results on synthetic data are not clinical validation.

## 1. Splits

| Split | Cases | Status |
|---|---|---|
| **dev** | SYN-0001, 0003, 0006, 0008, 0010, 0013, 0017, 0021, 0026, 0027, 0037, 0038, 0043, 0044, 0047, 0054, 0056, 0065, 0067, 0070 (20 cases) | Open: used to build and debug the pipeline. |
| **held-out (in-repo, not sealed)** | The other 52 cases of `data/dev-v1/` | Not opened during pipeline work. They have the same writer as the dev cases and sit in the same repository, so they are **not** a sealed test. This is disclosed with every result. |
| **locked** | Written later (plan Step 6, §7.4) | Sealed; not yet written. |

- The splits are always reported separately and never pooled.
- Every result records the dataset version, the git commit of the code and the commit of the reference answers.

## 2. Reference answers

- Source: `reference/dev-v1/intended/<case_id>.json` (answer format `0.1-provisional`).
- Label in every report: **"intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); not clinician-verified"**.
- When Step 5 produces adjudicated answers, those replace the intended answers. The change is logged and earlier results are kept.

## 3. Scoring (plan §8.3)

Each in-scope case has two **fields**, onset and maximum grade. Each field gets one category per method (§7.1–7.8).

**Field classes, by the reference category:**

| Class | Reference category |
|---|---|
| positive | 7.1, 7.2, 7.3, 7.8 |
| negative | 7.6, 7.7 |
| review | 7.4, 7.5 |

**Method outputs:** a **discrepancy alert** is 7.1, 7.2, 7.3 or 7.8. A **review flag** is 7.4 or 7.5.

| Term | Definition |
|---|---|
| Detection | An alert on a positive field. Any alert category counts. |
| Miss | A positive field with no alert. The report also states how many misses received a review flag instead. |
| False alert | An alert on a negative field (reference 7.6 or 7.7). |
| Alert on a review field | Reported separately. It counts as neither a detection nor a false alert. |
| "review: …" result | A field the method could not decide (e.g. "review: not implemented (§…)" for a rule not yet built, or an unresolved event date). It counts as **neither an alert nor a review flag**, and is reported separately with its count per field. |

These rules settle the three points that plan §8.3 left open: a detection does not need the exact category (exact agreement is reported separately); alerts on review fields are kept out of precision and recall; methods without review flags are compared on alerts only (below).

**Measures** are reported per field (onset, grade) and combined (both fields pooled). Every rate is shown with its raw counts and denominator.
- Precision = detections ÷ (detections + false alerts).
- Recall = detections ÷ positive fields.
- F1 = 2 × precision × recall ÷ (precision + recall).
- **Exact-category agreement:** the share of in-scope fields where the method's category equals the reference category, over all fields and over positive fields only.
- **Review flags:** counts broken down by reference category. Never counted as detections or false alerts.
- **Evidence-quote validity:** the share of the method's evidence references that pass `resauce.loader.check_evidence_ref` (the document version exists, and the quote equals the text at the offsets).
- No significance tests or confidence intervals: the splits are too small for them to mean much. The counts are reported as they are.

**Out-of-scope (OOS) cases** (§5, A29) are scored only on whether they are flagged out of scope, and with which reason. They never enter the discrepancy measurements of any method. If an in-scope case is wrongly flagged out of scope, it is counted and reported, and its positive fields count as misses.

**Methods that cannot produce review flags** (Baseline A) are scored on alerts only. Their review-flag rows read "n/a (method cannot produce review flags)". Baseline A produces no out-of-scope flags, so no OOS score is reported for it.

## 4. Baseline A: conventional validation

What a careful data manager would check without temporal reconciliation. It is built to be as strong as such checks can be, not weakened.
- **Input:** the same extraction output as ReSauce (`resauce.extract`), with the same ICE parsing and the same negation handling. Extraction quality is therefore not what the comparison measures. Only observations with status `present` are used.
- **Documents:** the latest version of each document, whether it is signed or not.
- **Time:** every observation is dated by its document's `documented_at` date, not by its event time.
- **No** attribution or competing causes, **no** observation window, and **no** record history (only the current record version is used).
- **Grading** (Table 6, §3.3), from these findings only:
  - ICE total: 7–9 → Grade 1, 3–6 → Grade 2, 0–2 → Grade 3;
  - a seizure → Grade 3; Grade 4 if it is documented as lasting more than 5 minutes, or as repetitive without return to baseline;
  - hemiparesis or paraparesis → Grade 4;
  - raised ICP or edema: focal edema → Grade 3; diffuse cerebral edema, papilledema, cranial nerve VI palsy, decerebrate or decorticate posturing, or Cushing's triad → Grade 4.
  - level of consciousness, only where the extractor has mapped the observation to a Table 6 category: awakens spontaneously → Grade 1, awakens to voice → Grade 2, awakens only to tactile stimulus → Grade 3, unarousable → Grade 4. This is what a careful data manager would do with the same wording.
  - Not graded: consciousness words with no approved mapping (e.g. "drowsy", "lethargic"; A15) and text-only ICP signs.
- **Onset:** the earliest `documented_at` date of a document with a Grade ≥1 finding. **Maximum grade:** the highest grade found.
- **Categories:**
  - the record reports no ICANS but a finding exists → grade 7.2, onset 7.1;
  - the record reports ICANS with an empty onset or grade → 7.8 for that field;
  - onset dates differ by 1 day or more (zero tolerance, as A4) → 7.1;
  - the documented grade is higher than the record → 7.2; lower → 7.3;
  - no Grade ≥1 finding at all → 7.7 for both fields ("missing evidence = no discrepancy");
  - otherwise → 7.7.
- **Output:** 7.1, 7.2, 7.3, 7.7 or 7.8 only.

## 5. Baseline B: LLM

Deferred until an API key is available. This is disclosed in every report until it is run. When it is specified, it is measured on the same cases with the same scoring.

## 6. Limitations (reported with every result)

- All data is synthetic. Results are not clinical validation.
- Cases and intended answers were written by Claude sessions. The answers are not independently verified and not clinician-verified.
- **The user does not read the development cases** (dataset plan, v0.3.2 changelog entry). They are checked only by `tools.check_dev` and by the reviewer's sampled reviews.
- The held-out split is not sealed (same writer, same repository).
- Rules that are not yet implemented return a review result, never a guess.
- The extractor's phrase lists were built from the 20 dev cases and `clinical-methods.md` only. Since session 4b, a word of 6 or more letters that is one letter away from a list word is read as an uncertain "spelling variant" and listed for review. Swapped letters (for example "seziure") are two changes, so they are still missed without a warning, as are shorter words.
