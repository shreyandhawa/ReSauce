# ReSauce dataset plan

- **Status:** v0.3.2, approved by the user (2026-11-07).
- **Builds on:** `docs/clinical-methods.md` v0.4 (cited as §) and `docs/data-format.md` v0.1.1 (cited as "format §").
- **This file contains no cases, case text, reference answers or code.** It plans them.

## Changelog

**v0.3.1 → v0.3.2** (user decision, 2026-11-08): the user no longer skims the development cases. This replaces the skim described in §4.2 and §9 check 10, which are left as written. It is disclosed as a limitation (`docs/evaluation-spec.md` §6).

**v0.3 → v0.3.1** (user decisions, 2026-11-07; the scenario catalogue, categories, case numbers and §8.3 scoring definitions are unchanged):
- Locked cases are now written **after** the pipeline is built (Milestone 3) and **before** any evaluation run (Milestone 4), instead of before Milestone 3 (§1, §7.4). A new protection logs every change to `clinical-methods.md` or this plan made before locked writing (§7.4). The weaker commitment is disclosed in §7.5.
- Readability check: the user skims every development case (about 2 minutes each). Locked-set sampling is unchanged (§4.2, §9 check 10).
- The remaining development cases are written in batches of about 17 (§4.2).

**v0.2 → v0.3** (the user's provisional decisions on NEW-1 to NEW-10 are in `clinical-methods.md` v0.4: A34 is new; A7, A15, A21–A26, A28–A30 and A32 are amended):
- NEW-1 to NEW-10 move to the "resolved" table (§10.1). §10.2 now lists only the points found in this round, NEW-11 to NEW-18, each with an "avoid" rule.
- The user accepts the §10.3 consequences. SC-52 stays not "plain".
- Seven edge-rule scenarios, SC-65 to SC-71, with 1 development and 1 locked case each. This is an exception to the 2-per-scenario rule (§3).
- A second "no ICANS" Neg scenario, SC-72 (a course dominated by CRS). SC-52's 14 locked cases are split evenly between SC-52 and SC-72, and each gets 1 extra case to keep the balance rules (§4.1).
- The new flags appear as distractors in named scenarios (§2.1).
- Sizes recomputed by script: 72 development and 153 locked cases (§4).
- §2.1: the unassessed-period flag is case-level. §5.1: the window is applied per observation (NEW-8); every later version gives a reason (format Q1). §8.1 and §8.2: which stage adds each flag.
- §11: the user's answers are recorded (§11.1) and removed from the open list (§11.2).
- Scenario rows lose their "(NEW-n)" markers where the point is now decided.

Tags follow `docs/clinical-methods.md`:

| Tag | Meaning |
|---|---|
| `[OPERATIONAL]` | A choice ReSauce makes for this plan. |
| `[ASSUMPTION — EXPERT REVIEW]` | Needs a clinician's input. |
| `NEW-n` | NEW-1 to NEW-10 are decided (§10.1). NEW-11 onward are open points found in this round, listed in §10.2. **Not decided here.** |

---

## 1. Purpose and status

**What the dataset is for.** [OPERATIONAL]
- To build the pipeline (development set).
- To measure the pipeline and the simpler verification approaches on the same cases (locked evaluation set).
- To check that every rule in `clinical-methods.md` is exercised at least once in each set, as far as the scenarios allow (§3.3 lists the rules that are not).

**What it cannot show.**
- The data is synthetic. Results on it are **not clinical validation**.
- The cases are written to test rules. Their mix of discrepancies is chosen by us. Rates measured on it (for example, how often flags are correct) **do not carry over** to real research records.
- It cannot show whether the rules in `clinical-methods.md` are clinically right. Only expert review can (§9 of that file).
- Answers are derived from `clinical-methods.md`. Until a clinician reviews them, every answer is labelled **"not clinician-verified"**. A19–A34 and the v0.4 amendments are provisional user decisions, so answers that rest on them are doubly provisional.

**Agreed order** (user decisions; changed in v0.3.1):
1. Step 3: this dataset plan.
2. Step 4: development cases, plus a small loader fix (whitespace-only note text is currently accepted).
3. Step 5: reference answers for the development cases.
4. Milestone 3: the pipeline.
5. Step 6: locked evaluation cases, written after the pipeline is built and before any evaluation run (§7.4).
6. Milestone 4: evaluation.

Steps 3 to 5 come before Milestone 3. Until v0.3.1, Step 6 also came before Milestone 3.

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
- **Case-level flags** (§7.10, v0.4) belong to the whole case and are not written in the Onset or Grade columns:
  - **unassessed period:** added to every in-scope case. It lists the days in the window with no gradeable assessment and any documented "not assessable" period. The list may be empty (A21, A25 as amended; NEW-5). With 3 to 12 documents over 29 days, most cases will list many days.
  - **ungradeable neurological symptom:** added to any in-scope case where such a symptom is documented (A21 as amended; NEW-2). The scenario text says where one is placed.
- **New flags as distractors** (they cannot change the answer where they are placed):
  - "ungradeable neurological symptom" is placed in SC-52 (the development case and about half of the locked cases), SC-60 and SC-67. All three are "no ICANS" records: the symptom cannot change the answer there (A21 as amended), and §7.3 does not apply to them (NEW-12). It is also part of the design of SC-47 and SC-53.
  - "record date matches an excluded or sub-threshold symptom" on a **7.4** onset is placed in every case of SC-18 and SC-48: an excluded symptom (e.g. tremor or headache) on the record's onset date, which already has no gradeable assessment, so the onset stays 7.4. It is also part of the design of SC-45, SC-47 and SC-53 (7.4) and SC-46 (7.1).
- **Type** of case [OPERATIONAL]:
  - **Pos**: at least one field is 7.1, 7.2, 7.3 or 7.8 (a discrepancy).
  - **Neg**: both fields are 7.6 or 7.7 (no discrepancy).
  - **Flag**: no discrepancy, but at least one field is 7.4 or 7.5 (for review).
  - **OOS**: out of scope (§5, A29). No category for either field. Scored only on whether the case is flagged "out of scope (reason)".
  - "plain" marks a case whose answer rests on **one plainly stated fact**. Simple methods should have a fair chance on these. This label describes the design, not a predicted result.
  - "no ICANS" marks a record with `icans_reported` = false.
- "Day +N" counts from infusion (Day 0). "G" means grade. Exact days in cases will vary; the days here only show the pattern. Every finding the answer relies on lies within the observation window, Day 0 to Day +28 (A32).
- "New in v0.3" marks scenarios added in this round.

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
| SC-18 | Partial ICE with no stated total is the only assessment on the record's onset date; first qualifying finding a day later; grade correct. Distractor: an excluded symptom (e.g. tremor) is also documented on the record's onset date | §4.1, §7.1, A6, A24, A34 | 7.4 + record date matches an excluded or sub-threshold symptom | 7.7 | Flag |
| SC-19 | Partial ICE where the note states a total; record matches | §4.1, A6 | 7.7 | 7.7 | Neg |
| SC-20 | Low ICE with a documented language barrier decides the grade; one reading matches the record, the other does not, so the readings lead to different categories | §4.1, §7.5, A10, A23 | 7.7 | 7.5 (assessment barrier) | Flag |

### 2.5 Consciousness wording

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-21 | Recorded onset date has "awakens spontaneously" with no drowsiness and ICE 10 (Grade 0); first qualifying finding next day; grade correct | §3.3, §7.1, A3 | 7.1 (−1) | 7.7 | Pos |
| SC-22 | Drowsiness documented with spontaneous waking (G1) on the recorded onset date; record correct | §3.3, A3, A15 | 7.7 | 7.7 | Neg |
| SC-23 | A consciousness phrase that could fit two categories decides the grade; one reading matches the record, the other does not, so the readings lead to different categories | §7.5, A15, A23 | 7.7 | 7.5 (consciousness wording) | Flag |

### 2.6 Time

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-24 | Onset finding observed before midnight (explicit date and time in text), note documented after midnight; record uses the event date. Counterpart of SC-59 | §6.1 | 7.7 | 7.7 | Neg |
| SC-59 | Same documents as the SC-24 pattern; record uses the documentation date. Counterpart of SC-24: tests a hypothesised ReSauce advantage, so both versions must exist | §6.1, §7.1, A4 | 7.1 (+1) | 7.7 | Pos |
| SC-25 | Onset finding with no event time in the note; record uses the documentation date | §6.1 | 7.7 + time-imprecise | 7.7 | Neg |
| SC-26 | Onset finding described as "overnight" in a note documented on date D (range D−1 to D); record onset D−1; no other finding overlaps the range | §6.1, §6.2, §7.1, A26 | 7.7 + relative time | 7.7 | Neg |
| SC-27 | Late-signed EEG report: seizure on Day +7, report signed Day +10; record G2 on Day +8, revised to G3 on Day +10. The report's `documented_at` is after the Day +8 record version and no later than the revision | §6.1, §7.6, A2, A28 | 7.7 | 7.6 | Neg |
| SC-28 | Same EEG report; record never revised (stays G2) | §6.1, §7.2 | 7.7 | 7.2 (+1) | Pos |
| SC-29 | A late-entry note documents an earlier first finding; record onset revised after it. The late entry's `documented_at` is between the two record versions | §6.1, §7.6, A28 | 7.6 | 7.7 | Neg |

### 2.7 Note versions and record history

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-30 | Note v1 supports G2; amended v2 (signed, current) supports G1; record G2 | §6.3, §7.3, A25 | 7.7 | 7.3 + superseded-version match | Pos |
| SC-31 | Amendment adds a higher-grade finding; record not updated. Counterpart of SC-63 | §6.3, §7.2 | 7.7 | 7.2 + superseded-version match | Pos |
| SC-63 | Amendment adds a higher-grade finding; record grade revised after it. The amendment's `documented_at` is between the two record versions. Counterpart of SC-31 | §6.3, §7.6, A2, A28 | 7.7 | 7.6 | Neg |
| SC-62 | Onset revised after an amended note: a signed amendment adds an earlier, timed finding to an existing note; record onset revised after it. The amendment's `documented_at` is between the two record versions | §6.3, §7.6, A28 | 7.6 | 7.7 | Neg |
| SC-32 | Latest version of a note is unsigned and contains a higher-grade finding than the signed version; record matches the signed version | §6.3, A27 | 7.7 | 7.7 + unsigned later version | Neg |
| SC-33 | Record revised to a higher grade with no supporting documentation; current value wrong | §7.3, §7.6, A25, A28 | 7.7 | 7.3 (history shown) | Pos |
| SC-34 | Record onset corrected (clerical) with no new documentation; current value agrees | §7.6, §7.7, A28 | 7.7 + revision without new documentation | 7.7 | Neg |

### 2.8 Repeated and conflicting observations

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-35 | Same finding in a nursing note (evening) and restated in next morning's physician note; record uses the earlier date | §6.4 | 7.7 | 7.7 | Neg |
| SC-36 | Same documents; record uses the physician note's date | §6.4, §7.1, A4 | 7.1 (+1) | 7.7 | Pos |
| SC-37 | Text copied forward into notes after documented resolution, verbatim or with only dates, times or formatting changed (vary across cases); no real recurrence | §6.4, §6.5, A13, A31 | 7.7 (no recurrence flag) | 7.7 | Neg |
| SC-38 | Two assessments within the same hour disagree, and the disagreement decides the grade; one reading matches the record, the other does not, so the readings lead to different categories | §6.4, §7.5, A23 | 7.7 | 7.5 (conflicting assessments) | Flag |
| SC-61 | Two assessments within the same hour disagree on the earliest day (one meets a Grade 1 criterion, one is a formal Grade 0 assessment); record onset is the next day, from an unambiguous finding. Readings: onset that day (record +1, 7.1) or the next day (7.7) | §6.4, §7.5, A23 | 7.5 (conflicting assessments) | 7.7 | Flag |

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
| SC-45 | Recorded onset date has only an excluded symptom (tremor or headache), no gradeable assessment that day | §4.2, §7.1, A11, A24, A34 | 7.4 + record date matches an excluded or sub-threshold symptom | 7.7 | Flag |
| SC-46 | Recorded onset date has an excluded symptom **and** a formal Grade 0 assessment (ICE 10, no other findings); first qualifying finding later | §7.1, A4, A11, A18, A24 | 7.1 (−N) + record date matches an excluded or sub-threshold symptom | 7.7 | Pos |
| SC-47 | Recorded onset date has only a sub-threshold symptom (e.g. word-finding difficulty, no ICE, no consciousness description), so the case carries the "ungradeable neurological symptom" flag. The grade answer depends on NEW-12 (§10.2) and is marked so | §7.1, A18, A21, A24, A34 | 7.4 + record date matches an excluded or sub-threshold symptom | 7.7 (NEW-12) | Flag |
| SC-48 | Recorded onset date has a narrative normal neuro note (no ICE) as its only assessment. Distractor: an excluded symptom (e.g. headache) is also documented that day | §7.1, A17, A24, A34 | 7.4 + record date matches an excluded or sub-threshold symptom | 7.7 | Flag |
| SC-49 | No notes on the days around the recorded onset (record onset Day +3, G1); first qualifying finding Day +6 at G1; nothing higher documented (the §7.4 example) | §7.1, §7.4, A34 | 7.4 | 7.7 | Flag |

### 2.12 Record-level situations (§7.8, §7.9)

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-50 | Record says no ICANS; notes document qualifying ICANS (no competing cause) | §7.9(a), A8, A19 | 7.1 ("record has no onset") | 7.2 | Pos, no ICANS |
| SC-51 | Record says ICANS; maximum grade left empty; onset correct | §7.8, A20 | 7.7 | 7.8 | Pos |
| SC-64 | Record says ICANS; onset left empty; grade correct | §7.8, A20 | 7.8 | 7.7 | Pos |
| SC-52 | Record says no ICANS; formal Grade 0 assessments in the window; no qualifying finding; no "not assessable" period; distractors such as CRS fever, tremor or headache. An ungradeable neurological symptom is placed in the development case and about half of the locked cases (it does not block 7.7: A21 as amended) | §7.9(b), A21, A34 | 7.7 | 7.7 | Neg, no ICANS |
| SC-72 | **New in v0.3.** Record says no ICANS; a course dominated by CRS (fever, low blood pressure and their treatment over several days); frequent formal Grade 0 assessments; no qualifying finding; no "not assessable" period. Second "no ICANS" Neg scenario, to spread SC-52's cases | §2, §7.9(b), A21, A34 | 7.7 | 7.7 | Neg, no ICANS |
| SC-60 | Record says no ICANS; no formal assessment at all (narrative notes only); no qualifying finding. Distractor: an ungradeable neurological symptom | §7.9(b), A17, A21 | 7.4 | 7.4 | Flag, no ICANS |
| SC-53 | Record says ICANS; notes contain only ungradeable symptoms (e.g. "confused", no ICE or consciousness level), including on the record's onset date, with no gradeable assessment that day; no "not assessable" period (with one, the grade would be 7.4: A22 as amended) | §7.3, §7.9(c), A18, A22, A24, A25, A34 | 7.4 + record date matches an excluded or sub-threshold symptom | 7.3 | Pos |

### 2.13 Out of scope (the pipeline must flag these)

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-54 | Age under 18 at infusion | §5, A16, A29 | — | — | OOS (age under 18) |
| SC-55 | Adult case with a CAPD assessment in a note | §5, A29 | — | — | OOS (CAPD assessment) |
| SC-56 | Record maximum grade 5 (no documented death) | §8, A29 | — | — | OOS (record Grade 5) |

SC-69 (documented death) is in §2.15.

### 2.14 Note formats

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-57 | Key findings only in templated or flowsheet-style notes with heavy abbreviations; record correct | §6.1 | 7.7 | 7.7 | Neg |
| SC-58 | The only higher-grade finding is stated once, clearly, inside a long discharge summary; record lower | §7.2 | 7.7 | 7.2 | Pos, plain |

### 2.15 Edge rules (new in v0.3; 1 development and 1 locked case each)

These scenarios test edge rules that no earlier scenario reached (v0.2 §3.3). Each gets 1 case per set instead of 2 (§3).

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-65 | ICE 0 with no consciousness information is the highest finding; no other Grade 3 or 4 finding; record G2 or lower | §4.1, §7.2, A33 | 7.7 | 7.2 (documented range 3–4) | Pos |
| SC-66 | Record says ICANS with a grade; no qualifying finding anywhere in the window; a formal Grade 0 assessment on the record's onset date; no "not assessable" period | §7.1, §7.3, §7.9(c), A22 | 7.1 ("no documented onset") | 7.3 | Pos |
| SC-67 | Record says no ICANS; formal Grade 0 assessments; no qualifying finding; a documented "not assessable" period stated explicitly (e.g. "ICE not done, intubated and sedated"). Distractor: an ungradeable neurological symptom | §4.1, §7.9(b), A7, A21 | 7.4 | 7.4 | Flag, no ICANS |
| SC-68 | A document with no signed version holds the only higher-grade finding; the record matches the signed documents | §6.3, A27 | 7.7 | 7.7 + unsigned document | Neg |
| SC-69 | Documented death; record grade 1 to 4 (not 5). The development case documents the death inside the window; the locked case after Day +28 | §5, §8, A29 | — | — | OOS (documented death) |
| SC-70 | Record says no ICANS; the only qualifying finding has a documented competing cause in the same note or within the 24 hours before, and no clinician statement; formal Grade 0 assessments on other days; no "not assessable" period. Readings: ICANS (onset 7.1 "record has no onset", grade 7.2) or not ICANS (both 7.7) | §7.5, §7.9(a), A9, A19, A30 | 7.5 (attribution) | 7.5 (attribution) | Flag, no ICANS |
| SC-71 | Record G1; the earliest finding is Grade 2 without doubt; a later finding would be Grade 3 but has a documented competing cause and no clinician statement. Readings G2 or G3 both give 7.2 | §7.5, A9, A23, A30 | 7.7 | 7.2 (documented G2; both readings in the ambiguity notes) | Pos |

### 2.16 Totals

| Type | Scenarios |
|---|---|
| Pos | 28 (6 of them plain) |
| Neg | 24 (2 of them plain) |
| Flag | 16 |
| OOS | 4 |
| **Total** | **72** |

The script that produced these counts also checks that each scenario's type matches the definitions in §2.1.

Realism of each scenario (whether such documentation occurs in practice) has not been checked by a clinician. [ASSUMPTION — EXPERT REVIEW]

---

## 3. Coverage matrix

Proposed case counts per scenario [OPERATIONAL]:
- **Development:** 1 case per scenario (72).
- **Locked:** 2 cases per scenario, except:
  - 4 cases each for SC-51 and SC-64. They are the only scenarios for grade 7.8 and onset 7.8; with 2 cases each, those categories would have only 2 locked cases.
  - **1 case each for SC-65 to SC-71** (user decision). They test edge rules rather than main categories, and every category they reach is also reached by other scenarios. The cost: in the locked set each edge rule is seen in only one wording, so one case decides whether a method handles it.
  - 8 cases each for SC-52 and SC-72: SC-52's 14 locked cases from v0.2 split evenly (7 + 7), plus 1 extra each for the balance rules (§4.1).

All counts below were computed with a throwaway script from the catalogue above.

### 3.1 Categories

| Field | Category | Scenarios | Dev cases | Locked cases |
|---|---|---|---|---|
| Onset | 7.1 | SC-05, 06, 21, 36, 40, 46, 50, 59, 66 | 9 | 17 |
| Onset | 7.4 | SC-18, 45, 47, 48, 49, 53, 60, 67 | 8 | 15 |
| Onset | 7.5 | SC-42, 61, 70 | 3 | 5 |
| Onset | 7.6 | SC-29, 62 | 2 | 4 |
| Onset | 7.7 | 45 scenarios (all others in scope) | 45 | 101 |
| Onset | 7.8 | SC-64 | 1 | 4 |
| Grade | 7.2 | SC-03, 07, 10, 15, 28, 31, 50, 58, 65, 71 | 10 | 18 |
| Grade | 7.3 | SC-04, 11, 12, 13, 30, 33, 43, 53, 66 | 9 | 17 |
| Grade | 7.4 | SC-16, 17, 60, 67 | 4 | 7 |
| Grade | 7.5 | SC-20, 23, 38, 41, 70 | 5 | 9 |
| Grade | 7.6 | SC-27, 63 | 2 | 4 |
| Grade | 7.7 | 37 scenarios | 37 | 87 |
| Grade | 7.8 | SC-51 | 1 | 4 |
| Both | No category (OOS) | SC-54, 55, 56, 69 | 4 | 7 |

Every category appears in both sets, with at least 4 locked cases. Onset 7.8 and grade 7.8 each rest on one scenario; their definition is simple (an empty field).

### 3.2 Assumptions

| Assumption | Scenarios | Dev | Locked |
|---|---|---|---|
| A1 (manuscript = published) | Not testable with data | – | – |
| A2 (max grade over time) | SC-01, 27, 39, 40, 63 | 5 | 10 |
| A3 (spontaneous waking needs drowsiness) | SC-21, 22 | 2 | 4 |
| A4 (0-day onset tolerance) | SC-05, 06, 21, 36, 40, 46, 59 | 7 | 14 |
| A5 (one episode) | SC-39, 40 | 2 | 4 |
| A6 (partial ICE) | SC-18, 19 | 2 | 4 |
| A7 (not assessable; definition added in v0.4) | SC-17, 67 | 2 | 3 |
| A8 (under = mismatch, over = unsupported) | All 7.2 and 7.3 scenarios (19) | 19 | 35 |
| A9 (attribution only from clinicians) | SC-41, 42, 43, 44, 70, 71 | 6 | 10 |
| A10 (barriers) | SC-20 | 1 | 2 |
| A11 (excluded symptoms) | SC-45, 46 | 2 | 4 |
| A12 (text-only ICP signs) | SC-13 | 1 | 2 |
| A13 (copied-forward text) | SC-37 | 1 | 2 |
| A14 (Lee 2019 is current) | Not testable with data | – | – |
| A15 (consciousness phrases) | SC-07, 08, 14, 15, 22, 23 | 6 | 12 |
| A16 (age ≥ 18) | SC-54 | 1 | 2 |
| A17 (narrative normal note) | SC-48, 60 | 2 | 4 |
| A18 (symptom-based onset) | SC-46, 47, 53 | 3 | 6 |
| A19 ("no ICANS" record vs documented ICANS) | SC-50, 70 | 2 | 3 |
| A20 (7.8 missing recorded value) | SC-51, 64 | 2 | 8 |
| A21 ("no ICANS" record, no qualifying finding) | SC-52, 60, 67, 72 | 4 | 19 |
| A22 (ICANS recorded, no qualifying finding) | SC-53, 66 | 2 | 3 |
| A23 (7.5 ambiguous evidence; same-category rule) | SC-20, 23, 38, 61, 71 | 5 | 9 |
| A24 ("record date matches" flag) | SC-46 (7.1); SC-45, 47, 53 (7.4, by design); SC-18, 48 (7.4, distractor) | 6 | 12 |
| A25 (unassessed periods and 7.3 / 7.4) | All 7.3 scenarios, SC-17 | 10 | 19 |
| A26 (relative time phrases; earliest possible onset) | SC-26 | 1 | 2 |
| A27 (unsigned content) | SC-32, 68 | 2 | 3 |
| A28 (when a revision is 7.6) | SC-27, 29, 33, 34, 62, 63 (and every multi-version record, §5.1) | 6 | 12 |
| A29 (out of scope) | SC-54, 55, 56, 69 | 4 | 7 |
| A30 (24-hour competing-cause window) | SC-41, 42, 70, 71 | 4 | 6 |
| A31 (lightly edited copies) | SC-37 | 1 | 2 |
| A32 (window Day 0 to +28, per observation) | Every case; out-of-window documents per §5.1 | 72 | 153 |
| A33 (ICE 0, no consciousness information) | SC-16, 65 | 2 | 3 |
| A34 (gradeable assessment) | Every case (the unassessed-period flag). It decides the onset category in SC-18, 45, 47, 48, 49, 53 | 72 (6 deciding) | 153 (12 deciding) |

### 3.3 Other rules

| Rule | Scenarios |
|---|---|
| §3.5 ICE alone is not the grade | SC-07, 08 |
| §4.1 ICE 0 and assessability | SC-14, 15, 16, 17, 65, 67 |
| §4.2 excluded findings | SC-11, 13, 45, 46 |
| §5 / §8 out of scope | SC-54, 55, 56, 69 |
| §6.1 event vs documentation time | SC-24, 25, 26, 27, 28, 29, 59 |
| §6.3 note versions | SC-30, 31, 32, 62, 63, 68 |
| §6.4 repeated and conflicting | SC-35, 36, 37, 38, 61 |
| §6.5 episodes | SC-39, 40 |
| §7.5 reasons | attribution SC-41, 42, 70; conflicting assessments SC-38, 61; assessment barrier SC-20; consciousness wording SC-23 |
| §7.5 same category under every reading | SC-71 (grade) |
| §7.6 revisions | SC-27, 29, 62, 63 (7.6); SC-33 (revision, still wrong); SC-34 (revision without new documentation) |
| §7.8 missing recorded value | SC-51 (grade), SC-64 (onset) |
| §7.9 record-level situations | (a) SC-50, 70; (b) SC-52, 60, 67, 72; (c) SC-53, 66 |

**Flags (§7.10)**

| Flag | Scenarios |
|---|---|
| unassessed period (case-level) | Every in-scope case |
| ungradeable neurological symptom (case-level) | SC-47, 53 (by design); SC-52, 60, 67 (distractor) |
| record date matches an excluded or sub-threshold symptom | SC-46 (7.1); SC-45, 47, 53 (7.4, by design); SC-18, 48 (7.4, distractor) |
| unsigned later version / unsigned document | SC-32 / SC-68 |
| outside observation window | About 10% of cases (§5.1) |
| out of scope (reason) | SC-54, 55, 56, 69 |
| time-imprecise, relative time, recurrence, text-only ICP sign, superseded-version match, revision without new documentation | As in the scenario rows |

**Rules that still have no scenario** (listed for transparency; the user decided which scenarios to add in this round, and these were not among them). The evaluation will not measure them:
- §7.9(c) together with a documented "not assessable" period (NEW-1: grade 7.4). SC-53 and SC-66 have no such period.
- The same-category rule of §7.5 for **onset** (NEW-3: signed difference to the nearest reading). SC-71 covers grade only.
- A field that changed value more than once (NEW-7).
- The per-observation window where a document's dates are split, e.g. a late entry after Day +28 about an in-window event (NEW-8). Out-of-window documents keep all their dates outside (§5.1).
- An onset range shortened by an exactly dated finding (NEW-9a), and A30 for a range-dated finding (NEW-9b).
- Documented baseline developmental delay as an out-of-scope trigger (NEW-10).

---

## 4. Size and balance (proposal for final approval)

### 4.1 Proposed numbers [OPERATIONAL]

| Set | Cases | In discrepancy measurements | OOS (scored only on flagging) |
|---|---|---|---|
| Development | 72 | 68 | 4 |
| Locked | 153 | 146 | 7 |

**How the locked number was reached** (by script):
1. 2 cases per scenario for SC-01 to SC-64: 64 × 2 = 128 cases (122 scored + 6 OOS).
2. 4-case rule for SC-51 and SC-64: 2 extra each → 132 cases (126 scored + 6 OOS).
3. SC-52's 14 locked cases from v0.2 (2 + 12 extra) split evenly with the new SC-72: 7 + 7. That adds 12 to step 2 → 144 cases (138 scored + 6 OOS).
4. Edge scenarios SC-65 to SC-71: 1 each → 151 cases (144 scored + 7 OOS; SC-69 is OOS).
5. Check the balance rules and add "no ICANS" Neg cases if needed (table below).

After step 4, the 144 scored cases are 57 Neg, 57 Pos and 30 Flag. The 57 Neg are: 21 Neg scenarios from v0.2 other than SC-52, × 2 = 42; SC-52 7; SC-72 7; SC-68 1.

| Step | Scored cases | Neg | Neg share | "No ICANS" Neg | Share of Neg |
|---|---|---|---|---|---|
| After step 4 | 144 | 57 | 39.6% | 14 (SC-52 7, SC-72 7) | 24.6% |
| Add *x* extra "no ICANS" Neg cases | 144 + *x* | 57 + *x* | | 14 + *x* | |
| Rule 1: Neg share ≥ 40% | (57 + *x*) / (144 + *x*) ≥ 0.40 → 0.6*x* ≥ 0.6 → *x* ≥ **1** | | | | |
| Rule 2: "no ICANS" ≥ ¼ of Neg | (14 + *x*) / (57 + *x*) ≥ 0.25 → 0.75*x* ≥ 0.25 → *x* ≥ 0.33 → **1** | | | | |
| Minimum, *x* = 1 | 145 | 58 | 40.0% | 15 | 25.9% |
| **Proposed, *x* = 2** (1 each, spread across both "no ICANS" Neg scenarios as the user asked) | **146** | **59** | **40.4%** | **16** | **27.1%** |

Locked total: 146 scored + 7 OOS = **153**. This is below 160, so no cut is proposed. (With *x* = 1 the total would be 152, but the extra case could not be spread across both scenarios.)

Locked scored cases by type: 59 Neg (40.4%), 57 Pos, 30 Flag. Counting the 7 OOS cases in the denominator, the Neg share is 59 / 153 = 38.6%.

"No ICANS" records in the locked set: 16 Neg (SC-52 8, SC-72 8), 2 Pos (SC-50), 4 Flag (SC-60 2, SC-67 1, SC-70 1), 22 in all.

Counted per field (2 fields per scored case, 292 fields): 196 expected 7.6/7.7, 60 expected 7.1/7.2/7.3/7.8, 36 expected 7.4/7.5.

Development set (1 per scenario): 24 Neg of 68 scored (35.3%). The balance rules are for the locked set only; the development set is for building, not measuring.

### 4.2 Why these numbers

- **Development, 1 per scenario:** the minimum that lets the pipeline be built against every rule. It is for building, not measuring.
- **Locked, 2 per scenario:** each scenario is seen in new wording, so a method cannot pass by matching one phrasing. OOS scenarios are treated the same way.
- **Edge scenarios, 1 locked case each:** they test rules rather than categories (§3). This keeps the locked set below 160.
- **4-case rule only for SC-51 and SC-64:** every other category already has at least 4 locked cases.
- **At least 40% Neg:** enough no-discrepancy fields to measure false alerts (§4.3). The real-world share of discrepancies is unknown, and this share does not claim to match it.
- **At least a quarter of Neg cases are "no ICANS" records:** the user's rationale is that most real CAR-T patients do not develop ICANS, so a record of "no ICANS" is a common real situation. This rate is not sourced in this project's documents.
- **Concentration:** in v0.2, 14 of 56 locked Neg cases came from SC-52 alone. Now 16 of 59 come from two scenarios with different designs (SC-52 and SC-72), 8 each. Their wording, distractors, note styles and number of formal assessments must still vary.
- **Workload:** 225 cases in total (72 + 153). The first 20 development cases were written in batches of about 10; the remaining development cases are written in batches of about 17 (user decision, v0.3.1). The user skims all 72 development cases (about 2 minutes each) and reads about 38 locked cases (25% of 153) plus every locked case with a disagreement (§9 check 10).
- **Smaller alternative:** 1 locked case per scenario (72 cases, 68 scored, 86 no-discrepancy fields). The false-alert bound would then be 4.3% instead of 1.9% (§4.3), and the 40% and quarter rules would not be met without extra cases.

### 4.3 What this size can and cannot show

**Method.** 95% Wilson score interval for a proportion *x/n*, with *z* = 1.96 (*p* = *x/n*):

centre = (*p* + *z*²/2*n*) / (1 + *z*²/*n*); half-width = *z* · √(*p*(1−*p*)/*n* + *z*²/4*n*²) / (1 + *z*²/*n*).

**Worked example** (*x* = 10, *n* = 100): *p* = 0.10; *z*²/*n* = 0.0384; centre = 0.1192 / 1.0384 = 0.1148; half-width = 1.96 × 0.0316 / 1.0384 = 0.0596; interval 5.5% to 17.4%.

When *x* = 0, the upper bound is *z*²/(*n* + *z*²). For *n* = 196: 3.8416 / 199.84 = 1.9%. For *n* = 86: 3.8416 / 89.84 = 4.3%.

The *n* values use the scoring definitions in §8.3: false alerts are counted on fields whose reference answer is 7.6 or 7.7 (196 locked fields); detection on fields whose reference answer is 7.1, 7.2, 7.3 or 7.8 (60 locked fields).

| What is measured | n | If observed | 95% Wilson interval |
|---|---|---|---|
| False alerts on no-discrepancy fields | 196 | 0 | 0.0% to 1.9% |
| | 196 | 20 (10.2%) | 6.7% to 15.2% |
| Discrepancy fields correctly alerted | 60 | 30 (50%) | 37.7% to 62.3% |
| | 60 | 60 (100%) | 94.0% to 100% |
| One category (e.g. grade 7.2) | 18 | 9 (50%) | 29.0% to 71.0% |
| | 18 | 18 (100%) | 82.4% to 100% |
| A rare category (e.g. grade 7.6) | 4 | 2 (50%) | 15.0% to 85.0% |

All values were computed by script; none is quoted from elsewhere.

**Can show:**
- a rough overall false-alert rate on these synthetic cases;
- a rough overall detection rate;
- which scenarios each method gets wrong (case by case, which matters most for a proof of concept).

**Cannot show:**
- reliable per-category rates: with 4 to 18 cases per category (other than 7.7), intervals are about 30 to 70 percentage points wide;
- whether a method handles an edge rule (SC-65 to SC-71) in general: each rests on one locked case;
- small differences between ReSauce and the simpler methods. Both run on the same cases, so a paired comparison is possible, but which test to use and how large a difference it can detect is not calculated here;
- anything about real records.

**The intervals above are too narrow.** They assume every field is independent. In fact the two fields of one case are related, cases from the same scenario are related (8 locked cases share the SC-52 design and 8 the SC-72 design), and one writer wrote them all. The true uncertainty is larger, by an amount not computed here.

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
| Observation window | `dataset.json` declares `start_day` 0 and `end_day` 28 in both sets (A32). The window is applied per observation: each finding, assessment or "not assessable" statement is placed by its event date, or by its documentation date if it has no event time (A32 as amended; NEW-8). |
| Documents outside the window | **Agreed by the user:** about 10% of cases include one document outside the window (e.g. a pre-infusion baseline note, or a follow-up after Day +28). Unless a scenario needs otherwise, such a document keeps both its documentation date and every event date it mentions outside the window, so it is outside under any reading (NEW-11). Each one contains at least one neurological observation (e.g. a baseline ICE score, or a symptom at follow-up), so the "outside observation window" flag has something to list. In-window documents do not describe assessments dated outside the window (NEW-11). |
| Age | 18 to 85, varied. Under 18 only in SC-54. |
| Death and developmental delay | No case documents a death, except SC-69. No case documents baseline developmental delay (A29; NEW-10 has no scenario). |
| Amendments | About 15–25% of all cases have an amended note, including cases where the amendment changes nothing relevant (e.g. a corrected vital sign). All amendments are signed unless the scenario is SC-32. |
| Unsigned versions | Only where the scenario needs them (SC-32, SC-68), or as distractors whose omission cannot change the answer. Worked out under A27. |
| "Not assessable" periods | Only where the scenario needs them (SC-17, SC-67), or in cases where they cannot change the answer. Never in a 7.3 case (A25 would make it 7.4), a "no ICANS" Neg case (A21 would make it 7.4), SC-53 or SC-66 (A22 as amended would make the grade 7.4). Each one is stated explicitly and applies only to its own documentation date or names its days (NEW-18). |
| Reasons for later versions | **User decision (format Q1):** the format stays as it is, but in these datasets every document version from 2 onward has a non-null `amendment_reason`, and every record version from 2 onward a non-null `change_reason`. They read like a realistic audit trail (§7.1). |
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

A field may change value more than once. Condition (c) then tests the last change, the one that produced the current value; earlier changes are shown in the history (A28 as amended; NEW-7). For every multi-version record, the case author writes down which of (a), (b) and (c) hold for each field.

### 5.2 Distractors

Each case contains at least 2 realistic distractors, for example:
- CRS fever, low blood pressure and their treatment (§2);
- excluded symptoms: tremor, headache, myoclonus, hallucinations (§4.2);
- irrelevant neuro history (e.g. remote migraine, neuropathy from earlier chemotherapy);
- normal tests (normal EEG, unremarkable imaging);
- routine nursing content.

Each case contains both **negated** findings (e.g. "no seizure activity", "no focal deficits") and **positive** findings.

A distractor must not change the answer by accident. For example:
- a sedative or other competing cause in the same note as a finding, or within the 24 hours before it, creates ambiguous evidence when the readings lead to different categories (§7.5, A23, A30);
- an excluded or sub-threshold symptom on the record's onset date changes the onset result or adds a flag (§7.1, A24);
- a documented "not assessable" period turns a 7.3 grade into 7.4 (A25), a "no ICANS" 7.7 into 7.4 (A21), and a §7.9(c) grade into 7.4 (A22);
- an unsigned version, or an observation dated outside the window, is left out (A27, A32), which can change the answer;
- an ungradeable neurological symptom adds the case-level flag (A21). Until NEW-12 to NEW-14 are decided, it appears only where §2.1 places it (see the avoid rules in §10.2);
- a relative time phrase near the onset can change the onset (A26 as amended); near a competing cause it touches NEW-17, and across a window boundary NEW-16;
- a documented death, or baseline developmental delay, makes the case out of scope (A29).

The independent answer derivation (§8) is the main check for this.

---

## 6. Realism and safety rules for note text [OPERATIONAL]

- **Fictional only.** No real names (patients or staff), institutions, product brand names, record numbers or dates of birth. Staff appear by role only. Generic drug names are allowed; CAR-T product brand names are not.
- **No copied text.** Never copy from real notes, publications, or Lee 2019 beyond short criterion phrases.
- **Varied wording.**
  - Do not always use Table 6 wording. Use realistic abbreviations and note styles (SOAP notes, templated ICE forms, flowsheet-style nursing entries, narrative consults, reports).
  - Tension with A15: no clinician-approved phrase list exists yet. Until it does, varied wording must clearly fit **one** consciousness category, or be plainly normal (e.g. "alert", "awake and interactive"), unless the scenario is SC-23 (NEW-15). Any phrase the independent derivation reads differently goes to the disagreement log. [ASSUMPTION — EXPERT REVIEW]
  - Tension with NEW-12 and NEW-13: until they are decided, free symptom words for cognition or speech (e.g. "confused", "disoriented", "agitated", "word-finding difficulty") appear only where §2.1 places an ungradeable neurological symptom. Elsewhere, notes describe ICE results and Table 6 findings instead. Wording that is itself part of a grading rule is not a free symptom word (e.g. "awake, global aphasia" with ICE 0 in SC-14, Table 6 footnote ^, §4.1). This costs some realism (§10.2).
- **Citable.** Every finding the intended answer relies on must be an exact quote in the text, so it can be cited by document, version, start and end (format §9).
- **Format rules.** Line breaks are `\n` only. Every file carries the fictional notice (format §3).

---

## 7. Leakage controls [OPERATIONAL]

"Leakage" means the inputs give away the answer, so a method can score well without doing the real task.

### 7.1 Inputs reveal nothing

- File names, case IDs, document IDs, `dataset_id`, `description` and any other metadata must not reveal the scenario or the answer.
- `amendment_reason` and `change_reason` must read like real audit-trail entries (e.g. "Late entry", "Addendum", "Corrected entry", "Data review"). Never "fixed to create grade mismatch". Every version from 2 onward has one (§5.1).
- Document numbers follow the order of first documentation, as a chart export would.
- Features that occur in some scenarios (amendments, record revisions, unsigned versions, EEG and imaging reports, "no ICANS" records, out-of-window documents) also occur in others (§5.1).

### 7.2 Case IDs

- Each set's cases are put in random order before IDs are given out.
- The order is produced by a seeded pseudo-random generator (a generator that gives the same order every time it is started from the same number, the **seed**). Proposal: Python's standard `random` module, so no new dependency.
- The seed, the generator used, and the list of cases in the order they were fed in are **stored with the answers** (`reference/<set>/`), so the ordering can be reproduced exactly.
- Development: `SYN-0001` to `SYN-0072`. Locked: a separate range (e.g. `SYN-5001` to `SYN-5153`). The range shows only which set a case belongs to.
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
- **When (user decision, v0.3.1):** written after the pipeline is built (Milestone 3) and before any evaluation run (Milestone 4).
- **Protections that do not change:** the locked writer is a fresh session in the separate private repository that never sees pipeline code or development case text; its inputs are only this plan, `clinical-methods.md` and `data-format.md`; the scenario catalogue (§2) and the scoring definitions (§8.3) stay frozen; the baseline specification is written before anyone sees locked results.
- **New protection (v0.3.1):** if `clinical-methods.md` or this plan changes between now and locked writing, each change is logged with the date and whether pipeline development prompted it. The locked writer uses the logged versions.
- **Adjudicator (user decision, v0.3):** the user adjudicates the locked set.
- **Human leakage:** the user reads a random 25% sample of locked cases plus every locked case with a disagreement (§9 check 10), so the user sees part of the locked content. Sampling keeps this smaller than reading every case. The user must not describe locked cases in ReSauce sessions. This risk is reduced, not removed.

### 7.5 Known limitation: Claude-written cases

Cases written by Claude may be systematically easier for Claude-based methods to read (ReSauce extraction and the Claude-based baseline). Claude also derives the independent answers, so shared blind spots can survive. **This bias cannot be fully removed.**

Proposed mitigations:
- a clinician-written or clinician-edited subset of locked cases (for example 15), with results reported separately for that subset [ASSUMPTION — EXPERT REVIEW; depends on clinician availability];
- deliberate style variation: each case gets a style randomly assigned from a list (terse, abbreviation-heavy, templated, verbose, with typos, mixed);
- the locked writer is a fresh session that never sees development text;
- results are reported by author type (Claude-written vs clinician-written or edited).

A non-Claude writer (a person, or another model) is **not used for now** (user decision, v0.3). Revisit if no clinician can write or edit a subset.

**Trade-off of writing locked cases after the pipeline (v0.3.1).** The locked set is no longer fixed before pipeline work begins, so this commitment is weaker than originally planned. Whoever builds the pipeline (the user and Claude sessions) will know the pipeline's weak points when the locked cases are written, and could, even unintentionally, write cases that avoid or favour them. The protections in §7.4 (fresh writer session without pipeline code or development text, frozen catalogue and scoring definitions, logged rule changes) reduce this risk but do not remove it. It must be reported with the results.

---

## 8. Reference-answer procedure (outline; file format designed in Step 5)

### 8.1 What an answer contains, per case and field

| Item | Content |
|---|---|
| Category | §7.1–7.8; for an OOS case, "out of scope (reason)" instead of a category for both fields |
| Documentation-derived onset | A date, a date range (§6.2, A26), or "none found"; plus the signed difference from the record where defined (not for "record has no onset" or "no documented onset", §7.9) |
| Documentation-derived maximum grade | A grade, a grade range (e.g. 3–4, A33), or "undetermined" with the reason. When every reading gives the same category (§7.5), the lowest grade proven under every reading |
| Readings | For 7.5: the reason, and the onset or grade and category under each reading. When every reading gives the same category, that category is the answer and the readings go in the ambiguity notes (A23 as amended) |
| Evidence | Evidence references (document, version, start, end, quote) for every deciding observation |
| Extra flags | As listed in clinical-methods §7.10. Case-level flags (unassessed period, ungradeable neurological symptom, out of scope) are given once per case. Whether the other flags are stored per case or per field is settled with the answer file format in Step 5; no category depends on it |
| Record history | For multi-version records: which of the 7.6 conditions (a)–(c) hold for each field (§5.1) |
| Ambiguity notes | What is uncertain and why, including every reading |
| Dependence on open points | Any open point in §10.2 the answer depends on (only SC-47's grade, NEW-12, is expected) |
| Status and provenance | "not clinician-verified"; intended / independent / adjudicated; versions of `clinical-methods.md` and `data-format.md` used; the case-ordering seed (§7.2) |

### 8.2 Steps (user decision)

1. **Intended answer.** The case author records the scenario label and intended answer separately, when writing the case.
2. **Independent answer, in two stages.** A fresh Claude session derives answers. It is never told the intent or the scenario.
   - **Stage A.** The session is given the case's documents, `case.json`, `dataset.json`, `clinical-methods.md` and `data-format.md`, but **not `record.json`**. It derives the documentation-derived onset (date or range), the maximum grade, the evidence references, and every flag that does not depend on the record (table below).
   - **Stage B.** Only then is `record.json` given. The session assigns the categories for both fields and adds the flags that need the record.
   - Proposal: the Stage A output is saved before Stage B starts. Any change to it during Stage B is logged with a reason.
   - **Why:** seeing the record first could anchor the checker towards agreeing with it.
3. **Comparison.** Field by field: category, onset or range, grade and deciding evidence.
4. **Disagreement log.** Every disagreement is recorded with: case, field, intended, independent, resolution, who decided, date.
5. **Adjudication by the user** (for both sets; user decision, v0.3). Each disagreement is either:
   - a **case bug** (the text does not say what was intended): fix the text, then re-run step 2; or
   - a **genuine ambiguity**: logged, and possibly added as a new open point (§10.2) or open question.
6. **Label.** All answers stay "not clinician-verified" until expert review.

**Which stage adds each flag** (§7.10):

| Flag | Stage | Why |
|---|---|---|
| time-imprecise, relative time | A | From note text and documentation times only |
| text-only ICP sign | A | From note text only |
| unsigned later version, unsigned document | A | From document versions only |
| recurrence | A | From note text only |
| outside observation window | A | From observation dates and `dataset.json` |
| **unassessed period** (case-level) | A | Days without a gradeable assessment, and "not assessable" statements, come from the documents only |
| **ungradeable neurological symptom** (case-level) | A | From note text only |
| out of scope: age under 18, CAPD assessment, documented death, developmental delay | A | From `case.json` and note text |
| superseded-version match | B | Compares the record with document versions |
| revision without new documentation | B | Needs the record history |
| record date matches an excluded or sub-threshold symptom | B | Needs the record's onset date |
| out of scope: record Grade 5 | B | Needs the record. If found, it replaces both categories, and the case-level flags from Stage A are dropped (they apply only to in-scope cases) |

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
| 5 | No reused text between development and locked sets: no shared run of 8 or more words, excluding short criterion phrases (threshold agreed by the user, v0.3) | Automatable later |
| 6 | Reason fields and metadata do not leak the scenario or answer | Manual; a list of banned words can help |
| 7 | No real identifiers, brand names or institutions | Partly automatable (pattern and word lists); manual read |
| 8 | At least 2 distractors, and both negated and positive findings | Manual checklist |
| 9 | Event times in text are consistent with documentation times and record times | Manual now; partly automatable later |
| 10 | Human readability check: reads like plausible notes, and nothing gives the answer away. **Development:** the user skims every case (about 2 minutes each; v0.3.1). **Locked:** the user reads a random 25% sample (about 38 of 153) plus every case with a disagreement. The sample is drawn with a recorded seed; the sample list and seed are stored with the answers. | Manual; sampling automatable |
| 11 | Note text is not empty or whitespace-only | Automated after the Step 4 loader fix |
| 12 | For every multi-version record, the 7.6 conditions (a)–(c) are written down for each field (§5.1) | Manual |
| 13 | The answer does not depend on any open point in §10.2, except where §8.1 records it (SC-47's grade, NEW-12) | Manual, using the "avoid" column of §10.2 |
| 14 | Every document version from 2 onward has a non-null `amendment_reason`, and every record version from 2 onward a non-null `change_reason` (§5.1) | Automatable later |

---

## 10. Gaps and open points

### 10.1 Resolved

**In `clinical-methods.md` v0.3** (the 15 gaps from plan v0.1). All are provisional user decisions awaiting clinician review.

| Gap | Rule | Where | Assumption |
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

**In `clinical-methods.md` v0.4** (the 10 open points from plan v0.2). All are provisional user decisions awaiting clinician review.

| Point | Rule | Where | Assumption |
|---|---|---|---|
| NEW-1 | ICANS recorded, no qualifying finding, and a documented "not assessable" period: A25 wins, grade 7.4. Onset rule of §7.9(c) unchanged | §7.3, §7.9(c) | A22, A25 (amended) |
| NEW-2 | Ungradeable neurological symptoms do not block 7.7 in a "no ICANS" record; new case-level flag "ungradeable neurological symptom" in any in-scope case (excluded symptoms not included). Clinician question: should they block 7.7? | §7.9(b), §7.10 | A21 (amended) |
| NEW-3 | 7.5 only when the readings lead to different categories; otherwise that category, with the value every reading supports (grade: lowest proven under every reading; onset: signed difference to the nearest reading). Readings in the ambiguity notes | §7.5 | A23 (amended) |
| NEW-4 | Definitions: gradeable assessment (ICE total for the day, or a qualifying finding); documented "not assessable" period (a statement that assessment could not be done; sedation alone does not count) | §7 intro | A34 (new), A7 (amended) |
| NEW-5 | Unassessed-period flag is case-level, on every in-scope case; list may be empty | §7.3, §7.9(b), §7.10 | A21, A25 (amended) |
| NEW-6 | "Record date matches an excluded or sub-threshold symptom" whenever such a symptom is on the record's onset date and no qualifying finding exists that day, whatever the onset category | §7.1, §7.10 | A24 (amended) |
| NEW-7 | A field changed more than once: 7.6 condition (c) tests the last change | §7.6 | A28 (amended) |
| NEW-8 | Window applied per finding by event date (documentation date if none); out-of-window findings not used and flagged; a documented death makes the case out of scope whatever its date | §5, §6.5, §7.10 | A29, A32 (amended) |
| NEW-9 | (a) Onset is the earliest possible date; a range before every exact finding ends at the earlier of its end and the earliest exact date. (b) A30 for a range-dated finding: the 24 hours before the end of the range | §6.2, §3.4 | A26, A30 (amended) |
| NEW-10 | Documented baseline developmental delay in an adult is a fifth out-of-scope trigger | §5, §7.10 | A29 (amended) |

### 10.2 New open points found in this round

**None is decided here.** Each is on the clinician agenda (§11.2). For each one, the "avoid" column says how cases are written so that their answers do not depend on it. The one exception is marked.

| ID | Situation | Decision needed | How cases avoid it for now |
|---|---|---|---|
| NEW-11 | The NEW-8 decision speaks of **findings**. `clinical-methods.md` v0.4 applies the same date rule to assessments and "not assessable" statements. | Confirm that every observation (finding, assessment, "not assessable" statement) is placed in or out of the window by its event date, or its documentation date if it has no event time. | Out-of-window documents keep their documentation date and every event date outside the window, and in-window documents do not describe assessments dated outside it (§5.1). So every observation is in or out under any reading. |
| NEW-12 | §7.3 defines 7.3 as "the record's maximum grade is higher than any grade the quoted documentation supports, **or** the documentation describes neurological symptoms that are not gradeable". Read literally, the second clause makes any ungradeable symptom a 7.3, even when gradeable findings support the record's grade. The plan has always read it as describing documentation that supports no grade (as in SC-53). Excluded symptoms are not affected: A11 says they count for neither grade nor onset. | Which reading is meant? With the new flag, ungradeable symptoms will be recorded in more cases, so the reading matters more. | Ungradeable symptoms appear only in "no ICANS" cases (where §7.3 does not apply) and in SC-53 (7.3 under either reading). **Exception: SC-47** needs one by design. Its grade answer is recorded as 7.7 under the reading used so far and marked "depends on NEW-12" (§8.1). |
| NEW-13 | Scope of "ungradeable neurological symptom". The definition's example is "'confused' … with no ICE score or consciousness level". | Is a symptom such as "confused" ungradeable when the same note also documents an ICE total or a consciousness description (e.g. "alert, confused", or "confused, ICE 6/10")? This decides whether almost every ICANS case carries the flag. | Free symptom words for cognition or speech (e.g. "confused", "disoriented", "agitated", "word-finding difficulty") appear only where §2.1 places an ungradeable symptom, and there in a note with neither an ICE total nor a consciousness description (§6). Costs some realism until decided. |
| NEW-14 | An ungradeable symptom documented close in time to a formal Grade 0 assessment (e.g. "confused" in a nursing note and "ICE 10/10" in the same hour). | Is this "conflicting assessments" (§6.4, 7.5), or does the Grade 0 assessment stand? | An ungradeable symptom is never documented on the same calendar day as any ICE assessment. |
| NEW-15 | A consciousness description that fits no Table 6 category and is not plainly normal (e.g. "lethargic", or "drowsy" without a waking pattern). | Is it an ungradeable neurological symptom, an A15 phrase-list question (7.5), or neither? | Every consciousness description clearly fits one Table 6 category or is plainly normal, unless the scenario is SC-23 (§6). |
| NEW-16 | A relative-time range that crosses a window boundary (e.g. "overnight" in a note documented on Day 0, giving Day −1 to Day 0; or on Day +29, giving Day +28 to +29). | Is the finding inside the window, outside, or partly inside? | No relative-time range phrase ("overnight", "last night") in a note documented on Day 0 or Day +29. |
| NEW-17 | A30 for a range-dated finding (NEW-9b) counts the 24 hours back from "the end of the range". A range is a pair of dates. | Is the end the documentation time of the note (the latest the event can have happened), or the end of the range's last calendar day? | No competing cause is documented in the same note as, or within the 2 calendar days before, a finding dated by a range. |
| NEW-18 | A "not assessable" statement that does not say which days it covers (e.g. "ICE not done, intubated and sedated"). The definition says the period covers "the calendar days the statement applies to". | Only its documentation date, or until the next assessment? This affects only the day list of the unassessed-period flag (any period gives 7.4 under A21 and A25). | Every "not assessable" statement applies only to its own documentation date or names its days (§5.1). |

### 10.3 Consequences of the earlier decisions

**Accepted by the user (v0.3).** These follow from the v0.3 decisions and changed earlier text:
- **clinical-methods §7.4 worked example:** the grade result changed from 7.4 to 7.7. Under A25, undocumented days alone no longer give 7.4.
- **SC-49** follows that example: grade 7.7. Grade 7.4 is covered by SC-16, 17, 60 and 67.
- **SC-04 and every 7.3 scenario:** undocumented days are allowed; a documented "not assessable" period is not.
- **Stage A flags (§8.2):** flags that need the record are added in Stage B.
- **SC-52 stays not "plain"**: its answer rests on the absence of any qualifying finding across all notes, plus at least one formal Grade 0 assessment.

**Following from the v0.4 decisions** (no change to any expected category):
- SC-45, SC-47 and SC-53 now carry the flag "record date matches an excluded or sub-threshold symptom" (NEW-6).
- SC-47 and SC-53 now carry the case-level flag "ungradeable neurological symptom"; SC-52 may now contain such a symptom (NEW-2).
- Every in-scope case carries the unassessed-period flag, possibly with an empty list (NEW-5).
- SC-53's "no 'not assessable' period" constraint is now explained by A22 as amended (NEW-1).
- SC-20, 23 and 38 stay 7.5: in each, one reading matches the record and the other does not, so the categories differ (NEW-3).

---

## 11. Questions

### 11.1 Answered by the user in this round (v0.3)

| Question (v0.2 §11) | Answer | Recorded in |
|---|---|---|
| Overlap threshold for "no reused sentences" | 8 words, as proposed | §9 check 5 |
| Out-of-window documents in about 10% of cases | Agreed | §5.1 |
| Locked adjudicator | The user; the 25% readability sample stays | §7.4, §8.2, §9 check 10 |
| Non-Claude writer for a subset | Not now. Revisit if no clinician can write or edit a subset | §7.5 |
| Format Q1: must later versions give a reason? | The format stays as it is, but every document version and record version from 2 onward in the datasets gives a reason (a realistic audit trail) | §5.1, §9 check 14 |
| SC-52 concentration | Second "no ICANS" Neg scenario SC-72; locked cases split evenly | §2.12, §3, §4.1 |
| NEW-1 to NEW-10 | Decided provisionally | `clinical-methods.md` v0.4; §10.1 |
| Rules with no scenario | Seven edge scenarios added (SC-65 to SC-71), 1 + 1 cases each | §2.15, §3 |

### 11.2 Still open

1. **Approved by the user (2026-11-07). Case numbers:** 72 development cases; 153 locked cases (146 scored, 7 OOS); 40.4% Neg among scored locked cases; 27.1% of Neg cases are "no ICANS" records (16: SC-52 8, SC-72 8). Rules still without a scenario are listed in §3.3.
2. **Clinician involvement:** who reviews:
   - A1–A34, including the v0.4 amendments;
   - the realism of each scenario;
   - the A21 question: should ungradeable neurological symptoms block 7.7 in a "no ICANS" record?
   - the open points NEW-11 to NEW-18 (§10.2). Deciding NEW-12 and NEW-13 before Step 6 would let locked cases use free symptom words such as "confused" again.

   And can a clinician write or edit a subset of locked cases? If not, revisit the non-Claude writer (§7.5).
3. **Baselines are not specified** in any project document yet. Proposal: write a short baseline specification before Milestone 3, and before anyone sees locked results.
4. **Scoring details** left for the evaluation specification (§8.3): exact-category detection, alerts on 7.4/7.5 fields, methods without review flags.
