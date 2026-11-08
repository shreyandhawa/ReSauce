"""Evaluation runner: score ReSauce and Baseline A on each split.

Implements docs/evaluation-spec.md §1 (splits), §2 (reference answers),
§3 (scoring) and §6 (limitations). Run:

    python -m resauce.evaluate [--splits dev held_out] [--data DIR]
                               [--reference DIR] [--out DIR]
    python -m resauce.evaluate --split-name NAME --data DIR --reference DIR

With --split-name, every case folder in --data is scored as one split called
NAME (for example "locked"); splits.json is not read.

This is evaluation code, not pipeline code: it is the only module in
src/resauce that reads reference answers. The engine, the extractor and
Baseline A never import it, and never read anything in reference/.

The dev cases are listed in <reference>/splits.json. The held-out split is
every other case folder. Splits are scored and written separately and are
never pooled. Nothing per case is printed: only totals.

Scoring is done by pure functions on small dicts (see score_method), so it
can be tested without any files.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from resauce import baseline_a, engine
from resauce.extract import extract_case
from resauce.loader import check_evidence_ref, load_case
from resauce.models import EvidenceRef

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("onset", "max_grade")
CATEGORIES = tuple(f"7.{n}" for n in range(1, 9))
POSITIVE = ("7.1", "7.2", "7.3", "7.8")  # reference classes (spec §3)
NEGATIVE = ("7.6", "7.7")
REVIEW = ("7.4", "7.5")
ALERTS = POSITIVE  # a method's discrepancy alerts are the same four categories
REVIEW_FLAGS = REVIEW
SPLIT_NAMES = ("dev", "held_out")
METHODS = ("resauce", "baseline_a")
METHOD_TITLES = {"resauce": "ReSauce", "baseline_a": "Baseline A"}
ERROR_TEXT_LIMIT = 300

LABEL = ("intended answers, agreed by a blind re-derivation by a separate Claude session (same model family); "
         "not clinician-verified")
HELD_OUT_SEEN = "seen: the pipeline changed after the first held-out run (commit 4ff6c5f)"
HELD_OUT_DISCLOSURE = (
    "The held-out split is in-repo and not sealed: it has the same writer as the dev cases and sits in the "
    "same repository (evaluation-spec §1). It was not opened during pipeline work, but it is not an "
    "independent test."
)
LIMITATIONS = (
    "All data is synthetic. Results are not clinical validation.",
    "Cases and intended answers were written by Claude sessions; the answers are not independently "
    "verified and not clinician-verified.",
    "Baseline B (LLM) is deferred until an API key is available, so it has no result here.",
    "Rules that are not yet implemented return a \"review: …\" result, never a guess.",
    "The user does not read the development cases; they are checked only by tools.check_dev and the "
    "reviewer's sampled reviews (evaluation-spec §6).",
    "The extractor's phrase lists were built from the 20 dev cases and clinical-methods.md only. A word of 6 "
    "or more letters one letter away from a list word is read as an uncertain \"spelling variant\" and listed "
    "for review; swapped letters and shorter words are missed without a warning.",
)


# ---------------------------------------------------------------------------
# Classes (evaluation-spec §3)
# ---------------------------------------------------------------------------


_CODE = re.compile(r"^\s*(7\.[1-9])(?=$|[\s(])")


def reference_code(category: str) -> str | None:
    """Leading code of a reference category ("7.5 (attribution)" -> "7.5"), or None if not 7.1 to 7.9."""
    match = _CODE.match(category)
    return match.group(1) if match else None


def reference_class(category: str) -> str | None:
    """"positive", "negative", "review", or None for a category outside 7.1 to 7.8."""
    category = reference_code(category) or category
    if category in POSITIVE:
        return "positive"
    if category in NEGATIVE:
        return "negative"
    if category in REVIEW:
        return "review"
    return None


def method_class(category: str) -> str:
    """How a method's category counts: alert, review_flag, review_result, out_of_scope, error or no_alert."""
    if category == "error":
        return "error"
    if category in ALERTS:
        return "alert"
    if category in REVIEW_FLAGS:
        return "review_flag"
    if category.startswith("review:"):
        return "review_result"
    if category.startswith("out of scope"):
        return "out_of_scope"
    return "no_alert"


