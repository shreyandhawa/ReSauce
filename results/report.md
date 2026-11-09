# ReSauce evaluation report

**Reference answers: intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); not clinician-verified.** Results on synthetic data are not clinical validation.

**Disclosure:** The held-out split is in-repo and not sealed: it has the same writer as the dev cases and sits in the same repository (evaluation-spec §1). It was not opened during pipeline work, but it is not an independent test.

The splits are reported separately and never pooled. Scoring follows docs/evaluation-spec.md §3.

## Split: dev

- **ReSauce:** 20 cases; 19 in scope and 1 out of scope by the reference; 0 without a usable reference; **0 with an error**.
- **Baseline A:** 20 cases; 19 in scope and 1 out of scope by the reference; 0 without a usable reference; **0 with an error**.
- **Baseline B:** 20 cases; 19 in scope and 1 out of scope by the reference; 0 without a usable reference; **0 with an error**.

Counts are fields (each in-scope case has two: onset and maximum grade). Rates show value (numerator/denominator).

| Method | Field | Positive | Negative | Review | Detections | Misses | False alerts | Alerts on review fields | "review: …" results | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ReSauce | onset | 3 | 16 | 0 | 3 | 0 | 0 | 0 | 0 | 1.00 (3/3) | 1.00 (3/3) | 1.00 (6/6) |
| ReSauce | max_grade | 7 | 10 | 2 | 7 | 0 | 0 | 0 | 0 | 1.00 (7/7) | 1.00 (7/7) | 1.00 (14/14) |
| ReSauce | combined | 10 | 26 | 2 | 10 | 0 | 0 | 0 | 0 | 1.00 (10/10) | 1.00 (10/10) | 1.00 (20/20) |
| Baseline A | onset | 3 | 16 | 0 | 2 | 1 | 0 | 0 | 0 | 1.00 (2/2) | 0.67 (2/3) | 0.80 (4/5) |
| Baseline A | max_grade | 7 | 10 | 2 | 7 | 0 | 1 | 1 | 0 | 0.88 (7/8) | 1.00 (7/7) | 0.93 (14/15) |
| Baseline A | combined | 10 | 26 | 2 | 9 | 1 | 1 | 1 | 0 | 0.90 (9/10) | 0.90 (9/10) | 0.90 (18/20) |
| Baseline B | onset | 3 | 16 | 0 | 3 | 0 | 0 | 0 | 0 | 1.00 (3/3) | 1.00 (3/3) | 1.00 (6/6) |
| Baseline B | max_grade | 7 | 10 | 2 | 7 | 0 | 0 | 0 | 0 | 1.00 (7/7) | 1.00 (7/7) | 1.00 (14/14) |
| Baseline B | combined | 10 | 26 | 2 | 10 | 0 | 0 | 0 | 0 | 1.00 (10/10) | 1.00 (10/10) | 1.00 (20/20) |

Precision = detections ÷ (detections + false alerts). Recall = detections ÷ positive fields. F1 = 2PR/(P+R), written with counts as 2·detections ÷ (2·detections + false alerts + misses); it is 0 when there are no detections but precision and recall are both defined, and undefined when either is undefined. A detection is any alert on a positive field (the exact category is not needed). Alerts on review fields and "review: …" results are kept out of precision and recall. A case where a method raised an error counts its positive fields as misses.

**Misses, by what the method gave instead (combined fields)**

| Method | Misses | With a review flag (7.4/7.5) | With a "review: …" result | From an error | Flagged out of scope | With no alert |
|---|---|---|---|---|---|---|
| ReSauce | 0 | 0 | 0 | 0 | 0 | 0 |
| Baseline A | 1 | 0 | 0 | 0 | 0 | 1 |
| Baseline B | 0 | 0 | 0 | 0 | 0 | 0 |

