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

**Not produced.** `reference/dev-v1/independent-run-notes.md` was not found when this report was generated, so no list of "unclear rules" could be made and none was invented. Each one is to be marked "format gap" (answer-format) or "rule gap" (clinical-methods) once the notes file is available.
