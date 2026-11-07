# ReSauce dataset plan

- **Status:** Draft v0.1 (2026-11-07), for user review. Milestone 2 Step 3. **Not approved.** All case numbers are a proposal.
- **Builds on:** `docs/clinical-methods.md` v0.2 (cited as §) and `docs/data-format.md` v0.1 (cited as "format §").
- **This file contains no cases, case text, reference answers or code.** It plans them.

Tags follow `docs/clinical-methods.md`:

| Tag | Meaning |
|---|---|
| `[OPERATIONAL]` | A choice ReSauce makes for this plan. |
| `[ASSUMPTION — EXPERT REVIEW]` | Needs a clinician's input. |
| `GAP-n` | `clinical-methods.md` does not define the correct answer. Listed in §10. **Not decided here.** |

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
- Answers are derived from `clinical-methods.md`. Until a clinician reviews them, every answer is labelled **"not clinician-verified"**.

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
| 7.5 Ambiguous attribution | yes | yes |
| 7.6 Legitimate revision | yes | yes |
| 7.7 No discrepancy | yes | yes |

  So the dataset must cover **5 onset categories** and **6 grade categories**.
- Extra flags that do not replace the category are written after a "+" (for example "+ recurrence flag", §6.5).
- **Type** of case [OPERATIONAL]:
  - **Pos**: at least one field is 7.1, 7.2 or 7.3 (a discrepancy).
  - **Neg**: both fields are 7.6 or 7.7 (no discrepancy).
  - **Flag**: no discrepancy, but at least one field is 7.4 or 7.5 (for review).
  - **Gap**: the correct answer depends on an open gap (§10). Such cases are written, but not scored until the gap is decided.
  - "plain" marks a case whose answer rests on **one plainly stated fact**. Simple methods should have a fair chance on these. This label describes the design, not a predicted result.
- "Day +N" counts from infusion (Day 0). "G" means grade. Exact days in cases will vary; the days here only show the pattern.

### 2.2 Plain cases

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-01 | Typical course recorded correctly: first finding Day +5 (ICE 9), worst Day +6 (ICE 4, awakens to voice); record onset Day +5, G2 | §6.2, §7.7, A2 | 7.7 | 7.7 | Neg, plain |
| SC-02 | Brief Grade 1 only, recorded correctly | §7.7 | 7.7 | 7.7 | Neg, plain |
| SC-03 | One clear ICE score (G2) is the only abnormal finding; record says G1 | §3.3, §7.2, A8 | 7.7 | 7.2 (+1) | Pos, plain |
| SC-04 | Record G3; notes support only G2 (ICE 5, awakens to voice); no Grade 3 finding; no unassessed period (see GAP-7) | §7.3, A8 | 7.7 | 7.3 | Pos, plain |
| SC-05 | Record onset 2 days early; ICE 10 and alert on the recorded date | §7.1, A4 | 7.1 (−2) | 7.7 | Pos, plain |
| SC-06 | Record onset 2 days late | §7.1, A4 | 7.1 (+2) | 7.7 | Pos, plain |

### 2.3 Grade domains beyond ICE

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-07 | ICE alone gives the wrong grade: ICE 8 plus awakens only to touch, no sedation; record follows ICE (G1) | §3.5, §3.4, A15 | 7.7 | 7.2 (+2) | Pos |
| SC-08 | Same pattern; record correctly says G3 | §3.5, A15 | 7.7 | 7.7 | Neg |
| SC-09 | A non-ICE domain sets the grade (rapidly resolving seizure, focal motor weakness or diffuse edema; vary across cases); record correct | §3.3, §3.4 | 7.7 | 7.7 | Neg |
| SC-10 | Imaging report states diffuse cerebral edema (G4); record G3 | §3.3, §7.2 | 7.7 | 7.2 (+1) | Pos, plain |
| SC-11 | Record G3 counts an intracranial hemorrhage on imaging; other findings G2 | §4.2, Table 6 footnote # | 7.7 | 7.3 | Pos |
| SC-12 | Record G3 counts EEG slowing (not a seizure) as a seizure; other findings G2 | §3.3 notes | 7.7 | 7.3 | Pos |
| SC-13 | Record G4 rests on a raised-ICP sign found only in the source text, not Table 6; Table 6 findings G2 | §3.3, A12 | 7.7 | 7.3 + A12 review flag | Pos |

