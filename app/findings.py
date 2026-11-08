"""Findings a reviewer decides on, read from one stored ReSauce output, and their review state.

A finding is one item of the pipeline output that asks for a person: a field category that
is not 7.6 or 7.7, a "Needs human review" item, an extra flag, or an out-of-scope result.
The output itself is never changed; decisions live in the audit log and are matched to a
finding by case, finding ID and the SHA-256 of the output they were made on.

Category wording is the heading of docs/clinical-methods.md §7 for each code; for 7.1 it adds the
direction the engine measured (to the first day of the documented onset when the record is earlier,
to its last day when the record is later, §7.1 and A26).
"""

from __future__ import annotations

from resauce.evaluate import ALERTS, FIELDS, NEGATIVE, REVIEW_FLAGS  # evaluation-spec §3 classes

CLEAR = NEGATIVE  # 7.6 and 7.7: no alert
FIELD_NAMES = {"onset": "Onset date", "max_grade": "Maximum grade"}

# Queue order, most serious first (the task's ordering): alerts, then review flags and
# "review: …" items, then other flags and out-of-scope results.
TIER_ALERT, TIER_REVIEW, TIER_OTHER = 0, 1, 2
TIER_NAMES = {TIER_ALERT: "Discrepancy", TIER_REVIEW: "Needs review", TIER_OTHER: "Flag"}

DECISIONS = {"confirm": "Confirmed discrepancy", "dismiss": "Dismissed", "clinician": "Needs clinician"}
# "Confirm" on an item that is not a discrepancy confirms what that item says (§5: out-of-scope
# cases get no discrepancy category).
CONFIRM_LABELS = {"out_of_scope": "Confirmed out of scope", "flag": "Confirmed flag"}


def decision_label(decision: str, kind: str) -> str:
    return CONFIRM_LABELS.get(kind, DECISIONS[decision]) if decision == "confirm" else DECISIONS[decision]


def code(category: str | None) -> str | None:
    """The leading 7.x code of a category: "7.5 (attribution)" -> "7.5"."""
    if not category:
        return None
    head = category.split()[0] if category.split() else ""
    return head if head in ALERTS + REVIEW_FLAGS + CLEAR else None


def category_label(category: str, field: dict | None = None) -> str:
    """A category in plain words with its code, e.g. "Mismatch: record earlier than first finding (7.1)"."""
    if category.startswith("review:"):
        return "Needs human review: " + category[len("review:"):].strip()
    if category.startswith("out of scope"):
        return "Out of scope " + category[len("out of scope"):].strip()
    c = code(category)
    field = field or {}
    if c == "7.1":
        diff, note = field.get("signed_difference_days"), field.get("difference_note")
        if diff is not None and diff < 0:
            text = "Onset date mismatch: record earlier than first finding"
        elif diff is not None and diff > 0:
            text = "Onset date mismatch: record later than documented onset"
        elif note:
            text = f"Onset date mismatch: {note}"
        else:
            text = "Onset date mismatch"
    else:
        text = {
            "7.2": "Maximum grade mismatch: documents prove a higher grade",
            "7.3": "Grade not supported by documented evidence",
            "7.4": "Insufficient evidence",
            "7.5": "Ambiguous evidence",
            "7.6": "Legitimate revision (not an error)",
            "7.7": "No discrepancy",
            "7.8": "Missing recorded value",
        }.get(c, category)
    rest = category[len(c):].strip() if c else ""
    return f"{text} ({c}{' ' + rest if rest else ''})" if c else text


def category_kind(category: str | None) -> str:
    """alert, flag (7.4/7.5), review ("review: …"), clear (7.6/7.7), oos, or none."""
    if not category:
        return "none"
    c = code(category)
    if c in ALERTS:
        return "alert"
    if c in REVIEW_FLAGS:
        return "flag"
    if c in CLEAR:
        return "clear"
    if category.startswith("review:"):
        return "review"
    if category.startswith("out of scope"):
        return "oos"
    return "none"


def findings(output: dict) -> list[dict]:
    """Every finding in one ReSauce output, in the order the pipeline lists them."""
    found = []
    oos = output.get("out_of_scope")
    if oos:
        found.append({
            "finding_id": "out-of-scope", "kind": "out_of_scope", "tier": TIER_OTHER, "field": None,
            "category": f"out of scope ({oos.get('reason')})",
            "label": f"Out of scope: {oos.get('reason')}",
            "detail": f"Out-of-scope cases get no discrepancy category (clinical-methods §5). Source: {oos.get('source')}.",
            "evidence": oos.get("evidence") or [],
            "record_value": None, "documented_value": None,
        })
        return found
    for name in FIELDS:
        field = (output.get("fields") or {}).get(name)
        if not field:
            continue
        kind = category_kind(field["category"])
        if kind in ("clear", "none"):
            continue
        found.append({
            "finding_id": name, "kind": "field", "tier": TIER_ALERT if kind == "alert" else TIER_REVIEW,
            "field": name, "category": field["category"], "category_kind": kind,
            "label": category_label(field["category"], field),
            "detail": field.get("difference_note"),
            "evidence": field.get("evidence") or [],
            "record_value": field.get("record_value"), "documented_value": field.get("documented_value"),
            "signed_difference_days": field.get("signed_difference_days"),
            "readings": field.get("readings") or [],
        })
    for i, item in enumerate(output.get("review_items") or []):
        found.append({
            "finding_id": f"review-{i + 1}", "kind": "review_item", "tier": TIER_REVIEW,
            "field": item.get("field"), "category": None,
            "label": "Needs human review", "detail": item.get("detail"), "rule": item.get("rule"),
            "evidence": item.get("evidence") or [], "record_value": None, "documented_value": None,
        })
    for i, flag in enumerate(output.get("other_flags") or []):
        found.append({
            "finding_id": f"flag-{i + 1}", "kind": "flag", "tier": TIER_OTHER,
            "field": flag.get("field"), "category": None,
            "label": f"Flag: {flag.get('flag')}", "detail": flag.get("detail"),
            "evidence": flag.get("evidence") or [], "record_value": None, "documented_value": None,
        })
    return found


def latest_decisions(audit_entries: list[dict]) -> dict:
    """{(case_id, finding_id, output_sha256): decision entry}; a later decision replaces an earlier one."""
    latest = {}
    for entry in audit_entries:
        if entry.get("type") == "decision":
            latest[(entry["case_id"], entry["finding_id"], entry["output_sha256"])] = entry
    return latest


def with_decisions(case_id: str, run: dict | None, decisions: dict) -> list[dict]:
    """The findings of a stored run, each with the decision made on that exact output (or None)."""
    if not run or not run.get("resauce", {}).get("output"):
        return []
    sha = run["output_sha256"]
    out = []
    for f in findings(run["resauce"]["output"]):
        d = decisions.get((case_id, f["finding_id"], sha))
        out.append({**f, "case_id": case_id, "run_id": run["run_id"], "output_sha256": sha,
                    "decision": None if d is None else {**{k: d[k] for k in ("decision", "note", "reviewer", "time")},
                                                    "label": decision_label(d["decision"], f["kind"])}})
    return out


def status(run: dict | None, items: list[dict]) -> str:
    """not_run, error, no_findings, to_review (some open) or reviewed (all decided)."""
    if run is None:
        return "not_run"
    if run.get("error") or run.get("resauce", {}).get("error"):
        return "error"
    if not items:
        return "no_findings"
    return "to_review" if any(i["decision"] is None for i in items) else "reviewed"
