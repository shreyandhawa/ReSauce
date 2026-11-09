# ReSauce evaluation specification

- **Status:** v0.2, draft (2026-11-09). v0.1 (2026-11-08, Milestone 3 session 3) was written **before** any pipeline result existed, so the definitions could not be chosen to suit the results. v0.2 specifies Baseline B (§5) before any Baseline B result exists.
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

Specified on 2026-11-09, **before any Baseline B call was made**, and committed before the run. Implemented in `src/resauce/baseline_b.py`.

**Question it answers:** given the same written rules and the same case files, can a general AI model do this check as well as the rule-based pipeline?

- **Model:** Claude Opus 5.5 (`claude-opus-5-5`), chosen by the user.
- **Route** (user's choice, 2026-11-09, made before any case was sent): Claude Code's print mode on the user's own Claude plan, one request per case. The command is:

  `claude -p --model claude-opus-5-5 --effort high --system-prompt <instructions> --tools "" --json-schema <schema> --output-format json --no-session-persistence --strict-mcp-config --setting-sources project`

  The case message goes to its standard input. Each request runs from a new empty folder, so no project instructions or settings are loaded. `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are removed from its environment, so it can never use a billed key.
  - `--tools ""` switches off every tool, so **the model cannot open any file**, including the reference answers.
  - `--system-prompt` replaces Claude Code's own system prompt with the instructions below.
- **Settings:** adaptive thinking (always on for this model; it cannot be switched off), effort `high`. The model accepts no temperature setting, so its answers are **not deterministic**: a second run could differ. No fallback to another model. An answer that reports a different model is an error.
- **Not controlled on this route** (disclosed): the maximum answer length is Claude Code's default, and Claude Code adds some context of its own. Before the run, `python -m resauce.baseline_b check` sent one tiny request with no case data and asked the model to copy any extra context it received. Its output is stored in `results/baseline_b/check.json`; the account email in it was removed before committing. The check (2026-11-09, Claude Code 2.1.319) found four additions, none of them case-related:
  - a two-sentence preamble before the instructions ("You are a Claude agent, built on Anthropic's Claude Agent SDK." and a sentence on parallel tool calls);
  - a reminder holding the user's account email;
  - an environment block: the empty working folder's path, the operating system, the model's name and knowledge cutoff, and today's date (2026-11-09; the synthetic cases are dated in the 2030s);
  - the definition of Claude Code's StructuredOutput tool, through which the schema answer is returned.
- **How Claude Code returns the answer:** through that StructuredOutput tool, so the last stop reason is `tool_use`. A request counts as finished when Claude Code reports `terminal_reason` "completed". The check took 2 turns (the answer, then the tool result), used no other tool, had no permission denials and started no sub-agents.
- **Instructions (system prompt):** a short fixed task description, followed by `docs/clinical-methods.md` verbatim from "How to read this document" through §9 (assumptions). The changelog and §10 (references) are left out. These are the same rules the pipeline implements and the reference answers follow.
- **Input per case (user message):** the case files as JSON: case ID, age at infusion, infusion date (Day 0), the observation window, every research record version, and every version of every document with its metadata (status, note type, author role, documented time, amendment reason) and text. Nothing from `reference/`, `results/` or the pipeline's output is sent.
- **No examples and no tuning:** the instructions are written before any case is run and are not changed after any answer is seen. A rerun for a technical fault in ReSauce's own code (for example, a parsing bug) is disclosed with the results.
- **Output:** JSON constrained by a schema:
  - out-of-scope reason: "in scope" or one of the five A29 reasons ("age under 18", "CAPD assessment", "record Grade 5", "documented death", "developmental delay");
  - for onset and for maximum grade: a §7 category allowed for that field (onset 7.1, 7.4–7.8; grade 7.2–7.8), the documented value, an explanation, and evidence quotes (document ID, version, exact quote).
- **Turning the answer into a method output:**
  - Each quote is located by exact search in the named document version, and its first occurrence gives the offsets. A quote that is not found exactly keeps offsets −1 and fails the evidence-quote check (§3).
  - A reason other than "in scope" makes both fields "out of scope (reason)", as for ReSauce.
- **Errors:** a declined request, a cut-off or unfinished answer, an answer from another model, or an answer that is not valid JSON is stored and counts as an error (§3). So does a stored answer whose fingerprints do not match the run's instructions or the current case files. If Claude Code returns no answer at all (for example not logged in, a usage limit or a timeout), nothing is stored and the run stops; the same command continues it later.
- **Scoring:** exactly §3. Baseline B can give review flags (7.4, 7.5) and out-of-scope flags, so both are scored as for ReSauce. Baseline B enters a report **only when every case of the dataset has a stored answer from the same run**. A partial run is left out of the report, never scored as if complete.
- **Run and storage:** one run on all 72 cases of `data/dev-v1` (dev and held-out).
  - Each answer is stored in `results/baseline_b/responses/<case_id>.json`. The record holds Claude Code's full output as returned, plus the model, settings, fingerprints of the instructions and of the case message, token usage and time. The instructions and schema are stored next to them.
  - `results/baseline_b/run.json` records the settings and command, the code commit and dataset version at collection time, the prices used for cost, and for each session the Claude Code version and the number of parallel requests.
  - Requests run in parallel (4 by default). The first case runs alone, so a setup fault costs only one request.
  - A rerun for a technical fault in ReSauce's own code is recorded in `run.json` under "disclosures" and printed with the results.
  - Scoring reads only the stored answers and never calls the model.
- **Cost:** the run uses the user's Claude plan and is not billed per token. For comparison, the measured token usage × Anthropic's listed API prices is reported with the results, labelled as such.

## 5a. Changelog

- **v0.2 (2026-11-09):** §5 Baseline B specified before its run; Baseline B limitations added to §6. Before any case was sent, the route was changed from the Messages API to Claude Code's print mode on the user's plan (the user's choice), with the differences listed under "Not controlled on this route".

## 6. Limitations (reported with every result)

- All data is synthetic. Results are not clinical validation.
- Cases and intended answers were written by Claude sessions. The answers are not independently verified and not clinician-verified.
- **The user does not read the development cases** (dataset plan, v0.3.2 changelog entry). They are checked only by `tools.check_dev` and by the reviewer's sampled reviews.
- The held-out split is not sealed (same writer, same repository).
- Rules that are not yet implemented return a review result, never a guess.
- The extractor's phrase lists were built from the 20 dev cases and `clinical-methods.md` only. Since session 4b, a word of 6 or more letters that is one letter away from a list word is read as an uncertain "spelling variant" and listed for review. Swapped letters (for example "seziure") are two changes, so they are still missed without a warning, as are shorter words.
- **Baseline B is the same model family that wrote the cases and the reference answers** (Claude). Its agreement with the reference may come partly from shared habits of reading the same rules text, not only from being right.
- Baseline B's answers are not deterministic and come from one run. A second run could give different numbers.
- The held-out split is new to Baseline B, but it is not sealed.