### 2.4 ICE 0 and assessability

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-14 | ICE 0, awake with global aphasia (documented wakefulness); record G3 | §3.4, §4.1, A15 | 7.7 | 7.7 | Neg |
| SC-15 | ICE 0, unarousable, no competing cause documented; record G3 | §3.4, §4.1 | 7.7 | 7.2 (+1) | Pos |
| SC-16 | ICE 0, no consciousness information; record G4 | §4.1, §7.4 | 7.7 | 7.4 | Flag |
| SC-17 | Sedated, documented "not assessable" during the period that would decide the record's G4; other days G2 | §4.1, §7.3, §7.4, A7 | 7.7 | GAP-7 | Gap |
| SC-18 | Partial ICE with no stated total is the only assessment on the record's onset date; first qualifying finding a day later; grade correct | §4.1, §7.1, A6 | 7.4 | 7.7 | Flag |
| SC-19 | Partial ICE where the note states a total; record matches | §4.1, A6 | 7.7 | 7.7 | Neg |
| SC-20 | Low ICE with a documented language barrier decides the grade | §4.1, A10 | 7.7 | GAP-5 | Gap |

### 2.5 Consciousness wording

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-21 | Recorded onset date has "awakens spontaneously" with no drowsiness and ICE 10 (Grade 0); first qualifying finding next day; grade correct | §3.3, §7.1, A3 | 7.1 (−1) | 7.7 | Pos |
| SC-22 | Drowsiness documented with spontaneous waking (G1) on the recorded onset date; record correct | §3.3, A3, A15 | 7.7 | 7.7 | Neg |
| SC-23 | A consciousness phrase that could fit two categories decides the grade | A15 | 7.7 | GAP-5 | Gap |

### 2.6 Time

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-24 | Onset finding observed before midnight (explicit date and time in text), note documented after midnight; record uses the event date | §6.1 | 7.7 | 7.7 | Neg |
| SC-25 | Onset finding with no event time in the note; record uses the documentation date | §6.1 | 7.7 + time-imprecise label | 7.7 | Neg |
| SC-26 | Onset finding described with a relative phrase ("overnight") | §6.1, §7.1 | GAP-8 | 7.7 | Gap |
| SC-27 | Late-signed EEG report: seizure on Day +7, report signed Day +10; record G2 on Day +8, revised to G3 on Day +10 | §6.1, §7.6 | 7.7 | 7.6 | Neg |
| SC-28 | Same EEG report; record never revised (stays G2) | §6.1, §7.2 | 7.7 | 7.2 (+1) | Pos |
| SC-29 | A late-entry note documents an earlier first finding; record onset revised after it | §6.1, §7.6 | 7.6 | 7.7 | Neg |

### 2.7 Note versions and record history

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-30 | Note v1 supports G2; amended v2 (signed, current) supports G1; record G2 | §6.3, §7.3 | 7.7 | 7.3 + superseded-version match | Pos |
| SC-31 | Amendment adds a higher-grade finding; record not updated | §6.3, §7.2 | 7.7 | 7.2 + superseded-version match | Pos |
| SC-32 | Latest version of a note is unsigned and differs from the signed version | §6.3, format §12 Q3 | 7.7 | 7.7 by §6.3; any flag: GAP-9 | Gap |
| SC-33 | Record revised to a higher grade with no supporting documentation; current value wrong | §7.3, §7.6 | 7.7 | 7.3 | Pos |
| SC-34 | Record onset corrected (clerical) with no new documentation; current value agrees | §7.6, §7.7 | GAP-10 | 7.7 | Gap |

