# Independent answers compared with intended answers (dev-v1)

Made by `tools/compare_answers.py` (run `python -m tools.compare_answers`). Intended answers: `reference/dev-v1/intended/`. Independent answers: `reference/dev-v1/independent/` (written blind by Claude Opus, not clinician-verified). Neither side is verified: a difference means the two disagree, not that either is wrong. No answer file was changed and nothing is adjudicated here. These are counts on synthetic cases, not clinical validation.

Cases in data/dev-v1: 72. Compared: 72.

## 1. Files that were missing, unreadable or incomplete

None. All independent files exist, parse, and have every field compared here.

## 2. Agreement counts

Value groups: **agree** = same grade, date or range; **form only** = a grade or date is missing on one or both sides, or the same grade/date is written differently; **real** = a different grade, date or range. `signed_difference_days` is not compared.

### All cases: 72 cases

- Out of scope: 72 of 72 cases agree (both in scope, or both out of scope with the same trigger).
- Onset category: 72 of 72 agree.
- Onset documented value (where both sides are in scope, 68 cases): 67 agree, 1 differ only in form, 0 real disagreement.
- Max grade category: 72 of 72 agree.
- Max grade documented value (where both sides are in scope, 68 cases): 64 agree, 4 differ only in form, 0 real disagreement.
- Category overall (both fields): 144 of 144 agree.
- Documented value overall (136 field comparisons): 131 agree, 5 differ only in form, 0 real disagreement.

### Dev split (20 cases): 20 cases

- Out of scope: 20 of 20 cases agree (both in scope, or both out of scope with the same trigger).
- Onset category: 20 of 20 agree.
- Onset documented value (where both sides are in scope, 19 cases): 19 agree, 0 differ only in form, 0 real disagreement.
- Max grade category: 20 of 20 agree.
- Max grade documented value (where both sides are in scope, 19 cases): 18 agree, 1 differ only in form, 0 real disagreement.
- Category overall (both fields): 40 of 40 agree.
- Documented value overall (38 field comparisons): 37 agree, 1 differ only in form, 0 real disagreement.

### Held-out split (not sealed): 52 cases

- Out of scope: 52 of 52 cases agree (both in scope, or both out of scope with the same trigger).
- Onset category: 52 of 52 agree.
- Onset documented value (where both sides are in scope, 49 cases): 48 agree, 1 differ only in form, 0 real disagreement.
- Max grade category: 52 of 52 agree.
- Max grade documented value (where both sides are in scope, 49 cases): 46 agree, 3 differ only in form, 0 real disagreement.
- Category overall (both fields): 104 of 104 agree.
- Documented value overall (98 field comparisons): 94 agree, 4 differ only in form, 0 real disagreement.

## 3. Independent evidence quotes

Quotes checked: 451. Not found exactly once in the named document version: 0.

## 4. Out-of-scope disagreements and out-of-scope cases

| Case | Split | Agree? | Intended | Independent |
|---|---|---|---|---|
| SYN-0001 | dev | agree | age under 18 | age under 18 at infusion (A29, section 5, A16) |
| SYN-0012 | held-out | agree | CAPD assessment | CAPD (Cornell Assessment of Pediatric Delirium) documented in a note (section 5, A29); patient age 65 is in scope by age |
| SYN-0031 | held-out | agree | documented death | documented death |
| SYN-0049 | held-out | agree | record Grade 5 | record maximum grade of 5 (clinical-methods section 5, section 8, A29) |

## 5. Category disagreements

None.

## 6. Real documented-value disagreements

Different grade, date or range. The category column says whether the categories agree.

None.

## 7. Documented values that differ only in form

A grade or date is missing on one or both sides, or the same grade/date is written differently. The category column says whether the categories agree.

5 field-level rows.