# ---------------------------------------------------------------------------
# Scoring: pure functions on small dicts
#
# A reference is {"out_of_scope": reason or None, "fields": {"onset": cat, "max_grade": cat}}.
# A method output is the engine's or Baseline A's to_dict() (only
# "out_of_scope" and fields[name]["category"] are read).
# ---------------------------------------------------------------------------


def _blank_counts() -> dict:
    counts = {key: 0 for key in (
        "fields", "positive", "negative", "review", "unclassified",
        "detections", "misses", "false_alerts", "alerts_on_review_fields", "review_results",
        "misses_with_review_flag", "misses_with_review_result", "misses_from_errors",
        "misses_from_out_of_scope", "misses_with_no_alert",
        "agree_all", "agree_positive",
    )}
    for category in CATEGORIES:
        counts[f"ref_{category}"] = 0
        for flag in REVIEW_FLAGS:
            counts[f"ref_{category}_flagged_{flag}"] = 0
    return counts


def _score_field(counts: dict, reference_category: str, method_category: str) -> None:
    reference_category = reference_code(reference_category) or reference_category
    ref, got = reference_class(reference_category), method_class(method_category)
    counts["fields"] += 1
    agrees = method_category == reference_category
    counts["agree_all"] += agrees
    if reference_category in CATEGORIES:
        counts[f"ref_{reference_category}"] += 1
        if got == "review_flag":
            counts[f"ref_{reference_category}_flagged_{method_category}"] += 1
    if got == "review_result":
        counts["review_results"] += 1
    if ref is None:
        counts["unclassified"] += 1
    elif ref == "positive":
        counts["positive"] += 1
        counts["agree_positive"] += agrees
        if got == "alert":
            counts["detections"] += 1
        else:
            counts["misses"] += 1
            counts[{"review_flag": "misses_with_review_flag", "review_result": "misses_with_review_result",
                    "error": "misses_from_errors", "out_of_scope": "misses_from_out_of_scope"}
                   .get(got, "misses_with_no_alert")] += 1
    elif ref == "negative":
        counts["negative"] += 1
        counts["false_alerts"] += got == "alert"
    else:
        counts["review"] += 1
        counts["alerts_on_review_fields"] += got == "alert"


def ratio(numerator: int, denominator: int) -> dict:
    """A rate with its raw counts. value is None when the denominator is 0."""
    return {"n": numerator, "d": denominator, "value": numerator / denominator if denominator else None}


def derive(counts: dict) -> dict:
    """Precision, recall, F1 and exact agreement from raw counts (spec §3)."""
    det, fa, miss = counts["detections"], counts["false_alerts"], counts["misses"]
    precision = ratio(det, det + fa)
    recall = ratio(det, counts["positive"])
    defined = precision["value"] is not None and recall["value"] is not None
    # 2PR/(P+R) written with counts: 2*det / (2*det + false alerts + misses).
    f1 = ratio(2 * det, 2 * det + fa + miss) if defined else ratio(0, 0)
    return {
        "precision": precision, "recall": recall, "f1": f1,
        "exact_agreement_all_fields": ratio(counts["agree_all"], counts["fields"]),
        "exact_agreement_positive_fields": ratio(counts["agree_positive"], counts["positive"]),
    }


def _same_reason(a: str, b: str) -> bool:
    return " ".join(a.lower().split()) == " ".join(b.lower().split())