### 2.8 Repeated and conflicting observations

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-35 | Same finding in a nursing note (evening) and restated in next morning's physician note; record uses the earlier date | §6.4 | 7.7 | 7.7 | Neg |
| SC-36 | Same documents; record uses the physician note's date | §6.4, §7.1 | 7.1 (+1) | 7.7 | Pos |
| SC-37 | Text copied forward verbatim into notes after documented resolution; no real recurrence | §6.4, §6.5, A13 | 7.7 (no recurrence flag) | 7.7 | Neg |
| SC-38 | Two assessments within the same hour disagree, and the disagreement decides the grade | §6.4 | 7.7 | GAP-5 | Gap |

### 2.9 Distinct episodes

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-39 | Documented full resolution, then recurrence; record onset from the first episode, grade the highest of both | §6.5, A2, A5 | 7.7 + recurrence flag | 7.7 | Neg |
| SC-40 | Same pattern; record onset from the recurrence (the recurrence holds the highest grade) | §6.5, §7.1, A5 | 7.1 + recurrence flag | 7.7 | Pos |

### 2.10 Attribution

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-41 | The grade-deciding finding is in the same note as a documented competing cause (e.g. a sedative given shortly before); no clinician statement | §3.4, §7.5, A9 | 7.7 | 7.5 | Flag |
| SC-42 | The earliest finding is in the same note as a documented competing cause; record onset is the next, unambiguous finding | §3.4, §7.5, A9 | 7.5 | 7.7 | Flag |
| SC-43 | A clinician attributes a finding to another cause; the record counts it | §3.4, §7.3, A9 | 7.7 | 7.3 | Pos |
| SC-44 | Finding during CRS fever; a clinician explicitly attributes it to ICANS; record correct | §2, §3.4, A9 | 7.7 | 7.7 | Neg |

### 2.11 Onset from non-qualifying evidence and missing evidence

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-45 | Recorded onset date has only an excluded symptom (tremor or headache), no gradeable assessment that day | §4.2, §7.1, A11 | 7.4 | 7.7 | Flag |
| SC-46 | Recorded onset date has an excluded symptom **and** ICE 10 with no other findings | §7.1, A11, A18 | GAP-6 | 7.7 | Gap |
| SC-47 | Recorded onset date has only a sub-threshold symptom (e.g. word-finding difficulty, no ICE) | §7.1, A18 | 7.4 | 7.7 | Flag |
| SC-48 | Recorded onset date has only a narrative normal neuro note (no ICE) | §7.1, A17 | 7.4 | 7.7 | Flag |
| SC-49 | No notes on the days around the recorded onset (§7.4 example) | §7.4 | 7.4 | 7.4 | Flag |

### 2.12 Record-level situations the methods do not cover

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-50 | Record says no ICANS; notes document qualifying ICANS | §7 | GAP-1 | GAP-1 | Gap |
| SC-51 | Record says ICANS; onset and/or grade left empty | §7, format §7 | GAP-2 | GAP-2 | Gap |
| SC-52 | Record says no ICANS; notes contain no qualifying finding | §7.4, §7.7 | GAP-3 | GAP-3 | Gap |
| SC-53 | Record says ICANS; notes contain only ungradeable symptoms (e.g. "confused", no ICE or consciousness level) | §7.3 | GAP-4 | 7.3 | Gap |

### 2.13 Out of scope (the pipeline must flag these)

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-54 | Age under 18 at infusion | §5, A16 | out-of-scope flag; GAP-11 | out-of-scope flag; GAP-11 | Gap |
| SC-55 | Adult case with a CAPD assessment in a note | §5 | out-of-scope flag; GAP-11 | out-of-scope flag; GAP-11 | Gap |
| SC-56 | Record maximum grade 5 | §8 | GAP-11 | Grade 5 flag; GAP-11 | Gap |