**Exact-category agreement** (the method's category equals the reference category)

| Method | Field | All in-scope fields | Positive fields only |
|---|---|---|---|
| ReSauce | onset | 1.00 (19/19) | 1.00 (3/3) |
| ReSauce | max_grade | 1.00 (19/19) | 1.00 (7/7) |
| ReSauce | combined | 1.00 (38/38) | 1.00 (10/10) |
| Baseline A | onset | 0.95 (18/19) | 0.67 (2/3) |
| Baseline A | max_grade | 0.79 (15/19) | 1.00 (7/7) |
| Baseline A | combined | 0.87 (33/38) | 0.90 (9/10) |
| Baseline B | onset | 1.00 (19/19) | 1.00 (3/3) |
| Baseline B | max_grade | 1.00 (19/19) | 1.00 (7/7) |
| Baseline B | combined | 1.00 (38/38) | 1.00 (10/10) |

**Review flags by reference category** (ReSauce, both fields). Review flags are never counted as detections or false alerts.

| Reference category | Fields | Flagged 7.4 | Flagged 7.5 |
|---|---|---|---|
| 7.1 | 3 | 0 | 0 |
| 7.2 | 3 | 0 | 0 |
| 7.3 | 4 | 0 | 0 |
| 7.4 | 1 | 1 | 0 |
| 7.5 | 1 | 0 | 1 |
| 7.6 | 1 | 0 | 0 |
| 7.7 | 25 | 0 | 0 |
| 7.8 | 0 | 0 | 0 |

**Review flags by reference category** (Baseline B, both fields). Review flags are never counted as detections or false alerts.

| Reference category | Fields | Flagged 7.4 | Flagged 7.5 |
|---|---|---|---|
| 7.1 | 3 | 0 | 0 |
| 7.2 | 3 | 0 | 0 |
| 7.3 | 4 | 0 | 0 |
| 7.4 | 1 | 1 | 0 |
| 7.5 | 1 | 0 | 1 |
| 7.6 | 1 | 0 | 0 |
| 7.7 | 25 | 0 | 0 |
| 7.8 | 0 | 0 | 0 |

Baseline A: n/a (method cannot produce review flags).

**Out of scope (ReSauce and Baseline B)**

- ReSauce: Reference out-of-scope cases: 1; flagged out of scope: 1 (reason matches the reference: 1; a different reason: 0); not flagged: 0; errors: 0.
- ReSauce: In-scope cases wrongly flagged out of scope: 0 (their positive fields count as misses).
- Baseline B: Reference out-of-scope cases: 1; flagged out of scope: 1 (reason matches the reference: 1; a different reason: 0); not flagged: 0; errors: 0.
- Baseline B: In-scope cases wrongly flagged out of scope: 0 (their positive fields count as misses).
- Baseline A produces no out-of-scope flags, so no out-of-scope score is reported for it.

**Evidence-quote validity** (references that pass `check_evidence_ref`, over every evidence reference in the method's outputs)

- ReSauce: 1.00 (137/137)
- Baseline A: 1.00 (68/68)
- Baseline B: 1.00 (156/156)

**Runtime** (seconds, summed over cases): extraction 0.177 (shared by ReSauce and Baseline A), ReSauce rules engine 0.005, Baseline A 0.001. Per method including extraction: ReSauce 0.182, Baseline A 0.178. Whole split 0.229 including loading and evidence checks.

**Baseline B model requests:** 317.4 seconds, summed over cases (each streamed request, timed when the answers were collected; requests ran in parallel, so this is not the elapsed time). The measured tokens would cost $1.19 on the API at listed prices; the run used the user's Claude plan and was not billed per token.

## Split: held-out (in-repo, not sealed)

**Seen: the pipeline changed after the first held-out run (commit 4ff6c5f).**

- **ReSauce:** 52 cases; 49 in scope and 3 out of scope by the reference; 0 without a usable reference; **0 with an error**.
- **Baseline A:** 52 cases; 49 in scope and 3 out of scope by the reference; 0 without a usable reference; **0 with an error**.
- **Baseline B:** 52 cases; 49 in scope and 3 out of scope by the reference; 0 without a usable reference; **0 with an error**.

Counts are fields (each in-scope case has two: onset and maximum grade). Rates show value (numerator/denominator).

| Method | Field | Positive | Negative | Review | Detections | Misses | False alerts | Alerts on review fields | "review: …" results | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ReSauce | onset | 7 | 31 | 11 | 6 | 1 | 1 | 0 | 4 | 0.86 (6/7) | 0.86 (6/7) | 0.86 (12/14) |
| ReSauce | max_grade | 13 | 29 | 7 | 10 | 3 | 2 | 1 | 1 | 0.83 (10/12) | 0.77 (10/13) | 0.80 (20/25) |
| ReSauce | combined | 20 | 60 | 18 | 16 | 4 | 3 | 1 | 5 | 0.84 (16/19) | 0.80 (16/20) | 0.82 (32/39) |
| Baseline A | onset | 7 | 31 | 11 | 5 | 2 | 6 | 8 | 0 | 0.45 (5/11) | 0.71 (5/7) | 0.56 (10/18) |
| Baseline A | max_grade | 13 | 29 | 7 | 9 | 4 | 3 | 4 | 0 | 0.75 (9/12) | 0.69 (9/13) | 0.72 (18/25) |
| Baseline A | combined | 20 | 60 | 18 | 14 | 6 | 9 | 12 | 0 | 0.61 (14/23) | 0.70 (14/20) | 0.65 (28/43) |
| Baseline B | onset | 7 | 31 | 11 | 7 | 0 | 0 | 0 | 0 | 1.00 (7/7) | 1.00 (7/7) | 1.00 (14/14) |
| Baseline B | max_grade | 13 | 29 | 7 | 13 | 0 | 0 | 0 | 0 | 1.00 (13/13) | 1.00 (13/13) | 1.00 (26/26) |
| Baseline B | combined | 20 | 60 | 18 | 20 | 0 | 0 | 0 | 0 | 1.00 (20/20) | 1.00 (20/20) | 1.00 (40/40) |

Precision = detections ÷ (detections + false alerts). Recall = detections ÷ positive fields. F1 = 2PR/(P+R), written with counts as 2·detections ÷ (2·detections + false alerts + misses); it is 0 when there are no detections but precision and recall are both defined, and undefined when either is undefined. A detection is any alert on a positive field (the exact category is not needed). Alerts on review fields and "review: …" results are kept out of precision and recall. A case where a method raised an error counts its positive fields as misses.

**Misses, by what the method gave instead (combined fields)**

| Method | Misses | With a review flag (7.4/7.5) | With a "review: …" result | From an error | Flagged out of scope | With no alert |
|---|---|---|---|---|---|---|
| ReSauce | 4 | 2 | 2 | 0 | 0 | 0 |
| Baseline A | 6 | 0 | 0 | 0 | 0 | 6 |
| Baseline B | 0 | 0 | 0 | 0 | 0 | 0 |

**Exact-category agreement** (the method's category equals the reference category)

| Method | Field | All in-scope fields | Positive fields only |
|---|---|---|---|
| ReSauce | onset | 0.84 (41/49) | 0.86 (6/7) |
| ReSauce | max_grade | 0.88 (43/49) | 0.77 (10/13) |
| ReSauce | combined | 0.86 (84/98) | 0.80 (16/20) |
| Baseline A | onset | 0.61 (30/49) | 0.71 (5/7) |
| Baseline A | max_grade | 0.69 (34/49) | 0.69 (9/13) |
| Baseline A | combined | 0.65 (64/98) | 0.70 (14/20) |
| Baseline B | onset | 1.00 (49/49) | 1.00 (7/7) |
| Baseline B | max_grade | 1.00 (49/49) | 1.00 (13/13) |
| Baseline B | combined | 1.00 (98/98) | 1.00 (20/20) |

**Review flags by reference category** (ReSauce, both fields). Review flags are never counted as detections or false alerts.

| Reference category | Fields | Flagged 7.4 | Flagged 7.5 |
|---|---|---|---|
| 7.1 | 6 | 0 | 0 |
| 7.2 | 7 | 1 | 0 |
| 7.3 | 5 | 0 | 1 |
| 7.4 | 11 | 11 | 0 |
| 7.5 | 7 | 0 | 6 |
| 7.6 | 3 | 1 | 0 |
| 7.7 | 57 | 1 | 1 |
| 7.8 | 2 | 0 | 0 |

**Review flags by reference category** (Baseline B, both fields). Review flags are never counted as detections or false alerts.

| Reference category | Fields | Flagged 7.4 | Flagged 7.5 |
|---|---|---|---|
| 7.1 | 6 | 0 | 0 |
| 7.2 | 7 | 0 | 0 |
| 7.3 | 5 | 0 | 0 |
| 7.4 | 11 | 11 | 0 |
| 7.5 | 7 | 0 | 7 |
| 7.6 | 3 | 0 | 0 |
| 7.7 | 57 | 0 | 0 |
| 7.8 | 2 | 0 | 0 |

Baseline A: n/a (method cannot produce review flags).

**Out of scope (ReSauce and Baseline B)**

- ReSauce: Reference out-of-scope cases: 3; flagged out of scope: 3 (reason matches the reference: 3; a different reason: 0); not flagged: 0; errors: 0.
- ReSauce: In-scope cases wrongly flagged out of scope: 0 (their positive fields count as misses).
- Baseline B: Reference out-of-scope cases: 3; flagged out of scope: 3 (reason matches the reference: 3; a different reason: 0); not flagged: 0; errors: 0.
- Baseline B: In-scope cases wrongly flagged out of scope: 0 (their positive fields count as misses).
- Baseline A produces no out-of-scope flags, so no out-of-scope score is reported for it.

**Evidence-quote validity** (references that pass `check_evidence_ref`, over every evidence reference in the method's outputs)

- ReSauce: 1.00 (395/395)
- Baseline A: 1.00 (147/147)
- Baseline B: 1.00 (330/331)

**Runtime** (seconds, summed over cases): extraction 0.197 (shared by ReSauce and Baseline A), ReSauce rules engine 0.009, Baseline A 0.001. Per method including extraction: ReSauce 0.206, Baseline A 0.198. Whole split 0.294 including loading and evidence checks.

**Baseline B model requests:** 810.4 seconds, summed over cases (each streamed request, timed when the answers were collected; requests ran in parallel, so this is not the elapsed time). The measured tokens would cost $2.63 on the API at listed prices; the run used the user's Claude plan and was not billed per token.

## Run metadata

- Code commit: 4fa9174fe72d47dd6941d4cff550336124ebc0a1 (uncommitted changes in code or data: no)
- Dataset: SYN-DS-DEV-V1 version 1.0.0
- Reference-answer commit: 5059a9b0980cf474f31086be913a371322047e1f
- Date: 2026-11-09T08:25:36-06:00
- Python 3.14.3 on macOS-26.6.2-arm64-arm-64bit-Mach-O
- Splits in this report: dev, held_out
- Baseline B (LLM): claude-opus-5-5, effort high, adaptive thinking, no fallback model, through Claude Code print mode on the user's Claude plan; dataset SYN-DS-DEV-V1 version 1.0.0; answers collected from 2026-11-09T08:20:02-06:00 at code commit 4fa9174fe72d47dd6941d4cff550336124ebc0a1 with Claude Code 2.1.319 (Claude Code) in 1 session(s); instructions SHA-256 0cda59baefac995b4e20a8dde5550077ed76c7f0f789f8c4661cf246f64e1596; stored in results/baseline_b/ (evaluation-spec §5)

## Limitations

- All data is synthetic. Results are not clinical validation.
- Cases and intended answers were written by Claude sessions; the answers are not independently verified and not clinician-verified.
- Rules that are not yet implemented return a "review: …" result, never a guess.
- The user does not read the development cases; they are checked only by tools.check_dev and the reviewer's sampled reviews (evaluation-spec §6).
- The extractor's phrase lists were built from the 20 dev cases and clinical-methods.md only. A word of 6 or more letters one letter away from a list word is read as an uncertain "spelling variant" and listed for review; swapped letters and shorter words are missed without a warning.
- Baseline B is the same model family (Claude) that wrote the cases and the reference answers. Its agreement with the reference may come partly from shared habits of reading the same rules text, not only from being right (evaluation-spec §6).
- Baseline B's answers are not deterministic and come from one run; a second run could give different numbers.
- The held-out split is new to Baseline B, but it is not sealed.
