# ReSauce dataset plan

- **Status:** Draft v0.2 (2026-11-07), for user review. Milestone 2 Step 3. **Not approved.** All case numbers are a proposal.
- **Builds on:** `docs/clinical-methods.md` v0.3 (cited as §) and `docs/data-format.md` v0.1.1 (cited as "format §").
- **This file contains no cases, case text, reference answers or code.** It plans them.

## Changelog

**v0.1 → v0.2** (review fixes; the user's provisional gap decisions are in `clinical-methods.md` v0.3 as A19–A33):
- The "Gap" case type is removed. The 15 former Gap scenarios are re-categorised under the v0.3 rules. SC-54 to SC-56 become type **OOS** (out of scope, scored only on flagging).
- New category **7.8 Missing recorded value** (both fields). 7.5 is renamed **Ambiguous evidence**. The dataset must now cover 6 onset and 7 grade categories.
- New scenarios SC-59 to SC-64 (§2): event time vs documentation time with a mismatch; a "no ICANS" record with no formal assessment; a second scenario each for onset 7.5, onset 7.6 and grade 7.6; 7.8 for onset (SC-51 now covers 7.8 for grade).
- SC-52 is now the "no ICANS" Neg scenario. SC-49's grade changed from 7.4 to 7.7, and SC-04's constraint changed, as a direct result of A25 (§10.3).
- Sizes recomputed by script: 64 development and 144 locked cases (§4).
- §5.1: record history follows the 7.6 rule (A28). New construction rules for unsigned versions, "not assessable" periods and documents outside the observation window.
- §7.2: the random seed for case-ID order is recorded with the answers.
- §8.2: the independent answer is derived in two stages; record.json is withheld in Stage A. New §8.3: scoring definitions.
- §9: readability check by sampling for locked cases; two new checks.
- §10: the gap table is replaced by a "resolved" table (§10.1). §10.2 lists 10 new open points found while applying the decisions. §10.3 lists consequences to confirm.
- §11: answered questions removed; new ones added.

Tags follow `docs/clinical-methods.md`:

| Tag | Meaning |
|---|---|
| `[OPERATIONAL]` | A choice ReSauce makes for this plan. |
| `[ASSUMPTION — EXPERT REVIEW]` | Needs a clinician's input. |
| `NEW-n` | A point left open while applying the v0.3 decisions. Listed in §10.2. **Not decided here.** |

---

## 1. Purpose and status

**What the dataset is for.** [OPERATIONAL]
- To build the pipeline (development set).
- To measure the pipeline and the simpler verification approaches on the same cases (locked evaluation set).
- To check that every rule in `clinical-methods.md` is exercised at least once in each set.

**What it cannot show.**
- The data is synthetic. Results on it are **not clinical validation**.
- The cases are written to test rules. Their mix of discrepancies is chosen by us. Rates measured on it (for example, how often flags are correct) **do not carry over** to real research records.
- It cannot show whether the rules in `clinical-methods.md` are clinically right. Only expert review can (§9 of that file).
- Answers are derived from `clinical-methods.md`. Until a clinician reviews them, every answer is labelled **"not clinician-verified"**. A19–A33 are provisional user decisions, so answers that rest on them are doubly provisional.

**Agreed order for the rest of Milestone 2** (user decision):
1. Step 3: this dataset plan.
2. Step 4: development cases, plus a small loader fix (whitespace-only note text is currently accepted).
3. Step 5: reference answers for the development cases.
4. Step 6: locked evaluation cases.

All four come before Milestone 3 (the pipeline).

---

## 2. Scenario catalogue

### 2.1 How to read the catalogue

- One row per **scenario**: a situation the dataset must contain. One scenario becomes one or more **cases** (one synthetic patient each).
- **Onset** and **Grade** give the expected category for each field, from §7:

| Category | Onset | Grade |
|---|---|---|
| 7.1 Onset date mismatch | yes | no (onset only) |
| 7.2 Maximum grade mismatch | no (grade only) | yes |
| 7.3 Grade not supported | no (grade only) | yes |
| 7.4 Insufficient evidence | yes | yes |
| 7.5 Ambiguous evidence | yes | yes |
| 7.6 Legitimate revision | yes | yes |
| 7.7 No discrepancy | yes | yes |
| 7.8 Missing recorded value | yes | yes |

  So the dataset must cover **6 onset categories** and **7 grade categories**.
- Extra flags (§7.10) that do not replace the category are written after a "+" (for example "+ recurrence"). For 7.5 the reason is given in brackets.
- **Unassessed-period flag.** Every 7.3 grade field also carries it when the window has days with no gradeable assessment (A25). With 3 to 12 documents over 29 days, that is expected in almost every case, so it is not repeated in each row. "No ICANS" records always carry it (A21).
- **Type** of case [OPERATIONAL]:
  - **Pos**: at least one field is 7.1, 7.2, 7.3 or 7.8 (a discrepancy).
  - **Neg**: both fields are 7.6 or 7.7 (no discrepancy).
  - **Flag**: no discrepancy, but at least one field is 7.4 or 7.5 (for review).
  - **OOS**: out of scope (§5, A29). No category for either field. Scored only on whether the case is flagged "out of scope (reason)".
  - "plain" marks a case whose answer rests on **one plainly stated fact**. Simple methods should have a fair chance on these. This label describes the design, not a predicted result.
  - "no ICANS" marks a record with `icans_reported` = false.
- "Day +N" counts from infusion (Day 0). "G" means grade. Exact days in cases will vary; the days here only show the pattern. Every finding the answer relies on lies within the observation window, Day 0 to Day +28 (A32).

### 2.2 Plain cases

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-01 | Typical course recorded correctly: first finding Day +5 (ICE 9), worst Day +6 (ICE 4, awakens to voice); record onset Day +5, G2 | §6.2, §7.7, A2 | 7.7 | 7.7 | Neg, plain |
| SC-02 | Brief Grade 1 only, recorded correctly | §7.7 | 7.7 | 7.7 | Neg, plain |
| SC-03 | One clear ICE score (G2) is the only abnormal finding; record says G1 | §3.3, §7.2, A8 | 7.7 | 7.2 (+1) | Pos, plain |
| SC-04 | Record G3; notes support only G2 (ICE 5, awakens to voice); no Grade 3 finding; no documented "not assessable" period | §7.3, A8, A25 | 7.7 | 7.3 | Pos, plain |
| SC-05 | Record onset 2 days early; ICE 10 and alert on the recorded date | §7.1, A4 | 7.1 (−2) | 7.7 | Pos, plain |
| SC-06 | Record onset 2 days late | §7.1, A4 | 7.1 (+2) | 7.7 | Pos, plain |

### 2.3 Grade domains beyond ICE

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-07 | ICE alone gives the wrong grade: ICE 8 plus awakens only to touch, no sedation; record follows ICE (G1) | §3.5, §3.4, A15 | 7.7 | 7.2 (+2) | Pos |
| SC-08 | Same pattern; record correctly says G3 | §3.5, A15 | 7.7 | 7.7 | Neg |
| SC-09 | A non-ICE domain sets the grade (rapidly resolving seizure, focal motor weakness or diffuse edema; vary across cases); record correct | §3.3, §3.4 | 7.7 | 7.7 | Neg |
| SC-10 | Imaging report states diffuse cerebral edema (G4); record G3 | §3.3, §7.2 | 7.7 | 7.2 (+1) | Pos, plain |
| SC-11 | Record G3 counts an intracranial hemorrhage on imaging; other findings G2 | §4.2, Table 6 footnote #, A25 | 7.7 | 7.3 | Pos |
| SC-12 | Record G3 counts EEG slowing (not a seizure) as a seizure; other findings G2 | §3.3 notes, A25 | 7.7 | 7.3 | Pos |
| SC-13 | Record G4 rests on a raised-ICP sign found only in the source text, not Table 6; Table 6 findings G2 | §3.3, A12, A25 | 7.7 | 7.3 + text-only ICP sign | Pos |

### 2.4 ICE 0 and assessability

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-14 | ICE 0, awake with global aphasia (documented wakefulness); record G3 | §3.4, §4.1, A15 | 7.7 | 7.7 | Neg |
| SC-15 | ICE 0, unarousable, no competing cause documented; record G3 | §3.4, §4.1 | 7.7 | 7.2 (+1) | Pos |
| SC-16 | ICE 0, no consciousness information; record G4 | §4.1, §7.4, A33 | 7.7 | 7.4 | Flag |
| SC-17 | Sedated, documented "not assessable" on some days; record G4; all assessed days support G2 | §4.1, §7.3, §7.4, A7, A25 | 7.7 | 7.4 | Flag |
| SC-18 | Partial ICE with no stated total is the only assessment on the record's onset date; first qualifying finding a day later; grade correct | §4.1, §7.1, A6 | 7.4 | 7.7 | Flag |
| SC-19 | Partial ICE where the note states a total; record matches | §4.1, A6 | 7.7 | 7.7 | Neg |
| SC-20 | Low ICE with a documented language barrier decides the grade; one reading matches the record, the other does not (NEW-3) | §4.1, §7.5, A10, A23 | 7.7 | 7.5 (assessment barrier) | Flag |

### 2.5 Consciousness wording

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-21 | Recorded onset date has "awakens spontaneously" with no drowsiness and ICE 10 (Grade 0); first qualifying finding next day; grade correct | §3.3, §7.1, A3 | 7.1 (−1) | 7.7 | Pos |
| SC-22 | Drowsiness documented with spontaneous waking (G1) on the recorded onset date; record correct | §3.3, A3, A15 | 7.7 | 7.7 | Neg |
| SC-23 | A consciousness phrase that could fit two categories decides the grade; one reading matches the record, the other does not (NEW-3) | §7.5, A15, A23 | 7.7 | 7.5 (consciousness wording) | Flag |

### 2.6 Time

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-24 | Onset finding observed before midnight (explicit date and time in text), note documented after midnight; record uses the event date. Counterpart of SC-59 | §6.1 | 7.7 | 7.7 | Neg |
| SC-59 | **New.** Same documents as the SC-24 pattern; record uses the documentation date. Counterpart of SC-24: tests a hypothesised ReSauce advantage, so both versions must exist | §6.1, §7.1, A4 | 7.1 (+1) | 7.7 | Pos |
| SC-25 | Onset finding with no event time in the note; record uses the documentation date | §6.1 | 7.7 + time-imprecise | 7.7 | Neg |
| SC-26 | Onset finding described as "overnight" in a note documented on date D (range D−1 to D); record onset D−1; no other finding overlaps the range (NEW-9) | §6.1, §7.1, A26 | 7.7 + relative time | 7.7 | Neg |
| SC-27 | Late-signed EEG report: seizure on Day +7, report signed Day +10; record G2 on Day +8, revised to G3 on Day +10. The report's `documented_at` is after the Day +8 record version and no later than the revision | §6.1, §7.6, A2, A28 | 7.7 | 7.6 | Neg |
| SC-28 | Same EEG report; record never revised (stays G2) | §6.1, §7.2 | 7.7 | 7.2 (+1) | Pos |
| SC-29 | A late-entry note documents an earlier first finding; record onset revised after it. The late entry's `documented_at` is between the two record versions | §6.1, §7.6, A28 | 7.6 | 7.7 | Neg |

### 2.7 Note versions and record history

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-30 | Note v1 supports G2; amended v2 (signed, current) supports G1; record G2 | §6.3, §7.3, A25 | 7.7 | 7.3 + superseded-version match | Pos |
| SC-31 | Amendment adds a higher-grade finding; record not updated. Counterpart of SC-63 | §6.3, §7.2 | 7.7 | 7.2 + superseded-version match | Pos |
| SC-63 | **New.** Amendment adds a higher-grade finding; record grade revised after it. The amendment's `documented_at` is between the two record versions. Counterpart of SC-31 | §6.3, §7.6, A2, A28 | 7.7 | 7.6 | Neg |
| SC-62 | **New.** Onset revised after an amended note: a signed amendment adds an earlier, timed finding to an existing note; record onset revised after it. The amendment's `documented_at` is between the two record versions | §6.3, §7.6, A28 | 7.6 | 7.7 | Neg |
| SC-32 | Latest version of a note is unsigned and contains a higher-grade finding than the signed version; record matches the signed version | §6.3, A27 | 7.7 | 7.7 + unsigned later version | Neg |
| SC-33 | Record revised to a higher grade with no supporting documentation; current value wrong | §7.3, §7.6, A25, A28 | 7.7 | 7.3 (history shown) | Pos |
| SC-34 | Record onset corrected (clerical) with no new documentation; current value agrees | §7.6, §7.7, A28 | 7.7 + revision without new documentation | 7.7 | Neg |

### 2.8 Repeated and conflicting observations

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-35 | Same finding in a nursing note (evening) and restated in next morning's physician note; record uses the earlier date | §6.4 | 7.7 | 7.7 | Neg |
| SC-36 | Same documents; record uses the physician note's date | §6.4, §7.1, A4 | 7.1 (+1) | 7.7 | Pos |
| SC-37 | Text copied forward into notes after documented resolution, verbatim or with only dates, times or formatting changed (vary across cases); no real recurrence | §6.4, §6.5, A13, A31 | 7.7 (no recurrence flag) | 7.7 | Neg |
| SC-38 | Two assessments within the same hour disagree, and the disagreement decides the grade; one reading matches the record, the other does not (NEW-3) | §6.4, §7.5, A23 | 7.7 | 7.5 (conflicting assessments) | Flag |
| SC-61 | **New.** Two assessments within the same hour disagree on the earliest day (one meets a Grade 1 criterion, one is a formal Grade 0 assessment); record onset is the next day, from an unambiguous finding. Readings: onset that day (record +1) or the next day (match) | §6.4, §7.5, A23 | 7.5 (conflicting assessments) | 7.7 | Flag |

### 2.9 Distinct episodes

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-39 | Documented full resolution, then recurrence (both inside the window); record onset from the first episode, grade the highest of both | §6.5, A2, A5 | 7.7 + recurrence | 7.7 | Neg |
| SC-40 | Same pattern; record onset from the recurrence (the recurrence holds the highest grade) | §6.5, §7.1, A2, A4, A5 | 7.1 + recurrence | 7.7 | Pos |

### 2.10 Attribution

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-41 | The grade-deciding finding has a documented competing cause (e.g. a sedative) in the same note, or documented as given within the 24 hours before (vary across cases); no clinician statement | §3.4, §7.5, A9, A30 | 7.7 | 7.5 (attribution) | Flag |
| SC-42 | The earliest finding has a documented competing cause in the same note or within the 24 hours before; record onset is the next, unambiguous finding | §3.4, §7.5, A9, A30 | 7.5 (attribution) | 7.7 | Flag |
| SC-43 | A clinician attributes a finding to another cause; the record counts it | §3.4, §7.3, A9, A25 | 7.7 | 7.3 | Pos |
| SC-44 | Finding during CRS fever; a clinician explicitly attributes it to ICANS; record correct | §2, §3.4, A9 | 7.7 | 7.7 | Neg |

### 2.11 Onset from non-qualifying evidence and missing evidence

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-45 | Recorded onset date has only an excluded symptom (tremor or headache), no gradeable assessment that day | §4.2, §7.1, A11 | 7.4 (NEW-6) | 7.7 | Flag |
| SC-46 | Recorded onset date has an excluded symptom **and** a formal Grade 0 assessment (ICE 10, no other findings); first qualifying finding later | §7.1, A4, A11, A18, A24 | 7.1 (−N) + record date matches an excluded or sub-threshold symptom | 7.7 | Pos |
| SC-47 | Recorded onset date has only a sub-threshold symptom (e.g. word-finding difficulty, no ICE) | §7.1, A18 | 7.4 (NEW-6) | 7.7 | Flag |
| SC-48 | Recorded onset date has only a narrative normal neuro note (no ICE) | §7.1, A17 | 7.4 | 7.7 | Flag |
| SC-49 | No notes on the days around the recorded onset (record onset Day +3, G1); first qualifying finding Day +6 at G1; nothing higher documented (the §7.4 example as revised in v0.3) | §7.1, §7.4 | 7.4 | 7.7 | Flag |

### 2.12 Record-level situations (§7.8, §7.9)

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-50 | Record says no ICANS; notes document qualifying ICANS (no competing cause) | §7.9(a), A8, A19 | 7.1 ("record has no onset") | 7.2 | Pos, no ICANS |
| SC-51 | Record says ICANS; maximum grade left empty; onset correct | §7.8, A20 | 7.7 | 7.8 | Pos |
| SC-64 | **New.** Record says ICANS; onset left empty; grade correct | §7.8, A20 | 7.8 | 7.7 | Pos |
| SC-52 | Record says no ICANS; formal Grade 0 assessments in the window; no qualifying finding; no "not assessable" period; no ungradeable neurological symptoms (NEW-2); distractors such as CRS fever, tremor or headache | §7.9(b), A21 | 7.7 + unassessed period | 7.7 + unassessed period | Neg, no ICANS |
| SC-60 | **New.** Record says no ICANS; no formal assessment at all (narrative notes only); no qualifying finding | §7.9(b), A17, A21 | 7.4 + unassessed period | 7.4 + unassessed period | Flag, no ICANS |
| SC-53 | Record says ICANS; notes contain only ungradeable symptoms (e.g. "confused", no ICE or consciousness level), including on the record's onset date, with no gradeable assessment that day; no "not assessable" period (NEW-1) | §7.3, §7.9(c), A18, A22, A25 | 7.4 (NEW-6) | 7.3 | Pos |

### 2.13 Out of scope (the pipeline must flag these)

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-54 | Age under 18 at infusion | §5, A16, A29 | — | — | OOS (age under 18) |
| SC-55 | Adult case with a CAPD assessment in a note | §5, A29 | — | — | OOS (CAPD assessment) |
| SC-56 | Record maximum grade 5 (no documented death) | §8, A29 | — | — | OOS (record Grade 5) |

### 2.14 Note formats

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-57 | Key findings only in templated or flowsheet-style notes with heavy abbreviations; record correct | §6.1 | 7.7 | 7.7 | Neg |
| SC-58 | The only higher-grade finding is stated once, clearly, inside a long discharge summary; record lower | §7.2 | 7.7 | 7.2 | Pos, plain |

### 2.15 Totals

| Type | Scenarios |
|---|---|
| Pos | 25 (6 of them plain) |
| Neg | 22 (2 of them plain) |
| Flag | 14 |
| OOS | 3 |
| **Total** | **64** |

The script that produced these counts also checks that each scenario's type matches the definitions in §2.1.

Realism of each scenario (whether such documentation occurs in practice) has not been checked by a clinician. [ASSUMPTION — EXPERT REVIEW]

---

## 3. Coverage matrix

Proposed case counts per scenario [OPERATIONAL]:
- **Development:** 1 case per scenario (64).
- **Locked:** 2 cases per scenario (including the former Gap scenarios and the OOS scenarios), except:
  - 4 cases each for SC-51 and SC-64. They are the only scenarios for grade 7.8 and onset 7.8. With 2 cases each, those categories would have only 2 locked cases. Every other category has at least 4, so the 4-case rule is kept only here.
  - 14 cases for SC-52: 2 plus 12 extra "no ICANS" no-discrepancy cases (§4.1 shows why 12).

All counts below were computed with a throwaway script from the catalogue above.

### 3.1 Categories

| Field | Category | Scenarios | Dev cases | Locked cases |
|---|---|---|---|---|
| Onset | 7.1 | SC-05, 06, 21, 36, 40, 46, 50, 59 | 8 | 16 |
| Onset | 7.4 | SC-18, 45, 47, 48, 49, 53, 60 | 7 | 14 |
| Onset | 7.5 | SC-42, 61 | 2 | 4 |
| Onset | 7.6 | SC-29, 62 | 2 | 4 |
| Onset | 7.7 | 41 scenarios (all others in scope) | 41 | 96 |
| Onset | 7.8 | SC-64 | 1 | 4 |
| Grade | 7.2 | SC-03, 07, 10, 15, 28, 31, 50, 58 | 8 | 16 |
| Grade | 7.3 | SC-04, 11, 12, 13, 30, 33, 43, 53 | 8 | 16 |
| Grade | 7.4 | SC-16, 17, 60 | 3 | 6 |
| Grade | 7.5 | SC-20, 23, 38, 41 | 4 | 8 |
| Grade | 7.6 | SC-27, 63 | 2 | 4 |
| Grade | 7.7 | 35 scenarios | 35 | 84 |
| Grade | 7.8 | SC-51 | 1 | 4 |
| Both | No category (OOS) | SC-54, 55, 56 | 3 | 6 |

Every category appears in both sets, with at least 4 locked cases. Onset 7.8 and grade 7.8 each rest on one scenario. Their definition is simple (an empty field), so this matters less than it did for 7.5 and 7.6, which now have 2 to 4 scenarios each.

### 3.2 Assumptions

| Assumption | Scenarios | Dev | Locked |
|---|---|---|---|
| A1 (manuscript = published) | Not testable with data | – | – |
| A2 (max grade over time) | SC-01, 27, 39, 40, 63 | 5 | 10 |
| A3 (spontaneous waking needs drowsiness) | SC-21, 22 | 2 | 4 |
| A4 (0-day onset tolerance) | SC-05, 06, 21, 36, 40, 46, 59 | 7 | 14 |
| A5 (one episode) | SC-39, 40 | 2 | 4 |
| A6 (partial ICE) | SC-18, 19 | 2 | 4 |
| A7 (not assessable) | SC-17 | 1 | 2 |
| A8 (under = mismatch, over = unsupported) | All 7.2 and 7.3 scenarios | 16 | 32 |
| A9 (attribution only from clinicians) | SC-41, 42, 43, 44 | 4 | 8 |
| A10 (barriers) | SC-20 | 1 | 2 |
| A11 (excluded symptoms) | SC-45, 46 | 2 | 4 |
| A12 (text-only ICP signs) | SC-13 | 1 | 2 |
| A13 (copied-forward text) | SC-37 | 1 | 2 |
| A14 (Lee 2019 is current) | Not testable with data | – | – |
| A15 (consciousness phrases) | SC-07, 08, 14, 15, 22, 23 | 6 | 12 |
| A16 (age ≥ 18) | SC-54 | 1 | 2 |
| A17 (narrative normal note) | SC-48, 60 | 2 | 4 |
| A18 (symptom-based onset) | SC-46, 47, 53 | 3 | 6 |
| A19 ("no ICANS" record vs documented ICANS) | SC-50 | 1 | 2 |
| A20 (7.8 missing recorded value) | SC-51, 64 | 2 | 8 |
| A21 ("no ICANS" record, no qualifying finding) | SC-52, 60 | 2 | 16 |
| A22 (ICANS recorded, no qualifying finding) | SC-53 | 1 | 2 |
| A23 (7.5 ambiguous evidence, non-attribution reasons) | SC-20, 23, 38, 61 | 4 | 8 |
| A24 (Grade 0 assessment beats symptom on record date) | SC-46 | 1 | 2 |
| A25 (unassessed periods and 7.3 / 7.4) | All 7.3 scenarios, SC-17 | 9 | 18 |
| A26 (relative time phrases) | SC-26 | 1 | 2 |
| A27 (unsigned content) | SC-32 | 1 | 2 |
| A28 (when a revision is 7.6) | SC-27, 29, 33, 34, 62, 63 (and every multi-version record, §5.1) | 6 | 12 |
| A29 (out of scope) | SC-54, 55, 56 | 3 | 6 |
| A30 (24-hour competing-cause window) | SC-41, 42 | 2 | 4 |
| A31 (lightly edited copies) | SC-37 | 1 | 2 |
| A32 (window Day 0 to +28) | Every case; out-of-window documents per §5.1 | 64 | 144 |
| A33 (ICE 0, no consciousness information) | SC-16 | 1 | 2 |

### 3.3 Other rules

| Rule | Scenarios |
|---|---|
| §3.5 ICE alone is not the grade | SC-07, 08 |
| §4.1 ICE 0 and assessability | SC-14, 15, 16, 17 |
| §4.2 excluded findings | SC-11, 13, 45, 46 |
| §5 / §8 out of scope | SC-54, 55, 56 |
| §6.1 event vs documentation time | SC-24, 25, 26, 27, 28, 29, 59 |
| §6.3 note versions | SC-30, 31, 32, 62, 63 |
| §6.4 repeated and conflicting | SC-35, 36, 37, 38, 61 |
| §6.5 episodes | SC-39, 40 |
| §7.5 reasons | attribution SC-41, 42; conflicting assessments SC-38, 61; assessment barrier SC-20; consciousness wording SC-23 |
| §7.6 revisions | SC-27, 29, 62, 63 (7.6); SC-33 (revision, still wrong); SC-34 (revision without new documentation) |
| §7.8 missing recorded value | SC-51 (grade), SC-64 (onset) |
| §7.9 record-level situations | (a) SC-50; (b) SC-52, 60; (c) SC-53 |

**Rules with no scenario yet** (see §11 question 9):
- §7.9(c) onset "no documented onset" (a formal Grade 0 assessment on the record's onset date, no qualifying finding anywhere; A22). SC-53 reaches 7.4 instead.
- A33 with a record of Grade 2 or lower (→ 7.2). SC-16 covers only the 7.4 path.
- §7.9(b) reaching 7.4 because of a documented "not assessable" period. SC-60 reaches 7.4 because there is no formal assessment.
- The "unsigned document" flag (a document with no signed version; A27).
- A documented death as an out-of-scope trigger (A29). SC-56 uses a Grade 5 record.
- 7.5 inside a "no ICANS" record (A19, "normal rules still apply").

---

## 4. Size and balance (proposal for user approval)

### 4.1 Proposed numbers [OPERATIONAL]

| Set | Cases | In discrepancy measurements | OOS (scored only on flagging) |
|---|---|---|---|
| Development | 64 | 61 | 3 |
| Locked | 144 | 138 | 6 |

**How the locked number was reached** (by script):
1. 2 cases per scenario: 64 × 2 = 128 cases (122 scored + 6 OOS).
2. 4-case rule only where a category would otherwise have fewer than 4 locked cases: SC-51 and SC-64 get 2 extra each → 132 cases (126 scored + 6 OOS).
3. Extra "no ICANS" Neg cases until both balance rules hold (table below): 12 → 144 cases (138 scored + 6 OOS).

| Step | Scored cases | Neg | Neg share | "No ICANS" Neg | Share of Neg |
|---|---|---|---|---|---|
| 2 per scenario, plus the 4-case rule for SC-51 and SC-64 | 126 | 44 | 34.9% | 2 (SC-52) | 4.5% |
| Add *x* extra "no ICANS" Neg cases (SC-52) | 126 + *x* | 44 + *x* | | 2 + *x* | |
| Rule 1: Neg share ≥ 40% | (44 + *x*) / (126 + *x*) ≥ 0.40 → 0.6*x* ≥ 6.4 → *x* ≥ 10.7 → **11** | | | | |
| Rule 2: "no ICANS" ≥ ¼ of Neg | (2 + *x*) / (44 + *x*) ≥ 0.25 → 0.75*x* ≥ 9 → *x* ≥ **12** | | | | |
| **Result, *x* = 12** | **138** | **56** | **40.6%** | **14** | **25.0%** |

Locked total: 138 scored + 6 OOS = **144**. This is below 150, so no cut is proposed.

Locked scored cases by type: 56 Neg (40.6%), 54 Pos, 28 Flag. Counting the 6 OOS cases in the denominator, the Neg share is 56 / 144 = 38.9%.

"No ICANS" records in the locked set: 14 Neg (SC-52), 2 Pos (SC-50), 2 Flag (SC-60), 18 in all.

Counted per field (2 fields per scored case, 276 fields): 188 expected 7.6/7.7, 56 expected 7.1/7.2/7.3/7.8, 32 expected 7.4/7.5.

Development set (1 per scenario): 22 Neg of 61 scored (36.1%). The balance rules are for the locked set only; the development set is for building, not measuring.

### 4.2 Why these numbers

- **Development, 1 per scenario:** the minimum that lets the pipeline be built against every rule. It is for building, not measuring.
- **Locked, 2 per scenario:** each scenario is seen in new wording, so a method cannot pass by matching one phrasing. Former Gap scenarios and OOS scenarios are treated the same way.
- **4-case rule only for SC-51 and SC-64:** every other category already has at least 4 locked cases.
- **At least 40% Neg:** enough no-discrepancy fields to measure false alerts (§4.3). The real-world share of discrepancies is unknown, and this share does not claim to match it.
- **At least a quarter of Neg cases are "no ICANS" records:** the user's rationale is that most real CAR-T patients do not develop ICANS, so a record of "no ICANS" is a common real situation. This rate is not sourced in this project's documents.
- **Concentration risk:** 14 of the 56 locked Neg cases come from one scenario (SC-52). Their wording, distractors, note styles and number of formal assessments must vary. A second "no ICANS" Neg scenario would spread this (§11 question 12).
- **Workload:** 208 cases in total (64 + 144), written in batches of about 10. The user reads all 64 development cases and about 36 locked cases (25% of 144) plus every locked case with a disagreement (§9 check 10).
- **Smaller alternative:** 1 locked case per scenario (64 cases, 61 scored, 80 no-discrepancy fields). The false-alert bound would then be 4.6% instead of 2.0% (§4.3), and the 40% and quarter rules would not be met without extra cases.

### 4.3 What this size can and cannot show

**Method.** 95% Wilson score interval for a proportion *x/n*, with *z* = 1.96 (*p* = *x/n*):

centre = (*p* + *z*²/2*n*) / (1 + *z*²/*n*); half-width = *z* · √(*p*(1−*p*)/*n* + *z*²/4*n*²) / (1 + *z*²/*n*).

**Worked example** (*x* = 10, *n* = 100): *p* = 0.10; *z*²/*n* = 0.0384; centre = 0.1192 / 1.0384 = 0.1148; half-width = 1.96 × 0.0316 / 1.0384 = 0.0596; interval 5.5% to 17.4%.

When *x* = 0, the upper bound is *z*²/(*n* + *z*²). For *n* = 188: 3.8416 / 191.84 = 2.0%. For *n* = 80: 3.8416 / 83.84 = 4.6%.

The *n* values use the scoring definitions in §8.3: false alerts are counted on fields whose reference answer is 7.6 or 7.7 (188 locked fields); detection on fields whose reference answer is 7.1, 7.2, 7.3 or 7.8 (56 locked fields).

| What is measured | n | If observed | 95% Wilson interval |
|---|---|---|---|
| False alerts on no-discrepancy fields | 188 | 0 | 0.0% to 2.0% |
| | 188 | 19 (10%) | 6.6% to 15.2% |
| Discrepancy fields correctly alerted | 56 | 28 (50%) | 37.3% to 62.7% |
| | 56 | 56 (100%) | 93.6% to 100% |
| One category (e.g. grade 7.2) | 16 | 8 (50%) | 28.0% to 72.0% |
| | 16 | 16 (100%) | 80.6% to 100% |
| A rare category (e.g. onset 7.5) | 4 | 2 (50%) | 15.0% to 85.0% |

All values were computed by script; none is quoted from elsewhere.

**Can show:**
- a rough overall false-alert rate on these synthetic cases;
- a rough overall detection rate;
- which scenarios each method gets wrong (case by case, which matters most for a proof of concept).

**Cannot show:**
- reliable per-category rates: with 4 to 16 cases per category (other than 7.7), intervals are about 30 to 70 percentage points wide;
- small differences between ReSauce and the simpler methods. Both run on the same cases, so a paired comparison is possible, but which test to use and how large a difference it can detect is not calculated here;
- anything about real records.

**The intervals above are too narrow.** They assume every field is independent. In fact the two fields of one case are related, cases from the same scenario are related (14 locked cases share the SC-52 design), and one writer wrote them all. The true uncertainty is larger, by an amount not computed here.

---

## 5. Case construction rules [OPERATIONAL]

### 5.1 One case

| Element | Rule |
|---|---|
| Documents per case | 3 to 12 (most 4 to 8). Count chosen independently of the scenario. |
| Note types | All 8 `note_type` values used across the set. At least 2 types per case. EEG and imaging reports also appear with normal results in unrelated cases, so their presence does not hint at a scenario. |
| Author roles | All 7 roles used. Role fits the note type (e.g. radiologist writes imaging reports). |
| Documentation times | Realistic shifts, including night notes and non-round times. Event times in the text are at or before documentation time, unless the scenario needs otherwise. |
| Dates | Fictional infusion dates spread over several years and months. Days from infusion vary between cases of the same scenario. Every finding the answer relies on lies within Day 0 to Day +28 (A32). |
| Observation window | `dataset.json` declares `start_day` 0 and `end_day` 28 in both sets (A32). |
| Documents outside the window | Proposal: about 10% of cases include one document outside the window (e.g. a pre-infusion baseline note, or a follow-up after Day +28). It gets the "outside observation window" flag and is left out when the answer is worked out (A32). Both its documentation date and every event date it mentions lie outside the window (NEW-8). |
| Age | 18 to 85, varied. Under 18 only in SC-54. |
| Amendments | About 15–25% of all cases have an amended note, including cases where the amendment changes nothing relevant (e.g. a corrected vital sign). All amendments are signed unless the scenario is SC-32. |
| Unsigned versions | Only where the scenario needs them (SC-32), or as distractors whose omission cannot change the answer. Worked out under A27. |
| "Not assessable" periods | Only where the scenario needs them (SC-17), or in cases where they cannot change the answer. Never in a 7.3 case (A25 would make it 7.4), a "no ICANS" Neg case (A21 would make it 7.4) or SC-53 (NEW-1). |
| Record history | See below. |
| Record values | Must pass format §7 rules. |

**Record history.** Multi-version records appear in Pos, Neg and Flag cases, not only in revision scenarios. Every record history is part of the intended answer and is worked out under the 7.6 rule (§7.6, A28). A field is 7.6 only if all three hold:
- (a) its value changed between record versions;
- (b) its current value meets the 7.7 conditions;
- (c) a document version supporting the new value has `documented_at` after the previous record version's `recorded_at`, and no later than the `recorded_at` of the version that made the change.

In a **non-revision scenario**, a multi-version record must not create a 7.6 by accident. Its intended category must still be worked out under that rule. Allowed patterns:
- a new version that re-enters the same values (no field's value changes), e.g. "Data review";
- a change whose current value agrees with the documents, with no supporting document version in the interval → 7.7 plus "revision without new documentation" (this adds a flag; the category is unchanged);
- in a Pos case, a change after which the current value still disagrees → the usual discrepancy category, with the history shown.

Each field changes value at most once per record until NEW-7 is decided. For every multi-version record, the case author writes down which of (a), (b) and (c) hold for each field.

### 5.2 Distractors

Each case contains at least 2 realistic distractors, for example:
- CRS fever, low blood pressure and their treatment (§2);
- excluded symptoms: tremor, headache, myoclonus, hallucinations (§4.2);
- irrelevant neuro history (e.g. remote migraine, neuropathy from earlier chemotherapy);
- normal tests (normal EEG, unremarkable imaging);
- routine nursing content.

Each case contains both **negated** findings (e.g. "no seizure activity", "no focal deficits") and **positive** findings.

A distractor must not change the answer by accident. For example:
- a sedative or other competing cause in the same note as a finding, or within the 24 hours before it, creates ambiguous evidence (§7.5, A30);
- an excluded or sub-threshold symptom on the record's onset date changes the onset result (§7.1, A24);
- a documented "not assessable" period turns a 7.3 grade into 7.4 (A25), and a "no ICANS" 7.7 into 7.4 (A21);
- an unsigned version or a document outside the window is left out (A27, A32), which can change the answer;
- an ungradeable neurological symptom (e.g. "confused") in a "no ICANS" case touches NEW-2;
- a relative time phrase near the onset touches NEW-9.

The independent answer derivation (§8) is the main check for this.

---

## 6. Realism and safety rules for note text [OPERATIONAL]

- **Fictional only.** No real names (patients or staff), institutions, product brand names, record numbers or dates of birth. Staff appear by role only. Generic drug names are allowed; CAR-T product brand names are not.
- **No copied text.** Never copy from real notes, publications, or Lee 2019 beyond short criterion phrases.
- **Varied wording.**
  - Do not always use Table 6 wording. Use realistic abbreviations and note styles (SOAP notes, templated ICE forms, flowsheet-style nursing entries, narrative consults, reports).
  - Tension with A15: no clinician-approved phrase list exists yet. Until it does, varied wording must clearly fit **one** consciousness category, unless the scenario is SC-23. Any phrase the independent derivation reads differently goes to the disagreement log. [ASSUMPTION — EXPERT REVIEW]
- **Citable.** Every finding the intended answer relies on must be an exact quote in the text, so it can be cited by document, version, start and end (format §9).
- **Format rules.** Line breaks are `\n` only. Every file carries the fictional notice (format §3).

---

## 7. Leakage controls [OPERATIONAL]

"Leakage" means the inputs give away the answer, so a method can score well without doing the real task.

### 7.1 Inputs reveal nothing

- File names, case IDs, document IDs, `dataset_id`, `description` and any other metadata must not reveal the scenario or the answer.
- `amendment_reason` and `change_reason` must read like real audit-trail entries (e.g. "Late entry", "Addendum", "Corrected entry", "Data review"). Never "fixed to create grade mismatch".
- Document numbers follow the order of first documentation, as a chart export would.
- Features that occur in some scenarios (amendments, record revisions, EEG and imaging reports, "no ICANS" records, out-of-window documents) also occur in others (§5.1).

### 7.2 Case IDs

- Each set's cases are put in random order before IDs are given out.
- The order is produced by a seeded pseudo-random generator (a generator that gives the same order every time it is started from the same number, the **seed**). Proposal: Python's standard `random` module, so no new dependency.
- The seed, the generator used, and the list of cases in the order they were fed in are **stored with the answers** (`reference/<set>/`), so the ordering can be reproduced exactly.
- Development: `SYN-0001` to `SYN-0064`. Locked: a separate range (e.g. `SYN-5001` to `SYN-5144`). The range shows only which set a case belongs to.
- The ID-to-scenario map is stored only with the answers.

### 7.3 Where answers and scenario labels live

| Set | Cases | Intended answers, scenario labels, disagreement log, seeds |
|---|---|---|
| Development | `data/dev-v1/` (main repo) | `reference/dev-v1/` (main repo, outside `data/`) |
| Locked | `data/locked-v1/` (private repo) | `reference/locked-v1/` (private repo) |

The pipeline (Milestone 3) must never read `reference/`. Only evaluation code may.

### 7.4 Locked cases

- **Separate private GitHub repository**, never opened in a ReSauce Claude Code session. The user creates it manually.
- **Same scenario catalogue, new material:** new text, dates and combinations. No sentence reused from development cases (checked automatically, §9).
- **Writer's inputs:** only this plan, `clinical-methods.md` and `data-format.md`. Never pipeline code, never development case text.
- **Sealed:** after the locked answers are adjudicated:
  1. compute the SHA-256 fingerprint (a unique checksum) of every file in the locked dataset and its answers;
  2. list them, sorted by path, in a manifest;
  3. compute the SHA-256 of the manifest;
  4. record that value, the locked repo's commit ID and the date in the main repo (e.g. `docs/locked-seal.md`).
- Any later change to the locked set gets a new seal and a logged reason. Never silent.
- **Written before Milestone 3 starts.**
- **Human leakage:** the user reads a random 25% sample of locked cases plus every locked case with a disagreement (§9 check 10), so the user sees part of the locked content. Sampling keeps this smaller than reading every case. The user must not describe locked cases in ReSauce sessions. This risk is reduced, not removed.

### 7.5 Known limitation: Claude-written cases

Cases written by Claude may be systematically easier for Claude-based methods to read (ReSauce extraction and the Claude-based baseline). Claude also derives the independent answers, so shared blind spots can survive. **This bias cannot be fully removed.**

Proposed mitigations:
- a clinician-written or clinician-edited subset of locked cases (for example 15), with results reported separately for that subset [ASSUMPTION — EXPERT REVIEW; depends on clinician availability];
- deliberate style variation: each case gets a style randomly assigned from a list (terse, abbreviation-heavy, templated, verbose, with typos, mixed);
- the locked writer is a fresh session that never sees development text;
- results are reported by author type (Claude-written vs clinician-written or edited);
- optionally, a subset written by a non-Claude writer (a person, or another model). This needs a user decision.

---

## 8. Reference-answer procedure (outline; file format designed in Step 5)

### 8.1 What an answer contains, per case and field

| Item | Content |
|---|---|
| Category | §7.1–7.8; for an OOS case, "out of scope (reason)" instead of a category for both fields |
| Documentation-derived onset | A date, a date range, or "none found"; plus the signed difference from the record where defined (not for "record has no onset" or "no documented onset", §7.9) |
| Documentation-derived maximum grade | A grade, a grade range (e.g. 3–4, A33), or "undetermined" with the reason |
| Readings (7.5 only) | The reason, and the onset or grade and category under each reading |
| Evidence | Evidence references (document, version, start, end, quote) for every deciding observation |
| Extra flags | As listed in clinical-methods §7.10 |
| Record history | For multi-version records: which of the 7.6 conditions (a)–(c) hold for each field (§5.1) |
| Ambiguity notes | What is uncertain and why |
| Status and provenance | "not clinician-verified"; intended / independent / adjudicated; versions of `clinical-methods.md` and `data-format.md` used; the case-ordering seed (§7.2) |

### 8.2 Steps (user decision)

1. **Intended answer.** The case author records the scenario label and intended answer separately, when writing the case.
2. **Independent answer, in two stages.** A fresh Claude session derives answers. It is never told the intent or the scenario.
   - **Stage A.** The session is given the case's documents, `case.json`, `dataset.json`, `clinical-methods.md` and `data-format.md`, but **not `record.json`**. It derives the documentation-derived onset (date or range), the maximum grade, the evidence references, and the flags that do not depend on the record (e.g. time-imprecise, relative time, unsigned document, outside observation window, recurrence, out of scope for age or CAPD).
   - **Stage B.** Only then is `record.json` given. The session assigns the categories for both fields and adds the flags that need the record (e.g. superseded-version match, revision without new documentation, record date matches an excluded or sub-threshold symptom, out of scope for a Grade 5 record).
   - Proposal: the Stage A output is saved before Stage B starts. Any change to it during Stage B is logged with a reason.
   - **Why:** seeing the record first could anchor the checker towards agreeing with it.
3. **Comparison.** Field by field: category, onset or range, grade and deciding evidence.
4. **Disagreement log.** Every disagreement is recorded with: case, field, intended, independent, resolution, who decided, date.
5. **Adjudication by the user.** Each disagreement is either:
   - a **case bug** (the text does not say what was intended): fix the text, then re-run step 2; or
   - a **genuine ambiguity**: logged, and possibly added as a new open point (§10.2) or open question.
6. **Label.** All answers stay "not clinician-verified" until expert review.

Agreement between two Claude sessions is not proof of correctness (§7.5).

### 8.3 Scoring definitions (proposal; final wording in the later evaluation specification)

Fixed now, before any results exist, so they cannot be chosen to suit the results. [OPERATIONAL]

| Term | Definition |
|---|---|
| **Discrepancy alert** | A method assigns a field 7.1, 7.2, 7.3 or 7.8. |
| **Review flag** | A method assigns a field 7.4 or 7.5. |
| **False alert** | A discrepancy alert on a field whose reference answer is 7.6 or 7.7. |

- Review flags are reported separately. They are never counted as detections or as false alerts.
- OOS cases are scored only on whether they were flagged "out of scope". They never enter the discrepancy measurements.
- Left for the evaluation specification (not defined here):
  - whether a detection needs the exact category (e.g. 7.2) or any discrepancy alert;
  - how a discrepancy alert on a field whose reference answer is 7.4 or 7.5 is counted;
  - how simpler methods that never produce review flags are compared on those fields.

---

## 9. Dataset quality requirements

Every case must pass all checks before it is accepted. [OPERATIONAL]

| # | Check | How |
|---|---|---|
| 1 | Loads with `load_dataset` without errors | Automated now |
| 2 | Scenario label and intended answer recorded outside the case folder | Automatable later (file presence) |
| 3 | Every intended quote matches the text at its offsets | Automatable later (`check_evidence_ref`) |
| 4 | Independent derivation done in two stages (§8.2); every disagreement adjudicated and logged | Comparison automatable later; adjudication manual |
| 5 | No reused text between development and locked sets (e.g. no shared run of 8 or more words, excluding short criterion phrases; threshold to be agreed) | Automatable later |
| 6 | Reason fields and metadata do not leak the scenario or answer | Manual; a list of banned words can help |
| 7 | No real identifiers, brand names or institutions | Partly automatable (pattern and word lists); manual read |
| 8 | At least 2 distractors, and both negated and positive findings | Manual checklist |
| 9 | Event times in text are consistent with documentation times and record times | Manual now; partly automatable later |
| 10 | Human readability check: reads like plausible notes. **Development:** the user reads every case. **Locked:** the user reads a random 25% sample (about 36 of 144) plus every case with a disagreement. The sample is drawn with a recorded seed; the sample list and seed are stored with the answers. | Manual; sampling automatable |
| 11 | Note text is not empty or whitespace-only | Automated after the Step 4 loader fix |
| 12 | For every multi-version record, the 7.6 conditions (a)–(c) are written down for each field (§5.1) | Manual |
| 13 | The answer does not depend on any open point in §10.2 | Manual, using the "avoid" column of §10.2 |

---

## 10. Gaps

### 10.1 Resolved in `clinical-methods.md` v0.3

All 15 gaps from v0.1 are now decided provisionally by the user. Each is an assumption awaiting clinician review.

| Gap | Rule in v0.3 | Where | Assumption |
|---|---|---|---|
| GAP-1 | Record "no ICANS" vs documented ICANS: Grade 0, no onset; grade 7.2, onset 7.1 ("record has no onset") | §7.9(a) | A19 |
| GAP-2 | Empty onset or grade: new category 7.8 | §7.8 | A20 |
| GAP-3 | Record "no ICANS", no qualifying finding: 7.7 with at least one formal Grade 0 assessment and no "not assessable" period; otherwise 7.4 | §7.9(b) | A21 |
| GAP-4 | ICANS recorded, no qualifying finding: grade 7.3; onset 7.1 ("no documented onset") or 7.4 | §7.9(c) | A22 |
| GAP-5 | 7.5 widened to "Ambiguous evidence" with four reasons | §7.5 | A23 |
| GAP-6 | Formal Grade 0 assessment on the record's date beats an excluded or sub-threshold symptom → 7.1 + flag | §7.1 | A24 |
| GAP-7 | Documented "not assessable" period → 7.4; undocumented days → 7.3 + unassessed-period flag | §7.3 | A25 |
| GAP-8 | Relative-phrase table; signed difference to nearest end of range | §6.1, §7.1 | A26 |
| GAP-9 | Unsigned content never used; two flags | §6.3 | A27 |
| GAP-10 | 7.6 needs a value change, a correct current value and timely new documentation | §7.6 | A28 |
| GAP-11 | Out of scope: flag only, no categories | §5, §8 | A29 |
| GAP-12 | Competing cause: same note or within the 24 hours before | §3.4, §7.5 | A30 |
| GAP-13 | Copies differing only in dates, times or formatting are copied forward | §6.4 | A31 |
| GAP-14 | Window Day 0 to Day +28; out-of-window documents flagged and not used | §6.5 | A32 |
| GAP-15 | ICE 0 without consciousness information: range 3–4; record ≤ 2 → 7.2; record 3–4 → 7.4 | §4.1 | A33 |

### 10.2 New open points found while applying the decisions

**None is decided here.** For each one, the "avoid" column says how cases are written so that their answers do not depend on it until it is decided.

| ID | Situation | Decision needed | How cases avoid it for now |
|---|---|---|---|
| NEW-1 | ICANS recorded, no qualifying finding (A22), **and** a documented "not assessable" period in the window | A22 says grade 7.3; A25 says a "not assessable" period gives 7.4. Which wins? | SC-53 has no "not assessable" period. |
| NEW-2 | Record "no ICANS", at least one formal Grade 0 assessment, but ungradeable neurological symptoms elsewhere (e.g. "confused", no ICE) | A21 gives 7.7. Under missing ≠ absent such symptoms could hide ICANS, and §7.3 treats them as "not gradeable". Should they block 7.7? | SC-52 cases contain no such symptoms. |
| NEW-3 | 7.5 where every reading gives the same category (e.g. record G1; the readings give G2 or G3, both higher) | The 7.5 condition is about changing the derived value, so this is 7.5. But A33 treats a similar range (3–4 vs a record ≤ 2) as 7.2. Should 7.5 apply only when the readings lead to different categories? | In every 7.5 scenario, one reading matches the record and the other does not. |
| NEW-4 | Definitions of "gradeable assessment" and "documented 'not assessable' period" | These now decide categories (§7.1, A21, A24, A25) and the day list of the unassessed-period flag. Does a nursing note "awakens to voice" without ICE count as a gradeable assessment for that day? Does documented sedation without the words "not assessable" count as such a period? | Every assessment an answer relies on includes an ICE score; "not assessable" periods are stated explicitly. Proposal: until decided, the flag's day list in reference answers is marked provisional. |
| NEW-5 | Where the unassessed-period flag is added | Decided only for A21 (always) and A25 (7.3 with undocumented days). Also for other fields, e.g. 7.7 grade or onset with undocumented days? | Reference answers add it only where decided. |
| NEW-6 | The flag "record date matches an excluded or sub-threshold symptom" | Decided for the 7.1 outcome (A24). Is it also added when the same symptom gives 7.4 (no gradeable assessment that day; SC-45, 47, 53)? | Not added in those scenarios. |
| NEW-7 | A field that changed value more than once | Which change does 7.6 condition (c) test, e.g. the last change, which produced the current value? | Each field changes value at most once per record (§5.1). |
| NEW-8 | Is a document "outside the window" judged by its documentation date or by the event dates it describes? | E.g. a Day +29 late entry about Day +27, or a Day +28 note about later events. Also: does a death documented after Day +28 still make the case out of scope (A29)? | Out-of-window documents have both dates outside the window; no documented death is planned. |
| NEW-9 | Relative-time ranges combined with other evidence | How to choose the earliest onset when a range (e.g. Day +5 to +6) overlaps a timed finding; how the 24-hour competing-cause window (A30) applies to a finding whose time is a range. | SC-26 has a single range finding and no competing cause; no relative phrase is used near the onset elsewhere. |
| NEW-10 | Documented baseline developmental delay in an adult | §5 puts it out of scope, but the A29 trigger list does not include it. Is it a fifth trigger? | No case contains it. |

### 10.3 Consequences of applying the decisions (please confirm)

These are not new rules. They follow directly from the decisions, but they change earlier text:
- **clinical-methods §7.4 worked example:** the grade result changed from 7.4 to 7.7. Under A25, undocumented days alone no longer give 7.4. The example now states that the documents support the recorded Grade 1.
- **SC-49** follows that example: grade changed from 7.4 to 7.7, and the scenario now states that the record grade equals the documented grade. Grade 7.4 is still covered by SC-16, 17 and 60.
- **SC-04 and every 7.3 scenario:** undocumented days are now allowed (they add the unassessed-period flag); a documented "not assessable" period is not.
- **Stage A flags (§8.2):** some flags need the record (e.g. superseded-version match), so they are added in Stage B. Stage A derives only the flags that do not need it.
- **SC-52 is not labelled "plain".** "Plain" means the answer rests on one plainly stated fact. SC-52's answer rests on the absence of any qualifying finding across all notes, plus at least one formal Grade 0 assessment. Change the label if you meant "plain" in that sense.

---

## 11. Open questions

1. **Approve the numbers?** 64 development cases; 144 locked cases (138 scored, 6 OOS); 40.6% Neg among scored locked cases; 25% of Neg cases are "no ICANS" records (14, all SC-52). Or the smaller alternative (§4.2).
2. **Clinician involvement** (already open): who reviews A1–A33 (A19–A33 are new in v0.3, plus the realism of each scenario), and can a clinician write or edit a subset of locked cases?
3. **Baselines are not specified** in any project document yet. Proposal: write a short baseline specification before Milestone 3, and before anyone sees locked results.
4. **Overlap threshold** for "no reused sentences" (§9 check 5): is 8 words right?
5. **Non-Claude writer** for a subset (§7.5): wanted? A different model would add a new tool, which needs the user's approval.
6. **Locked adjudicator:** the user, or a different person, to reduce human leakage (§7.4)?
7. **Format question Q1** (format §12): must later versions give a reason?
8. **New open points NEW-1 to NEW-10** (§10.2): who decides them, and when? Proposal: before Step 5. NEW-4 and NEW-5 affect the flag lists of most reference answers.
9. **Rules with no scenario yet** (§3.3): add scenarios for any of them? Each new scenario adds 1 development and 2 locked cases.
10. **Out-of-window documents** in about 10% of cases (§5.1): agree?
11. **Scoring details** left for the evaluation specification (§8.3): exact-category detection, alerts on 7.4/7.5 fields, methods without review flags.
12. **SC-52 concentration:** 14 locked cases come from one scenario. Accept, or add a second "no ICANS" Neg scenario (e.g. a course dominated by CRS, with frequent formal Grade 0 assessments) to share the extra cases?