### 2.14 Note formats

| ID | Scenario | Rules | Onset | Grade | Type |
|---|---|---|---|---|---|
| SC-57 | Key findings only in templated or flowsheet-style notes with heavy abbreviations; record correct | §6.1 | 7.7 | 7.7 | Neg |
| SC-58 | The only higher-grade finding is stated once, clearly, inside a long discharge summary; record lower | §7.2 | 7.7 | 7.2 | Pos, plain |

### 2.15 Totals

| Type | Scenarios |
|---|---|
| Pos | 19 (6 of them plain) |
| Neg | 16 |
| Flag | 8 |
| Gap | 15 |
| **Total** | **58** |

Realism of each scenario (whether such documentation occurs in practice) has not been checked by a clinician. [ASSUMPTION — EXPERT REVIEW]

---

## 3. Coverage matrix

Proposed case counts per scenario [OPERATIONAL]:
- **Development:** 1 case per scenario (58).
- **Locked:** 2 cases per scenario, except:
  - 4 cases each for SC-27, SC-29, SC-41, SC-42 (the only scenarios for onset 7.5 and 7.6 and grade 7.5 and 7.6);
  - 4 cases each for SC-01, SC-02, SC-09 (extra no-discrepancy cases);
  - 1 case each for the 15 Gap scenarios.

Counts were computed with a throwaway script from the catalogue above.

### 3.1 Categories

| Field | Category | Scenarios | Dev cases | Locked cases |
|---|---|---|---|---|
| Onset | 7.1 | SC-05, 06, 21, 36, 40 | 5 | 10 |
| Onset | 7.4 | SC-18, 45, 47, 48, 49 | 5 | 10 |
| Onset | 7.5 | SC-42 | 1 | 4 |
| Onset | 7.6 | SC-29 | 1 | 4 |
| Onset | 7.7 | 36 scenarios (all others with a defined onset) | 36 | 77 |
| Onset | Gap-dependent | SC-26, 34, 46, 50–56 | 10 | 10 |
| Grade | 7.2 | SC-03, 07, 10, 15, 28, 31, 58 | 7 | 14 |
| Grade | 7.3 | SC-04, 11, 12, 13, 30, 33, 43, 53 | 8 | 15 |
| Grade | 7.4 | SC-16, 49 | 2 | 4 |
| Grade | 7.5 | SC-41 | 1 | 4 |
| Grade | 7.6 | SC-27 | 1 | 4 |
| Grade | 7.7 | 28 scenarios | 28 | 63 |
| Grade | Gap-dependent | SC-17, 20, 23, 32, 38, 50–52, 54–56 | 11 | 11 |

Every category appears in both sets. Onset 7.5 and 7.6, and grade 7.5 and 7.6, rest on a single scenario each. That is a weakness: one scenario's wording dominates those categories. Step 4 may add a second scenario for each if the user wants.

### 3.2 Assumptions

| Assumption | Scenarios | Dev | Locked |
|---|---|---|---|
| A1 (manuscript = published) | Not testable with data | – | – |
| A2 (max grade over time) | SC-01, 27, 39, 40 | 4 | 12 |
| A3 (spontaneous waking needs drowsiness) | SC-21, 22 | 2 | 4 |
| A4 (0-day onset tolerance) | SC-05, 06, 21, 36, 40 | 5 | 10 |
| A5 (one episode) | SC-39, 40 | 2 | 4 |
| A6 (partial ICE) | SC-18, 19 | 2 | 4 |
| A7 (not assessable) | SC-17 | 1 | 1 (gap-dependent) |
| A8 (under = mismatch, over = unsupported) | 7.2 and 7.3 scenarios except SC-53 | 14 | 28 |
| A9 (attribution only from clinicians) | SC-41, 42, 43, 44 | 4 | 12 |
| A10 (barriers) | SC-20 | 1 | 1 (gap-dependent) |
| A11 (excluded symptoms) | SC-45, 46 | 2 | 3 |
| A12 (text-only ICP signs) | SC-13 | 1 | 2 |
| A13 (copied-forward text) | SC-37 | 1 | 2 |
| A14 (Lee 2019 is current) | Not testable with data | – | – |
| A15 (consciousness phrases) | SC-07, 08, 14, 15, 22, 23 | 6 | 11 |
| A16 (age ≥ 18) | SC-54 | 1 | 1 (gap-dependent) |
| A17 (narrative normal note) | SC-48 | 1 | 2 |
| A18 (symptom-based onset) | SC-46, 47 | 2 | 3 |