| Case | Split | Field | Category | Intended category / value | Independent category / value | What differs |
|---|---|---|---|---|---|---|
| SYN-0016 | held-out | max_grade | same | 7.3 / Grade 0 | 7.3 / no value (undetermined: no qualifying finding anywhere in the window; only ungradeable sympto…) | independent has no grade or date |
| SYN-0018 | held-out | max_grade | same | 7.5 / no value (undetermined: Grade 2 or Grade 3, depending on whether the Day +5 13:40 response wa…) | 7.5 / Grade 2 to 3 | intended has no grade or date |
| SYN-0047 | dev | max_grade | same | 7.5 / no value (undetermined: Grade 3 if the Day +6 07:30 finding is counted as ICANS, Grade 2 if i…) | 7.5 / Grade 2 to 3 | intended has no grade or date |
| SYN-0063 | held-out | onset | same | 7.5 (attribution) / 2033-01-25 (Day +6) | 7.5 / no value (undetermined: depends on attribution of the Day 6 ICE 6/10: onset 2033-01-25 (Day 6…) | independent has no grade or date |
| SYN-0069 | held-out | max_grade | same | 7.5 / no value (undetermined: Grade 2 if the Day +4 English-language ICE 4/10 is accepted; Grade 1…) | 7.5 / Grade 1 to 2 | intended has no grade or date |

## 8. Unclear rules reported in the blind run notes


Taken from `reference/dev-v1/independent-run-notes.md` (the blind-run report), one line each. "Format gap" = the answer format does not say; "rule gap" = `clinical-methods.md` does not say. For each format gap, "settled" names the Value convention in `reference/dev-v1/README.md` that now answers it; "open" means no convention does. Nothing here was adjudicated against a clinician. The report gives no case ID for items 7, 10 and 28; that is stated there.

### Format gaps

1. Batch 1, SYN-0002: whether a signed difference is reported for a 7.4 onset where the record is earlier than the first finding (gave −1). **Format gap, settled** by the 7.4 onset convention.
2. Batch 3, SYN-0025, SYN-0028, SYN-0036: the same question (reported the difference as informational). **Format gap, settled** by the 7.4 onset convention.
3. Batch 6, SYN-0072: §7.1 says "always reported" but the answer format gives null only for §7.9 (gave −3). **Format gap, settled** by the 7.4 onset convention.
4. Batch 2, SYN-0023: for a 7.5 onset with two readings that give different dates, whether the signed difference is the nearest reading (as A23 does for same-category readings) or null (used null). **Format gap, settled** by the 7.5 onset convention (null difference, each reading gives its own).
5. Batch 4, SYN-0046: which difference to report when readings split between 7.1 and 7.7 (gave the range, a null difference and per-reading differences in `readings`). **Format gap, settled** by the 7.5 onset convention (`documented_value` and the signed difference).
6. Batch 6, SYN-0063: no form for `documented_value` or `difference_note` when onset is 7.5 (used `{"undetermined": …}`; for the grade, a numeric range). **Format gap, settled** by the 7.5 onset convention (`documented_value`, `signed_difference_days` and `difference_note`).
7. Batch 1, the 7.4 "no ICANS" cases (the report gives no case ID): no `documented_value` form for no qualifying finding (used `{"undetermined": …}`). **Format gap, settled** by the no-qualifying-finding convention.
8. Batch 2, SYN-0016: the same (§7.3 and §7.9(c) give no grade value; used `{"undetermined": …}`). **Format gap, settled** by the no-qualifying-finding convention.
9. Batch 4, SYN-0048: the same (used `{"grade": 0}` and "none found"). **Format gap, settled** by the no-qualifying-finding convention.
10. Batches 2 to 6 (no case IDs given): the format does not cover an unchanged field in a multi-version record `record_history` (all used `a` false, the rest null, with an explanation). **Format gap, settled** by the unchanged-field convention.
11. Batch 1, SYN-0001: out-of-scope evidence when no note states the trigger (age is only in `case.json`); cited `case.json` plus a corroborating note quote. **Format gap, settled** by the out-of-scope trigger evidence convention.
12. Batch 5, SYN-0049: the trigger is a record value, not a document; put the record field in `source` plus one context quote. **Format gap, settled** by the out-of-scope trigger evidence convention.
13. Batch 6 (format note): `docs/answer-format.md` is the dev-v1 reference README, with no spec for independent answers; `derivation` was put inside each field object and `ambiguity_notes` at top level, and earlier batches may have placed `derivation` differently (60 files top-level, 12 inside the fields). **Format gap, settled** by the `derivation` convention (inside each field object; not scored).

### Rule gaps

14. Batch 1, SYN-0011: whether "ICE not done, patient off the unit for CT" counts as a documented not-assessable period (§7 intro, A7; the example there is sedation or intubation). **Rule gap.**
15. Batch 3, SYN-0030: the same for "No ICE possible: patient away from the ward" (no category changed). **Rule gap.**
16. Batch 1, SYN-0009: §6.4 "about the same time" has no stated window (treated 30 minutes as conflicting). **Rule gap.**
17. Batch 3, SYN-0029: §7.5 covers only findings no clinician attributes; whether an explicit attribution can itself be read as ambiguous (treated as settled). **Rule gap.**
18. Batch 4, SYN-0047: whether a general line such as "A: ICANS post CAR-T" attributes a specific finding (treated as not attributing, per A9; if it did, the grade would be 7.7). **Rule gap** (A9).
19. Batch 6, SYN-0063: A30 and A35 do not say whether treatment before the finding removes the competing cause (ICE taken after dextrose, recheck glucose later); treated the cause as present, giving 7.5. **Rule gap.**
20. Batch 6, SYN-0069: A10 has no criterion for when a documented language barrier invalidates an ICE (used 7.5). **Rule gap** (A10).
21. Batch 1, SYN-0004, SYN-0009: whether an excluded symptom such as headache blocks 7.7 under §7.9(b) (read §7.10 and A21 as saying no). **Rule gap.**
22. Batch 4, SYN-0038: whether an ungradeable symptom with no ICE total blocks 7.7 (A21 leaves it open; followed v0.4, no). **Rule gap** (A21).
23. Batch 5, SYN-0054: the A35 competing-cause list does not mention subdural or other intracranial hemorrhage (treated as not competing). **Rule gap** (A35).
24. Batch 2, SYN-0024: whether "awakens spontaneously, not drowsy" plus ICE 10/10 is a formal Grade 0 assessment (only implied by A3 and §3.3; treated as one). **Rule gap.**
25. Batch 5, SYN-0055: whether "awakens spontaneously" with drowsiness and ICE 10/10 is a gradeable qualifying finding for onset (applied A3 literally). **Rule gap** (A3).
26. Batch 3, SYN-0034: whether a changed date in copied-forward text shows a real new observation after a documented resolution (A31; the category is the same either way). **Rule gap** (A31).
27. Batch 3, SYN-0027: whether a later record version made after the documents existed counts as "revision without new documentation" in §7.6(c) (applied (c) literally). **Rule gap.**
28. Batch 5 (the report gives no case ID): whether a document must support the changed value on its own or a later general summary is enough for §7.6(c) (treated any supporting version as eligible; none passed the date test). **Rule gap.**
29. Batch 5, SYN-0060: §7.5 and A26 do not say whether a relative-time range that contains an earlier formal Grade 0 on the record date is two readings (7.5) or one range (7.7) (used 7.7). **Rule gap** (A26).
30. Batch 6, SYN-0068: A5 says documented full resolution then recurrence is flagged, not split; the record's 07-19 may be a deliberate second-episode onset, but the rules do not allow splitting. **Rule gap** (A5).

### Run notes that are not unclear rules

Batch 6's first subagent hit a rate limit and wrote nothing; a fresh one ran. Batch 3's subagent saw the header lines of `answers/SYN-0001.json` by mistake and says it did not use them.