def score_method(cases: list, *, scores_out_of_scope: bool) -> dict:
    """Score one method on one split.

    cases: (case_id, reference or None, output or None) tuples.
    A case with no usable reference is counted and left out. A case where the
    method raised an error (output None) counts its positive fields as misses.
    Reference out-of-scope cases never enter the discrepancy measures; they
    are scored only for a method with scores_out_of_scope.
    """
    per_field = {name: _blank_counts() for name in FIELDS}
    oos = {"reference_cases": 0, "flagged": 0, "reason_matches": 0, "flagged_other_reason": 0,
           "not_flagged": 0, "errors": 0, "in_scope_wrongly_flagged": 0, "wrongly_flagged_ids": []}
    summary = {"cases": len(cases), "in_scope": 0, "out_of_scope": 0, "without_reference": 0,
               "errors": 0, "error_ids": []}
    for case_id, reference, output in cases:
        if output is None:
            summary["errors"] += 1
            summary["error_ids"].append(case_id)
        if reference is None:
            summary["without_reference"] += 1
            continue
        flagged = output.get("out_of_scope") if output else None
        if reference["out_of_scope"] is not None:
            summary["out_of_scope"] += 1
            if scores_out_of_scope:
                oos["reference_cases"] += 1
                if output is None:
                    oos["errors"] += 1
                elif not flagged:
                    oos["not_flagged"] += 1
                else:
                    oos["flagged"] += 1
                    if _same_reason(flagged["reason"], reference["out_of_scope"]):
                        oos["reason_matches"] += 1
                    else:
                        oos["flagged_other_reason"] += 1
            continue
        summary["in_scope"] += 1
        if flagged and scores_out_of_scope:
            oos["in_scope_wrongly_flagged"] += 1
            oos["wrongly_flagged_ids"].append(case_id)
        for name in FIELDS:
            got = output["fields"][name]["category"] if output else "error"
            _score_field(per_field[name], reference["fields"][name], got)
    combined = _blank_counts()
    for counts in per_field.values():
        for key, value in counts.items():
            combined[key] += value
    return {
        "summary": summary,
        "fields": {name: {"counts": c, **derive(c)}
                   for name, c in (*per_field.items(), ("combined", combined))},
        "out_of_scope": oos if scores_out_of_scope else None,
    }


# ---------------------------------------------------------------------------
# Evidence validity
# ---------------------------------------------------------------------------