### 3.3 Other rules

| Rule | Scenarios |
|---|---|
| §3.5 ICE alone is not the grade | SC-07, 08 |
| §4.1 ICE 0 and assessability | SC-14, 15, 16, 17 |
| §4.2 excluded findings | SC-11, 13, 45, 46 |
| §5 / §8 out of scope | SC-54, 55, 56 |
| §6.1 event vs documentation time | SC-24, 25, 26, 27, 28, 29 |
| §6.3 note versions | SC-30, 31, 32 |
| §6.4 repeated and conflicting | SC-35, 36, 37, 38 |
| §6.5 episodes | SC-39, 40 |

---

## 4. Size and balance (proposal for user approval)

### 4.1 Proposed numbers [OPERATIONAL]

| Set | Cases | Scored now | Gap-dependent |
|---|---|---|---|
| Development | 58 | 43 | 15 |
| Locked | 115 | 100 | 15 |

Locked scored cases: 42 Neg (42%), 38 Pos, 20 Flag.

Counted per field (2 fields per case, 200 scored fields): 140 fields expected 7.6/7.7, 38 expected 7.1–7.3, 22 expected 7.4/7.5.

### 4.2 Why these numbers

- **Development, 1 per scenario:** the minimum that lets the pipeline be built against every rule. It is for building, not measuring.
- **Locked, about 2 per scenario:** each scenario is seen in new wording, so a method cannot pass by matching one phrasing. Rare categories get 4 cases so none rests on 2.
- **42% no-discrepancy cases:** enough negatives to measure false alerts (§4.3). The real-world share of discrepancies is unknown, and this share does not claim to match it.
- **Workload:** 173 cases in total, written in batches (about 10 per batch). A larger set would take longer to adjudicate than the user can realistically review.
- **Smaller alternative:** 1 locked case per scenario (58 cases, about 57 negative fields). The false-alert bound would then be about 6.3% instead of 2.7% (see §4.3).

### 4.3 What this size can and cannot show

**Method.** 95% Wilson score interval for a proportion *x/n*, with *z* = 1.96 (*p* = *x/n*):

