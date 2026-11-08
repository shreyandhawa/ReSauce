"""Compare the independent (blind) answers with the intended answers.

Usage (from the project folder):
    .venv/bin/python -m tools.compare_answers

Reads  reference/dev-v1/independent/<id>.json  and  reference/dev-v1/intended/<id>.json
for every case in data/dev-v1, and writes  reference/dev-v1/comparison.md.
It changes no answer file and decides nothing: it only counts and lists
differences, so that a person can adjudicate them later.

What is compared
  * out of scope: both null, or both set with the same reason. A "same reason"
    is judged by which of the five triggers of clinical-methods §5 the text
    names (CAPD, death, record Grade 5, developmental delay, age under 18);
    both texts are shown in the report.
  * category of each field, by its leading code ("7.5 (attribution)" -> "7.5",
    "out of scope (...)" -> "out of scope").
  * documented value of each field, in three groups (only where both sides are
    in scope): agree; differ only in form; real disagreement.
        agree           the same grade, date or range (or both say "no value")
        form only       a grade/date is missing on one or both sides, or the
                        same grade/date is written in a different way
        real            a different grade, date or range
  * every evidence quote of an independent answer must occur exactly once in
    the document version it names (found with resauce.loader).
signed_difference_days is not compared.
Any independent file that is missing, unreadable or lacks a field is listed.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from resauce.loader import DataFormatError, load_case

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dev-v1"
REF = ROOT / "reference" / "dev-v1"
INTENDED = REF / "intended"
INDEPENDENT = REF / "independent"
SPLITS = REF / "splits.json"
OUTPUT = REF / "comparison.md"
NOTES = REF / "independent-run-notes.md"


# Section 8, written by hand from the saved blind-run notes (the notes are free text).
UNCLEAR_RULES = r"""
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
"""

FIELDS = ("onset", "max_grade")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
CODE = re.compile(r"\s*(7\.[1-8])\b")


# --------------------------------------------------------------------------
# Reading files
# --------------------------------------------------------------------------


def read_json(path: Path):
    """Return (data, problem). Exactly one of the two is None."""
    if not path.exists():
        return None, "file is missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as error:
        return None, f"unreadable: {error}"


def structure_problems(answer) -> list[str]:
    """Fields an independent answer must have for the comparison to run."""
    if not isinstance(answer, dict):
        return ["top level is not an object"]
    problems = []
    for key in ("case_id", "answer_kind", "out_of_scope", "fields"):
        if key not in answer:
            problems.append(f"lacks '{key}'")
    fields = answer.get("fields")
    if not isinstance(fields, dict):
        problems.append("'fields' is not an object")
        return problems
    for name in FIELDS:
        field = fields.get(name)
        if not isinstance(field, dict):
            problems.append(f"lacks fields.{name}")
            continue
        for key in ("category", "documented_value"):
            if key not in field:
                problems.append(f"lacks fields.{name}.{key}")
        if not isinstance(field.get("category"), str):
            problems.append(f"fields.{name}.category is not text")
    return problems


# --------------------------------------------------------------------------
# Categories, out of scope
# --------------------------------------------------------------------------


def category_code(category) -> str:
    if not isinstance(category, str):
        return "(none)"
    match = CODE.match(category)
    if match:
        return match.group(1)
    if category.strip().lower().startswith("out of scope"):
        return "out of scope"
    return category.strip()


def oos_trigger(oos) -> str | None:
    """Which §5 trigger the reason names. None if no out-of-scope flag."""
    if not oos:
        return None
    reason = str(oos.get("reason", "")).lower() if isinstance(oos, dict) else str(oos).lower()
    if "capd" in reason:
        return "CAPD"
    if "death" in reason or "died" in reason:
        return "death"
    if "grade 5" in reason or "grade of 5" in reason:
        return "record Grade 5"
    if "developmental" in reason:
        return "developmental delay"
    if "age" in reason or "18" in reason:
        return "age under 18"
    return "(unrecognised reason)"


# --------------------------------------------------------------------------
# Documented values
# --------------------------------------------------------------------------
# A value is normalised to one of:
#   ("date", "YYYY-MM-DD") / ("day", n) / ("range", a, b)   (onset)
#   ("grade", n) / ("grange", lo, hi)                        (max_grade)
#   ("none", label)    no grade or date; label says how it was written
#   ("odd", text)      something not recognised


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalise(value) -> dict:
    """Return {'main': tuple, 'alt': tuple or None}. 'alt' is a second way of
    writing the same value (study day next to a date)."""
    if value is None:
        return {"main": ("none", "null"), "alt": None}
    if isinstance(value, bool):
        return {"main": ("odd", repr(value)), "alt": None}
    if is_int(value):
        return {"main": ("grade", value), "alt": None}
    if isinstance(value, str):
        text = value.strip()
        if DATE.fullmatch(text):
            return {"main": ("date", text), "alt": None}
        if re.fullmatch(r"[0-9]", text):
            return {"main": ("grade", int(text)), "alt": None}
        lowered = text.lower()
        if lowered in ("none found", "none", "undetermined", "n/a"):
            return {"main": ("none", lowered), "alt": None}
        return {"main": ("odd", text), "alt": None}
    if isinstance(value, dict):
        if "grade" in value and is_int(value["grade"]):
            return {"main": ("grade", value["grade"]), "alt": None}
        if "date" in value and isinstance(value["date"], str):
            alt = ("day", value["study_day"]) if is_int(value.get("study_day")) else None
            return {"main": ("date", value["date"]), "alt": alt}
        if "range" in value and isinstance(value["range"], list) and len(value["range"]) == 2:
            low, high = value["range"]
            if is_int(low) and is_int(high):
                return {"main": ("grange", low, high), "alt": None}
            alt = None
            days = value.get("study_days")
            if isinstance(days, list) and len(days) == 2 and all(is_int(d) for d in days):
                alt = ("drange", days[0], days[1])
            return {"main": ("range", low, high), "alt": alt}
        if "undetermined" in value:
            return {"main": ("none", "undetermined"), "alt": None}
        return {"main": ("odd", json.dumps(value, sort_keys=True)), "alt": None}
    return {"main": ("odd", repr(value)), "alt": None}


def show_value(value) -> str:
    """Short text for the report."""
    norm = normalise(value)["main"]
    alt = normalise(value)["alt"]
    kind = norm[0]
    if kind == "date":
        extra = f" (Day {alt[1]:+d})" if alt else ""
        return f"{norm[1]}{extra}"
    if kind == "range":
        extra = f" (Days {alt[1]:+d} to {alt[2]:+d})" if alt else ""
        return f"{norm[1]} to {norm[2]}{extra}"
    if kind == "grade":
        return f"Grade {norm[1]}"
    if kind == "grange":
        return f"Grade {norm[1]} to {norm[2]}"
    if kind == "none":
        reason = ""
        if isinstance(value, dict) and value.get("undetermined"):
            reason = ": " + shorten(value["undetermined"], 70)
        return f"no value ({norm[1]}{reason})"
    return f"? {shorten(str(norm[1]), 60)}"


def compare_value(intended, independent) -> tuple[str, str]:
    """Return (group, why). group is 'agree', 'form' or 'real'."""
    a, b = normalise(intended), normalise(independent)
    ka, kb = a["main"], b["main"]
    if ka[0] == "odd" or kb[0] == "odd":
        return "form", "value not in a recognised shape"
    a_has = ka[0] != "none"
    b_has = kb[0] != "none"
    if not a_has and not b_has:
        if ka[1] == kb[1]:
            return "agree", ""
        return "form", f"no value on either side, written '{ka[1]}' and '{kb[1]}'"
    if a_has != b_has:
        side = "independent" if a_has else "intended"
        return "form", f"{side} has no grade or date"
    # both have a value
    if ka[0] != kb[0]:
        if ka[0] in ("date", "range") and kb[0] in ("date", "range"):
            return "real", "a single date against a range"
        if ka[0] in ("grade", "grange") and kb[0] in ("grade", "grange"):
            return "real", "a single grade against a range"
        return "real", "values of different kinds"
    if ka != kb:
        return "real", "different " + {
            "date": "onset date",
            "range": "onset range",
            "grade": "grade",
            "grange": "grade range",
        }[ka[0]]
    # same grade/date/range: is it written the same way?
    if a["alt"] != b["alt"]:
        if a["alt"] and b["alt"]:
            return "form", "same value, different study day"
        return "form", "same value, study day given on one side only"
    if shape(intended) != shape(independent):
        return "form", "same value, written in a different way"
    return "agree", ""


def shape(value) -> str:
    if isinstance(value, dict):
        return "object:" + ",".join(sorted(value))
    return type(value).__name__


# --------------------------------------------------------------------------
# Evidence quotes
# --------------------------------------------------------------------------


def iter_quotes(node, path=""):
    """Yield (path, ref) for every {document_id, version, quote} object."""
    if isinstance(node, dict):
        if all(key in node for key in ("document_id", "version", "quote")):
            yield path, node
        for key, value in node.items():
            yield from iter_quotes(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_quotes(value, f"{path}[{index}]")


def check_quotes(answer, case) -> tuple[int, list[str]]:
    """Return (number of quotes, list of problems)."""
    total, problems = 0, []
    for path, ref in iter_quotes(answer):
        total += 1
        name = f"{ref['document_id']} v{ref['version']}"
        quote = ref["quote"]
        if not isinstance(quote, str) or not quote:
            problems.append(f"{path}: quote is empty or not text ({name})")
            continue
        if not is_int(ref["version"]):
            problems.append(f"{path}: version is not a whole number ({name})")
            continue
        document = case.get_document_version(ref["document_id"], ref["version"])
        if document is None:
            problems.append(f"{path}: {name} does not exist; quote {shorten(quote, 60)!r}")
            continue
        # overlapping occurrences count too
        position, count = document.text.find(quote), 0
        while position != -1:
            count += 1
            position = document.text.find(quote, position + 1)
        if count != 1:
            problems.append(f"{path}: {name} has the quote {count} times: {shorten(quote, 80)!r}")
    return total, problems


# --------------------------------------------------------------------------
# Report helpers
# --------------------------------------------------------------------------


def shorten(text, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def derivation_text(answer: dict, name: str) -> str:
    top = answer.get("derivation")
    if isinstance(top, dict) and top.get(name):
        return str(top[name])
    inside = answer.get("fields", {}).get(name, {})
    if isinstance(inside, dict) and inside.get("derivation"):
        return str(inside["derivation"])
    if isinstance(top, str) and top:
        return top
    return "(none written)"


def pct(part: int, whole: int) -> str:
    return f"{part} of {whole}" if whole else "0 of 0"


def table(headers: list[str], rows: list[list]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return lines


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    dev_ids = set(splits["dev"])
    case_ids = sorted(path.name for path in (DATA / "cases").iterdir() if path.is_dir())

    listed_problems: list[str] = []  # missing/unreadable/lacking, quotes
    rows = []  # one dict per case that could be compared
    quote_total, quote_bad = 0, 0

    for case_id in case_ids:
        split = "dev" if case_id in dev_ids else "held-out"
        intended, problem = read_json(INTENDED / f"{case_id}.json")
        if problem:
            listed_problems.append(f"{case_id}: INTENDED answer {problem}")
            continue
        independent, problem = read_json(INDEPENDENT / f"{case_id}.json")
        if problem:
            listed_problems.append(f"{case_id}: independent answer {problem}")
            continue
        missing = structure_problems(independent)
        if missing:
            listed_problems.append(f"{case_id}: independent answer " + "; ".join(missing))
            continue
        if independent["case_id"] != case_id:
            listed_problems.append(
                f"{case_id}: independent answer says case_id {independent['case_id']!r}"
            )
        if independent.get("answer_kind") != "independent":
            listed_problems.append(
                f"{case_id}: answer_kind is {independent.get('answer_kind')!r}, not 'independent'"
            )
        try:
            case = load_case(DATA / "cases" / case_id)
            total, bad = check_quotes(independent, case)
            quote_total += total
            quote_bad += len(bad)
            listed_problems += [f"{case_id}: quote problem at {item}" for item in bad]
        except DataFormatError as error:
            listed_problems.append(f"{case_id}: case could not be loaded, quotes unchecked: {error}")
        rows.append({"id": case_id, "split": split, "i": intended, "b": independent})

    # ----- evaluate -----
    results = []
    for row in rows:
        i, b = row["i"], row["b"]
        i_trigger, b_trigger = oos_trigger(i.get("out_of_scope")), oos_trigger(b.get("out_of_scope"))
        if i_trigger is None and b_trigger is None:
            oos = "agree"
        elif i_trigger == b_trigger:
            oos = "agree"
        else:
            oos = "differ"
        fields = {}
        for name in FIELDS:
            fi, fb = i["fields"][name], b["fields"][name]
            ci, cb = category_code(fi.get("category")), category_code(fb.get("category"))
            if ci == "out of scope" or cb == "out of scope":
                group, why = "n/a", "out of scope on at least one side"
            else:
                group, why = compare_value(fi.get("documented_value"), fb.get("documented_value"))
            fields[name] = {"ci": ci, "cb": cb, "group": group, "why": why, "fi": fi, "fb": fb}
        results.append({**row, "oos": oos, "oi": i_trigger, "ob": b_trigger, "fields": fields})

    # ----- write report -----
    out: list[str] = []
    out.append("# Independent answers compared with intended answers (dev-v1)")
    out.append("")
    out.append(
        "Made by `tools/compare_answers.py` (run `python -m tools.compare_answers`). "
        "Intended answers: `reference/dev-v1/intended/`. Independent answers: "
        "`reference/dev-v1/independent/` (written blind by Claude Opus, not clinician-verified). "
        "Neither side is verified: a difference means the two disagree, not that either is wrong. "
        "No answer file was changed and nothing is adjudicated here. These are counts on synthetic "
        "cases, not clinical validation."
    )
    out.append("")
    out.append(f"Cases in data/dev-v1: {len(case_ids)}. Compared: {len(rows)}.")
    out.append("")

    # --- problems with files
    out.append("## 1. Files that were missing, unreadable or incomplete")
    out.append("")
    files_bad = [p for p in listed_problems if "quote problem" not in p]
    if files_bad:
        out += [f"- {p}" for p in files_bad]
    else:
        out.append("None. All independent files exist, parse, and have every field compared here.")
    out.append("")

    # --- agreement counts
    def counts(subset: list[dict]) -> list[str]:
        n = len(subset)
        lines = []
        lines.append(
            f"- Out of scope: {pct(sum(r['oos'] == 'agree' for r in subset), n)} cases agree "
            "(both in scope, or both out of scope with the same trigger)."
        )
        cat_total = 0
        cat_agree = 0
        val_total = Counter()
        for name in FIELDS:
            agree = sum(r["fields"][name]["ci"] == r["fields"][name]["cb"] for r in subset)
            cat_total += n
            cat_agree += agree
            groups = Counter(r["fields"][name]["group"] for r in subset)
            val_both = sum(groups[g] for g in ("agree", "form", "real"))
            val_total.update({g: groups[g] for g in ("agree", "form", "real")})
            label = "Onset" if name == "onset" else "Max grade"
            lines.append(f"- {label} category: {pct(agree, n)} agree.")
            lines.append(
                f"- {label} documented value (where both sides are in scope, {val_both} cases): "
                f"{groups['agree']} agree, {groups['form']} differ only in form, "
                f"{groups['real']} real disagreement."
            )
        lines.append(f"- Category overall (both fields): {pct(cat_agree, cat_total)} agree.")
        both = sum(val_total.values())
        lines.append(
            f"- Documented value overall ({both} field comparisons): {val_total['agree']} agree, "
            f"{val_total['form']} differ only in form, {val_total['real']} real disagreement."
        )
        return lines

    out.append("## 2. Agreement counts")
    out.append("")
    out.append(
        "Value groups: **agree** = same grade, date or range; **form only** = a grade or date "
        "is missing on one or both sides, or the same grade/date is written differently; "
        "**real** = a different grade, date or range. `signed_difference_days` is not compared."
    )
    out.append("")
    for title, subset in (
        ("All cases", results),
        ("Dev split (20 cases)", [r for r in results if r["split"] == "dev"]),
        ("Held-out split (not sealed)", [r for r in results if r["split"] == "held-out"]),
    ):
        out.append(f"### {title}: {len(subset)} cases")
        out.append("")
        out += counts(subset)
        out.append("")

    # --- evidence quotes
    out.append("## 3. Independent evidence quotes")
    out.append("")
    out.append(
        f"Quotes checked: {quote_total}. Not found exactly once in the named document "
        f"version: {quote_bad}."
    )
    out.append("")
    quote_lines = [p for p in listed_problems if "quote problem" in p]
    if quote_lines:
        out += [f"- {p}" for p in quote_lines]
        out.append("")

    # --- out of scope detail
    out.append("## 4. Out-of-scope disagreements and out-of-scope cases")
    out.append("")
    oos_rows = [r for r in results if r["oi"] or r["ob"]]
    if oos_rows:
        out += table(
            ["Case", "Split", "Agree?", "Intended", "Independent"],
            [
                [
                    r["id"],
                    r["split"],
                    r["oos"],
                    (r["i"]["out_of_scope"] or {}).get("reason", "not out of scope"),
                    (r["b"]["out_of_scope"] or {}).get("reason", "not out of scope"),
                ]
                for r in oos_rows
            ],
        )
    else:
        out.append("No case is out of scope on either side.")
    out.append("")

    # --- category disagreements
    out.append("## 5. Category disagreements")
    out.append("")
    cat_rows = []
    for r in results:
        for name in FIELDS:
            f = r["fields"][name]
            if f["ci"] != f["cb"]:
                cat_rows.append(
                    [
                        r["id"],
                        r["split"],
                        name,
                        f"{f['fi'].get('category')} / {show_value(f['fi'].get('documented_value'))}",
                        f"{f['fb'].get('category')} / {show_value(f['fb'].get('documented_value'))}",
                        shorten(derivation_text(r["b"], name), 400),
                        shorten(
                            "note: "
                            + str(f["fi"].get("difference_note"))
                            + " | ambiguity: "
                            + str(r["i"].get("ambiguity_notes")),
                            300,
                        ),
                    ]
                )
    if cat_rows:
        out.append(f"{len(cat_rows)} field-level disagreements.")
        out.append("")
        out += table(
            [
                "Case",
                "Split",
                "Field",
                "Intended category / value",
                "Independent category / value",
                "Independent derivation",
                "Intended difference_note / ambiguity_notes",
            ],
            cat_rows,
        )
    else:
        out.append("None.")
    out.append("")

    # --- value disagreements
    for group, title, blurb in (
        ("real", "6. Real documented-value disagreements", "Different grade, date or range."),
        (
            "form",
            "7. Documented values that differ only in form",
            "A grade or date is missing on one or both sides, or the same grade/date is written differently.",
        ),
    ):
        out.append(f"## {title}")
        out.append("")
        out.append(blurb + " The category column says whether the categories agree.")
        out.append("")
        value_rows = []
        for r in results:
            for name in FIELDS:
                f = r["fields"][name]
                if f["group"] == group:
                    value_rows.append(
                        [
                            r["id"],
                            r["split"],
                            name,
                            "same" if f["ci"] == f["cb"] else f"differ ({f['ci']} vs {f['cb']})",
                            f"{f['fi'].get('category')} / {show_value(f['fi'].get('documented_value'))}",
                            f"{f['fb'].get('category')} / {show_value(f['fb'].get('documented_value'))}",
                            f["why"],
                        ]
                        + (
                            [
                                shorten(derivation_text(r["b"], name), 400),
                                shorten(
                                    "note: "
                                    + str(f["fi"].get("difference_note"))
                                    + " | ambiguity: "
                                    + str(r["i"].get("ambiguity_notes")),
                                    300,
                                ),
                            ]
                            if group == "real"
                            else []
                        )
                    )
        headers = [
            "Case",
            "Split",
            "Field",
            "Category",
            "Intended category / value",
            "Independent category / value",
            "What differs",
        ]
        if group == "real":
            headers += ["Independent derivation", "Intended difference_note / ambiguity_notes"]
        if value_rows:
            out.append(f"{len(value_rows)} field-level rows.")
            out.append("")
            out += table(headers, value_rows)
        else:
            out.append("None.")
        out.append("")

    # --- unclear rules
    out.append("## 8. Unclear rules reported in the blind run notes")
    out.append("")
    if NOTES.exists():
        out.append(UNCLEAR_RULES.rstrip("\n"))
    else:
        out.append(
            f"**Not produced.** `{NOTES.relative_to(ROOT)}` was not found when this report "
            "was generated, so no list of \"unclear rules\" could be made and none was invented."
        )
    out.append("")

    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"Compared {len(rows)} of {len(case_ids)} cases; {len(files_bad)} file problem(s); {quote_bad} quote problem(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