def _evidence_lists(node):
    """Every list stored under an "evidence" key, anywhere in a method output."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "evidence" and isinstance(value, list):
                yield value
            else:
                yield from _evidence_lists(value)
    elif isinstance(node, list):
        for item in node:
            yield from _evidence_lists(item)


def evidence_validity(case, output: dict) -> tuple[int, int]:
    """(valid, total) evidence references of an output, checked with check_evidence_ref."""
    valid = total = 0
    for evidence in _evidence_lists(output):
        for item in evidence:
            total += 1
            try:
                check_evidence_ref(case, EvidenceRef(item["document_id"], item["version"],
                                                     item["start"], item["end"], item["quote"]))
                valid += 1
            except Exception:
                pass
    return valid, total


# ---------------------------------------------------------------------------
# Running the methods
# ---------------------------------------------------------------------------


def _error_text(exc: Exception) -> str:
    text = " ".join(f"{type(exc).__name__}: {exc}".split())
    return text if len(text) <= ERROR_TEXT_LIMIT else text[:ERROR_TEXT_LIMIT] + "…"


def read_reference(reference_dir: Path, case_id: str) -> dict:
    """The parts of an intended answer that scoring needs."""
    answer = json.loads((reference_dir / "intended" / f"{case_id}.json").read_text(encoding="utf-8"))
    oos = answer["out_of_scope"]
    fields = {name: answer["fields"][name]["category"] for name in FIELDS}
    for name, category in fields.items():
        if not oos and reference_code(category) is None:  # never dropped silently: listed in reference_errors
            raise ValueError(f"reference category for {name} is not 7.1 to 7.9: {category!r}")
    return {"out_of_scope": oos["reason"] if oos else None, "fields": fields}


def run_case(case_id: str, data_dir: Path, reference_dir: Path) -> dict:
    """Run both methods on one case. Failures become error entries; this never raises."""
    record = {"case_id": case_id, "reference": None, "reference_error": None,
              "resauce": None, "baseline_a": None,
              "runtime_seconds": {"extract": 0.0, "resauce": 0.0, "baseline_a": 0.0}}
    try:
        record["reference"] = read_reference(reference_dir, case_id)
    except Exception as exc:
        record["reference_error"] = _error_text(exc)

    folder = data_dir / "cases" / case_id
    try:
        case = load_case(folder)
        window = engine.load_window(folder)
    except Exception as exc:
        record["resauce"], record["baseline_a"] = ({"error": "load: " + _error_text(exc)} for _ in METHODS)
        return record
    started = time.perf_counter()
    try:
        observations = extract_case(case)
    except Exception as exc:
        record["resauce"], record["baseline_a"] = ({"error": "extract: " + _error_text(exc)} for _ in METHODS)
        return record
    finally:
        record["runtime_seconds"]["extract"] = time.perf_counter() - started

    runs = {"resauce": lambda: engine.evaluate_case(case, observations, window).to_dict(),
            "baseline_a": lambda: baseline_a.evaluate_case(case, observations).to_dict()}
    for method, run in runs.items():
        started = time.perf_counter()
        try:
            output = run()
            record[method] = {"output": output, "evidence_valid": evidence_validity(case, output)}
        except Exception as exc:
            record[method] = {"error": _error_text(exc)}
        record["runtime_seconds"][method] = time.perf_counter() - started
    return record


def read_splits(data_dir: Path, reference_dir: Path) -> dict[str, list[str]]:
    """Case IDs per split: dev from splits.json, held-out = every other case folder."""
    listed = json.loads((reference_dir / "splits.json").read_text(encoding="utf-8"))["dev"]
    folders = sorted(p.name for p in (data_dir / "cases").iterdir() if p.is_dir())
    missing = [c for c in listed if c not in folders]
    repeated = sorted({c for c in listed if listed.count(c) > 1})
    if missing or repeated:
        raise SystemExit(f"splits.json does not match the case folders (missing: {missing}; repeated: {repeated})")
    return {"dev": sorted(listed), "held_out": [c for c in folders if c not in listed]}


def read_folder_split(data_dir: Path) -> list[str]:
    """Every case folder in <data>/cases, sorted: one named split (--split-name)."""
    return sorted(p.name for p in (data_dir / "cases").iterdir() if p.is_dir())


def run_split(name: str, case_ids: list[str], data_dir: Path, reference_dir: Path) -> dict:
    started = time.perf_counter()
    records = [run_case(case_id, data_dir, reference_dir) for case_id in case_ids]
    metrics = {}
    for method in METHODS:
        scored = [(r["case_id"], r["reference"], r[method].get("output")) for r in records]
        result = score_method(scored, scores_out_of_scope=method == "resauce")
        valid = total = 0
        for r in records:
            v, t = r[method].get("evidence_valid", (0, 0))
            valid, total = valid + v, total + t
        result["evidence_validity"] = ratio(valid, total)
        result["errors"] = [{"case_id": r["case_id"], "error": r[method]["error"]}
                            for r in records if "error" in r[method]]
        metrics[method] = result
    runtime = {key: sum(r["runtime_seconds"][key] for r in records) for key in ("extract", *METHODS)}
    runtime["wall_clock"] = time.perf_counter() - started
    return {"split": name, "case_ids": case_ids, "cases": records, "metrics": metrics,
            "runtime_seconds": runtime,
            "reference_errors": [{"case_id": r["case_id"], "error": r["reference_error"]}
                                 for r in records if r["reference_error"]]}


# ---------------------------------------------------------------------------
# Run metadata and report
# ---------------------------------------------------------------------------


def _git(*args: str) -> str | None:
    """Output of a git command, or None if git is not available or the command failed."""
    try:
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return done.stdout.strip() if done.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def run_metadata(data_dir: Path, reference_dir: Path) -> dict:
    try:
        dataset = json.loads((data_dir / "dataset.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dataset = {}
    dirty = _git("status", "--porcelain", "--", "src", "tests", "data", "reference", "tools", "pyproject.toml")
    return {
        "code_commit": _git("rev-parse", "HEAD") or "unknown (git not available)",
        "uncommitted_changes_in_code_or_data": None if dirty is None else bool(dirty),
        "dataset_id": dataset.get("dataset_id"),
        "dataset_version": dataset.get("dataset_version"),
        "reference_answer_commit": _git("log", "-1", "--format=%H", "--", str(reference_dir / "intended"))
        or "unknown (git not available)",
        "reference_label": LABEL,
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }


def _fmt(r: dict) -> str:
    return "undefined (0/0)" if r["value"] is None else f"{r['value']:.2f} ({r['n']}/{r['d']})"


def _split_report(split: dict) -> list[str]:
    name, metrics = split["split"], split["metrics"]
    if name == "dev":
        title = "dev"
    elif name == "held_out":
        title = "held-out (in-repo, not sealed)"
    else:
        title = name
    lines = [f"## Split: {title}", ""]
    if name == "held_out":
        lines += [f"**{HELD_OUT_SEEN[0].upper()}{HELD_OUT_SEEN[1:]}.**", ""]
    for method in METHODS:
        s = metrics[method]["summary"]
        lines.append(f"- **{METHOD_TITLES[method]}:** {s['cases']} cases; {s['in_scope']} in scope and "
                     f"{s['out_of_scope']} out of scope by the reference; {s['without_reference']} without a "
                     f"usable reference; **{s['errors']} with an error**.")
    lines += ["", "Counts are fields (each in-scope case has two: onset and maximum grade). Rates show "
              "value (numerator/denominator).", "",
              "| Method | Field | Positive | Negative | Review | Detections | Misses | False alerts | "
              "Alerts on review fields | \"review: …\" results | Precision | Recall | F1 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for method in METHODS:
        for field_name in (*FIELDS, "combined"):
            f = metrics[method]["fields"][field_name]
            c = f["counts"]
            lines.append(f"| {METHOD_TITLES[method]} | {field_name} | {c['positive']} | {c['negative']} | "
                         f"{c['review']} | {c['detections']} | {c['misses']} | {c['false_alerts']} | "
                         f"{c['alerts_on_review_fields']} | {c['review_results']} | {_fmt(f['precision'])} | "
                         f"{_fmt(f['recall'])} | {_fmt(f['f1'])} |")
    lines += ["", "Precision = detections ÷ (detections + false alerts). Recall = detections ÷ positive fields. "
              "F1 = 2PR/(P+R), written with counts as 2·detections ÷ (2·detections + false alerts + misses); it is "
              "0 when there are no detections but precision and recall are both defined, and undefined when "
              "either is undefined. "
              "A detection is any alert on a positive field (the exact category is not needed). Alerts on "
              "review fields and \"review: …\" results are kept out of precision and recall. A case where a "
              "method raised an error counts its positive fields as misses.", "",
              "**Misses, by what the method gave instead (combined fields)**", "",
              "| Method | Misses | With a review flag (7.4/7.5) | With a \"review: …\" result | "
              "From an error | Flagged out of scope | With no alert |",
              "|---|---|---|---|---|---|---|"]
    for method in METHODS:
        c = metrics[method]["fields"]["combined"]["counts"]
        lines.append(f"| {METHOD_TITLES[method]} | {c['misses']} | {c['misses_with_review_flag']} | "
                     f"{c['misses_with_review_result']} | {c['misses_from_errors']} | "
                     f"{c['misses_from_out_of_scope']} | {c['misses_with_no_alert']} |")
    lines += ["", "**Exact-category agreement** (the method's category equals the reference category)", "",
              "| Method | Field | All in-scope fields | Positive fields only |", "|---|---|---|---|"]
    for method in METHODS:
        for field_name in (*FIELDS, "combined"):
            f = metrics[method]["fields"][field_name]
            lines.append(f"| {METHOD_TITLES[method]} | {field_name} | {_fmt(f['exact_agreement_all_fields'])} | "
                         f"{_fmt(f['exact_agreement_positive_fields'])} |")
    c = metrics["resauce"]["fields"]["combined"]["counts"]
    lines += ["", "**Review flags by reference category** (ReSauce, both fields). Review flags are never "
              "counted as detections or false alerts.", "",
              "| Reference category | Fields | Flagged 7.4 | Flagged 7.5 |", "|---|---|---|---|"]
    for category in CATEGORIES:
        lines.append(f"| {category} | {c[f'ref_{category}']} | {c[f'ref_{category}_flagged_7.4']} | "
                     f"{c[f'ref_{category}_flagged_7.5']} |")
    lines += ["", "Baseline A: n/a (method cannot produce review flags).", ""]
    oos = metrics["resauce"]["out_of_scope"]
    lines += ["**Out of scope (ReSauce only)**", "",
              f"- Reference out-of-scope cases: {oos['reference_cases']}; flagged out of scope: {oos['flagged']} "
              f"(reason matches the reference: {oos['reason_matches']}; a different reason: "
              f"{oos['flagged_other_reason']}); not flagged: {oos['not_flagged']}; errors: {oos['errors']}.",
              f"- In-scope cases wrongly flagged out of scope: {oos['in_scope_wrongly_flagged']} (their positive "
              "fields count as misses).",
              "- Baseline A produces no out-of-scope flags, so no out-of-scope score is reported for it.", "",
              "**Evidence-quote validity** (references that pass `check_evidence_ref`, over every evidence "
              "reference in the method's outputs)", ""]
    for method in METHODS:
        lines.append(f"- {METHOD_TITLES[method]}: {_fmt(metrics[method]['evidence_validity'])}")
    rt = split["runtime_seconds"]
    lines += ["", f"**Runtime** (seconds, summed over cases): extraction {rt['extract']:.3f} (shared by both "
              f"methods), ReSauce rules engine {rt['resauce']:.3f}, Baseline A {rt['baseline_a']:.3f}. "
              f"Per method including extraction: ReSauce {rt['extract'] + rt['resauce']:.3f}, "
              f"Baseline A {rt['extract'] + rt['baseline_a']:.3f}. Whole split {rt['wall_clock']:.3f} "
              "including loading and evidence checks.", ""]
    errors = [(METHOD_TITLES[m], e) for m in METHODS for e in metrics[m]["errors"]]
    if errors or split["reference_errors"]:
        lines += ["**Errors** (counted above; the run carried on)", ""]
        lines += [f"- {m}, {e['case_id']}: {e['error']}" for m, e in errors]
        lines += [f"- Reference answer, {e['case_id']}: {e['error']}" for e in split["reference_errors"]]
        lines.append("")
    return lines


def build_report(splits: list[dict], metadata: dict) -> str:
    lines = ["# ReSauce evaluation report", "",
             f"**Reference answers: {LABEL}.** Results on synthetic data are not clinical validation.", ""]
    if any(s["split"] == "held_out" for s in splits):
        lines += [f"**Disclosure:** {HELD_OUT_DISCLOSURE}", ""]
    lines += ["The splits are reported separately and never pooled. Scoring follows docs/evaluation-spec.md §3.",
             ""]
    for split in splits:
        lines += _split_report(split)
    changes = metadata["uncommitted_changes_in_code_or_data"]
    lines += ["## Run metadata", "",
              f"- Code commit: {metadata['code_commit']}"
              + ("" if changes is None else f" (uncommitted changes in code or data: {'yes' if changes else 'no'})"),
              f"- Dataset: {metadata['dataset_id']} version {metadata['dataset_version']}",
              f"- Reference-answer commit: {metadata['reference_answer_commit']}",
              f"- Date: {metadata['date']}",
              f"- Python {metadata['python_version']} on {metadata['platform']}",
              f"- Splits in this report: {', '.join(s['split'] for s in splits)}",
              "- Baseline B (LLM): not run (deferred, evaluation-spec §5)", "",
              "## Limitations", ""]
    lines += [f"- {text}" for text in LIMITATIONS]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m resauce.evaluate", description=__doc__.split("\n")[0])
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "dev-v1")
    parser.add_argument("--reference", type=Path, default=ROOT / "reference" / "dev-v1")
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    parser.add_argument("--splits", nargs="+", choices=SPLIT_NAMES, default=None)
    parser.add_argument("--split-name", help="score every case in --data as one split with this name")
    args = parser.parse_args(argv)
    if args.split_name and args.splits:
        parser.error("--split-name and --splits cannot be used together")
    if args.split_name and (args.split_name in SPLIT_NAMES or not re.fullmatch(r"[A-Za-z0-9_-]+", args.split_name)):
        parser.error("--split-name must be letters, digits, _ or -, and not 'dev' or 'held_out'")

    if args.split_name:
        ids = {args.split_name: read_folder_split(args.data)}
        names = [args.split_name]
    else:
        ids = read_splits(args.data, args.reference)
        names = [n for n in SPLIT_NAMES if n in (args.splits or SPLIT_NAMES)]
    metadata = run_metadata(args.data, args.reference)
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for name in names:
        split = run_split(name, ids[name], args.data, args.reference)
        results.append(split)
        (args.out / f"{name}.json").write_text(
            json.dumps({"metadata": metadata, **split}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        errors = sum(len(split["metrics"][m]["errors"]) for m in METHODS)
        print(f"{name}: {len(ids[name])} cases run, {errors} method errors")
    report = f"report-{args.split_name}.md" if args.split_name else "report.md"  # never overwrite report.md
    (args.out / report).write_text(build_report(results, metadata), encoding="utf-8")
    print(f"wrote {args.out}/{report}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