centre = (*p* + *z*²/2*n*) / (1 + *z*²/*n*); half-width = *z* · √(*p*(1−*p*)/*n* + *z*²/4*n*²) / (1 + *z*²/*n*).

**Worked example** (*x* = 10, *n* = 100): *p* = 0.10; *z*²/*n* = 0.0384; centre = 0.1192 / 1.0384 = 0.1148; half-width = 1.96 × 0.0316 / 1.0384 = 0.0596; interval 5.5% to 17.4%.

When *x* = 0, the upper bound is *z*²/(*n* + *z*²). For *n* = 140: 3.84 / 143.84 = 2.7%. For *n* = 57: 3.84 / 60.84 = 6.3%.

| What is measured | n | If observed | 95% Wilson interval |
|---|---|---|---|
| False alerts on no-discrepancy fields | 140 | 0 | 0.0% to 2.7% |
| | 140 | 14 (10%) | 6.1% to 16.1% |
| Discrepancy fields correctly flagged | 38 | 19 (50%) | 34.8% to 65.2% |
| | 38 | 38 (100%) | 90.8% to 100% |
| One category (e.g. grade 7.2) | 14 | 7 (50%) | 26.8% to 73.2% |
| | 14 | 14 (100%) | 78.5% to 100% |
| A rare category (e.g. onset 7.5) | 4 | 2 (50%) | 15.0% to 85.0% |

All values were computed by script; none is quoted from elsewhere.

**Can show:**
- a rough overall false-alert rate on these synthetic cases;
- a rough overall detection rate;
- which scenarios each method gets wrong (case by case, which matters most for a proof of concept).

**Cannot show:**
- reliable per-category rates: with 4 to 15 cases per category, intervals are 20 to 70 percentage points wide;
- small differences between ReSauce and the simpler methods. Both run on the same cases, so a paired comparison is possible, but which test to use and how large a difference it can detect is not calculated here;
- anything about real records.

**The intervals above are too narrow.** They assume every field is independent. In fact the two fields of one case are related, cases from the same scenario are related, and one writer wrote them all. The true uncertainty is larger, by an amount not computed here.

---

## 5. Case construction rules [OPERATIONAL]

### 5.1 One case

| Element | Rule |
|---|---|
| Documents per case | 3 to 12 (most 4 to 8). Count chosen independently of the scenario. |
| Note types | All 8 `note_type` values used across the set. At least 2 types per case. EEG and imaging reports also appear with normal results in unrelated cases, so their presence does not hint at a scenario. |
| Author roles | All 7 roles used. Role fits the note type (e.g. radiologist writes imaging reports). |
| Documentation times | Realistic shifts, including night notes and non-round times. Event times in the text are at or before documentation time, unless the scenario needs otherwise. |
| Dates | Fictional infusion dates spread over several years and months. Days from infusion vary between cases of the same scenario. |
| Age | 18 to 85, varied. Under 18 only in SC-54. |
| Amendments | About 15–25% of all cases have an amended note, including cases where the amendment changes nothing relevant (e.g. a corrected vital sign). |
| Record history | Multi-version records appear in Pos, Neg and Flag cases, not only in revision scenarios. Every record history is part of the intended answer: a revision explained by later notes makes that field 7.6 (§7.6). |
| Record values | Must pass format §7 rules. |

### 5.2 Distractors

Each case contains at least 2 realistic distractors, for example:
- CRS fever, low blood pressure and their treatment (§2);
- excluded symptoms: tremor, headache, myoclonus, hallucinations (§4.2);
- irrelevant neuro history (e.g. remote migraine, neuropathy from earlier chemotherapy);
- normal tests (normal EEG, unremarkable imaging);
- routine nursing content.

Each case contains both **negated** findings (e.g. "no seizure activity", "no focal deficits") and **positive** findings.

A distractor must not change the answer by accident. For example:
- a sedative near a finding creates ambiguous attribution (§7.5);
- an excluded symptom on the record's onset date creates GAP-6;
- an undocumented day in a 7.3 case touches GAP-7.

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
- Features that occur in some scenarios (amendments, record revisions, EEG and imaging reports) also occur in others (§5.1).

### 7.2 Case IDs

- Each set's cases are put in random order before IDs are given out.
- Development: `SYN-0001` to `SYN-0058`. Locked: a separate range (e.g. `SYN-5001` onward). The range shows only which set a case belongs to.
- The ID-to-scenario map is stored only with the answers.

### 7.3 Where answers and scenario labels live

| Set | Cases | Intended answers, scenario labels, disagreement log |
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
- **Human leakage:** the user adjudicates locked disagreements, so the user sees some locked content. The user must not describe locked cases in ReSauce sessions. This risk is reduced, not removed.

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
| Category | §7.1–7.7, or "pending GAP-n" |
| Documentation-derived onset | A date, a date range, or "none found"; plus the signed difference from the record where defined |
| Documentation-derived maximum grade | A grade, or "undetermined" with the reason |
| Evidence | Evidence references (document, version, start, end, quote) for every deciding observation |
| Extra flags | e.g. time-imprecise, recurrence, superseded-version match, A12 text-only sign, out of scope |
| Ambiguity notes | What is uncertain and why |
| Status and provenance | "not clinician-verified"; intended / independent / adjudicated; versions of `clinical-methods.md` and `data-format.md` used |

### 8.2 Steps (user decision)

1. **Intended answer.** The case author records the scenario label and intended answer separately, when writing the case.
2. **Independent answer.** A fresh Claude session derives answers. It is given only the case files (notes, record, case facts), `clinical-methods.md` and `data-format.md`. It is never told the intent or the scenario.
3. **Comparison.** Field by field: category, onset or range, grade and deciding evidence.
4. **Disagreement log.** Every disagreement is recorded with: case, field, intended, independent, resolution, who decided, date.
5. **Adjudication by the user.** Each disagreement is either:
   - a **case bug** (the text does not say what was intended): fix the text, then re-run step 2; or
   - a **genuine ambiguity**: logged, and possibly added as a new gap or open question.
6. **Label.** All answers stay "not clinician-verified" until expert review.

Agreement between two Claude sessions is not proof of correctness (§7.5).

---

## 9. Dataset quality requirements

Every case must pass all checks before it is accepted. [OPERATIONAL]

| # | Check | How |
|---|---|---|
| 1 | Loads with `load_dataset` without errors | Automated now |
| 2 | Scenario label and intended answer recorded outside the case folder | Automatable later (file presence) |
| 3 | Every intended quote matches the text at its offsets | Automatable later (`check_evidence_ref`) |
| 4 | Independent derivation done; every disagreement adjudicated and logged | Comparison automatable later; adjudication manual |
| 5 | No reused text between development and locked sets (e.g. no shared run of 8 or more words, excluding short criterion phrases; threshold to be agreed) | Automatable later |
| 6 | Reason fields and metadata do not leak the scenario or answer | Manual; a list of banned words can help |
| 7 | No real identifiers, brand names or institutions | Partly automatable (pattern and word lists); manual read |
| 8 | At least 2 distractors, and both negated and positive findings | Manual checklist |
| 9 | Event times in text are consistent with documentation times and record times | Manual now; partly automatable later |
| 10 | Human readability check: reads like plausible notes | Manual |
| 11 | Note text is not empty or whitespace-only | Automated after the Step 4 loader fix |

---

## 10. Gaps found in `clinical-methods.md`

These are situations where the methods do not define the correct answer. **None is decided here.** Each needs a decision (by the user, ideally with a clinician) before reference answers for the affected scenarios can be fixed.

| Gap | Situation | Decision needed | Scenarios |
|---|---|---|---|
| GAP-1 | Record says no ICANS, but notes document qualifying ICANS | Category for each field. §7.1 and §7.2 assume a recorded value to compare. | SC-50 |
| GAP-2 | Record says ICANS, but onset and/or grade is empty | Category for an empty field; whether the other field is still compared | SC-51 |
| GAP-3 | Record says no ICANS, and notes have no qualifying finding | Is this 7.7, or 7.4 because missing ≠ absent (§7.4)? If 7.7, what Grade 0 documentation is needed (how many assessments, over which days)? **Until decided, every Neg case must contain ICANS.** | SC-52 |
| GAP-4 | Record says ICANS, but no qualifying finding exists | Onset category (§7.1 assumes a documented onset exists). Grade is 7.3 by §7.3. | SC-53 |
| GAP-5 | Ambiguity that is not about attribution: conflicting assessments (§6.4), barriers (A10), ambiguous phrases (A15) | These are called "ambiguous" but have no §7 category. Map to 7.4, widen 7.5, or add a category? | SC-20, 23, 38 |
| GAP-6 | Record's onset date has an excluded or sub-threshold symptom **and** a gradeable no-ICANS assessment | §7.1 bullet 2 gives mismatch; bullet 4 gives insufficient evidence. Which wins? Also: is "the record dates onset from a symptom" judged only by matching dates? | SC-46 |
| GAP-7 | Record grade is above the supported grade, but an unassessable or undocumented period could hide a higher grade | 7.3 or 7.4? Which periods count as "relevant days" (§7.4)? **Until decided, 7.3 cases must have no such period.** | SC-17 (and constrains SC-04 and other 7.3 cases) |
| GAP-8 | Relative time phrases ("overnight", "since yesterday") | A table converting phrases to date ranges (§6.1 gives none). How the signed difference is reported when onset is a range (§7.1). | SC-26 |
| GAP-9 | Unsigned latest version of a note; or a note with no signed version at all | Is unsigned content ignored, reported or flagged? What is "current" if nothing is signed? (Also format §12 Q3.) | SC-32 |
| GAP-10 | Record revisions | When is a revision "explained by later documentation" (§7.6)? Is a field 7.6 or 7.7 when a revision has no new documentation but the current value agrees? Does any explained revision make a field 7.6? | SC-34 (and all multi-version records) |
| GAP-11 | Out-of-scope cases | Is the case only flagged, or are §7 categories also computed? For a Grade 5 record, what happens to the onset field? | SC-54, 55, 56 |
| GAP-12 | Timing of a competing cause | §3.4 says "near", §7.5 says "coincides"; no time window is given. SC-41 and SC-42 avoid this by putting the cause in the same note. | SC-41, 42 (as written) |
| GAP-13 | Copied-forward text | §6.4 defines it as "repeated unchanged". Lightly edited copies are not covered. SC-37 uses verbatim copies only. | SC-37 (as written) |
| GAP-14 | Observation window | No window has been chosen (§6.5 says it is declared per dataset). Handling of findings outside it is undefined (format §12 Q5). Needed before cases with late findings or recurrences are written. | SC-39, 40 and all cases |
| GAP-15 | ICE 0 with no consciousness information, when the record says Grade 2 or lower | ICE 0–2 meets the Grade 3 ICE criterion, but §4.1 calls ICE 0 without consciousness information insufficient. 7.2 or 7.4? | None planned |

---

## 11. Open questions

1. **Approve the numbers?** 58 development and 115 locked cases (100 scored, 15 gap-dependent), 42% no-discrepancy among scored locked cases. Or the smaller alternative (§4.2).
2. **Who decides the gaps in §10, and when?** Proposal: before Step 5, ideally with a clinician. Gap-dependent cases stay unscored until then.
3. **Clinician involvement** (already open): who reviews A1–A18, and can a clinician write or edit a subset of locked cases?
4. **Observation window** (GAP-14): which days should each dataset declare?
5. **Scoring:** do 7.4 and 7.5 count as alerts when measuring false alerts? This changes what "false alert" means. To be fixed before any locked results are seen.
6. **Baselines are not specified** in any project document yet. Proposal: write a short baseline specification before Milestone 3, and before anyone sees locked results.
7. **Independent derivation inputs:** the user's wording was "only the note text". This plan assumes the record and case facts are also given, because categories cannot be assigned without them. Confirm.
8. **Overlap threshold** for "no reused sentences" (§9 check 5): is 8 words right?
9. **Non-Claude writer** for a subset (§7.5): wanted? A different model would add a new tool, which needs the user's approval.
10. **Locked adjudicator:** the user, or a different person, to reduce human leakage (§7.4)?
11. **Single-scenario categories** (onset 7.5 and 7.6, grade 7.5 and 7.6): add a second scenario for each in Step 4?
12. **Format questions** that affect cases (format §12): Q1 (must later versions give a reason) and Q3 (must the latest version be signed).
