"""Baseline A: conventional validation without temporal reconciliation.

Implements docs/evaluation-spec.md §4: what a careful data manager would
check using the same extraction output as ReSauce (resauce.extract), but
with no attribution, no observation window and no record history.

- Documents: the latest version of each document, signed or not.
- Observations: status "present" only.
- Time: each observation is dated by its document's documented_at date.
- Grading: only the Table 6 findings listed in §4 (ICE total, mapped
  consciousness categories, seizures, hemi/paraparesis, ICP and edema).
  Everything else is not graded.
- Onset: earliest documentation date of a Grade 1+ finding. Maximum grade:
  the highest grade found.
- Categories: 7.1, 7.2, 7.3, 7.7 or 7.8 only. No review flags, no 7.4/7.5/7.6,
  no out-of-scope flag. Missing evidence is "no discrepancy" (7.7).

The Table 6 values below are written out here on purpose, so a change to the
rules engine can never change this baseline. Deterministic, standard library
only. Never reads reference answers.

Run "python -m resauce.baseline_a <case folder>" to print a case's result.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date

from resauce import phrases as P
from resauce.extract import Observation, extract_case
from resauce.loader import load_case, study_day
from resauce.models import Case
from resauce.timeline import evidence_dict

# Table 6 (§3.3), as listed in evaluation-spec §4.
CONSCIOUSNESS_GRADE = {P.SPONTANEOUS: 1, P.VOICE: 2, P.TACTILE: 3, P.UNAROUSABLE: 4}
# [OPERATIONAL] §4 names hemiparesis and paraparesis; the plegias are the stronger forms.
DEEP_FOCAL_MOTOR = ("hemiparesis", "hemiplegia", "paraparesis", "paraplegia")
ICP_GRADE = {
    "focal edema": 3,
    "diffuse cerebral edema": 4,
    "papilledema": 4,
    "cranial nerve VI palsy": 4,
    "decerebrate or decorticate posturing": 4,
    "Cushing's triad": 4,
}
FIVE_MINUTES = 300  # seconds


@dataclass(frozen=True)
class Finding:
    """One graded observation (Grade 1 or higher)."""

    obs: Observation
    grade: int
    label: str

    @property
    def day(self) -> date:
        return self.obs.documented_at.date()


@dataclass(frozen=True)
class BaselineResult:
    case_id: str
    fields: dict

    def to_dict(self) -> dict:
        return {"case_id": self.case_id, "fields": self.fields}


def ice_grade(total: int) -> int:
    """§4: 7-9 Grade 1, 3-6 Grade 2, 0-2 Grade 3 (10 is no impairment)."""
    if total >= 10:
        return 0
    if total >= 7:
        return 1
    if total >= 3:
        return 2
    return 3


def grade_observation(o: Observation) -> tuple[int, str] | None:
    """(grade, label) for an observation §4 can grade, else None."""
    kind, value = o.kind, o.value
    if kind == "ice_total":
        return ice_grade(value), f"ICE {value}/10"
    if kind == "ice_partial":
        # [OPERATIONAL] Same ICE parsing as ReSauce: five scored items add up
        # to a total. A partial ICE gives no total and is not graded.
        if o.details.get("all_five_items") and o.details.get("item_sum") is not None:
            total = o.details["item_sum"]
            return ice_grade(total), f"ICE items summing to {total}/10"
        return None
    if kind == "consciousness" and value in CONSCIOUSNESS_GRADE:
        return CONSCIOUSNESS_GRADE[value], value
    if kind == "seizure":
        low, high = o.details.get("min_seconds"), o.details.get("max_seconds")
        # [OPERATIONAL] §4: "documented as lasting more than 5 minutes". "over 5 minutes" is stored
        # as min_seconds = 300 with no maximum. A range starting at 5 minutes, an unstated duration
        # and "status epilepticus" without a duration stay Grade 3.
        over_five = low is not None and (low > FIVE_MINUTES or (high is None and low >= FIVE_MINUTES))
        if over_five:
            return 4, f"{value} seizure lasting more than 5 minutes"
        if o.details.get("repetitive") and o.details.get("return_to_baseline") is False:
            return 4, "repetitive seizures without return to baseline"
        return 3, f"{value} seizure"
    if kind == "motor_finding" and value in DEEP_FOCAL_MOTOR:
        return 4, value
    if kind == "icp_sign" and value in ICP_GRADE:
        return ICP_GRADE[value], value
    return None


def latest_version_ids(case: Case) -> set[tuple[str, int]]:
    """(document_id, version) of the latest version of each document, signed or not."""
    latest: dict[str, int] = {}
    for document in case.documents:
        latest[document.document_id] = max(latest.get(document.document_id, 0), document.version)
    return set(latest.items())


def find_findings(case: Case, observations: tuple[Observation, ...]) -> list[Finding]:
    """Grade 1+ findings in the latest document versions (present observations only)."""
    latest = latest_version_ids(case)
    findings = []
    for o in observations:
        if o.status != "present" or (o.evidence.document_id, o.evidence.version) not in latest:
            continue
        graded = grade_observation(o)
        if graded and graded[0] >= 1:
            findings.append(Finding(o, graded[0], graded[1]))
    return findings


def _evidence(findings: list[Finding], role: str) -> list[dict]:
    result, seen = [], set()
    for f in findings:
        ref = f.obs.evidence
        key = (ref.document_id, ref.version, ref.start, ref.end)
        if key not in seen:
            seen.add(key)
            result.append(evidence_dict(ref, f"{role}: {f.label} (Grade {f.grade})"))
    return result


def _field(category, record_value, documented_value, diff=None, note=None, evidence=()) -> dict:
    return {
        "category": category,
        "record_value": record_value,
        "documented_value": documented_value,
        "signed_difference_days": diff,
        "difference_note": note,
        "readings": [],
        "evidence": list(evidence),
        "record_history": None,
    }


def evaluate_case(case: Case, observations: tuple[Observation, ...]) -> BaselineResult:
    """Baseline A's onset and maximum-grade categories for one case."""
    findings = find_findings(case, observations)
    record = case.record.current
    found = bool(findings)

    # Onset: the earliest documentation date among the findings.
    if found:
        first = min(f.day for f in findings)
        onset_value = {"date": first.isoformat(), "study_day": study_day(case, first)}
        onset_evidence = _evidence([f for f in findings if f.day == first], "first documented finding")
    else:
        first, onset_value, onset_evidence = None, "none found", []
    record_onset = record.onset_date.isoformat() if record.onset_date else None
    diff = None  # record date minus documented date; only when the record reports an onset
    note = None
    # [OPERATIONAL] The 7.8 check comes before "no finding -> 7.7", as in the §4 list.
    if not record.icans_reported:
        category = "7.1" if found else "7.7"
        note = "record has no onset" if found else None
    elif record.onset_date is None:
        category, note = "7.8", "record has no onset"
    elif not found:
        category, note = "7.7", "no documented onset"
    else:
        diff = (record.onset_date - first).days
        category = "7.7" if diff == 0 else "7.1"
    onset = _field(category, record_onset, onset_value, diff, note, onset_evidence)

    # Maximum grade: the highest grade among the findings.
    if found:
        top = max(f.grade for f in findings)
        grade_value = {"grade": top}
        grade_evidence = _evidence([f for f in findings if f.grade == top], "highest grade")
    else:
        top, grade_value, grade_evidence = 0, "none found", []
    note = None
    if not record.icans_reported:
        category = "7.2" if found else "7.7"
    elif record.max_grade is None:
        category, note = "7.8", "record has no maximum grade"
    elif not found:
        category = "7.7"
    elif top > record.max_grade:
        category = "7.2"
    elif top < record.max_grade:
        category = "7.3"
    else:
        category = "7.7"
    grade = _field(category, record.max_grade, grade_value, None, note, grade_evidence)

    return BaselineResult(case.case_id, {"onset": onset, "max_grade": grade})


def evaluate_folder(case_folder) -> BaselineResult:
    """Load, extract and evaluate one case folder."""
    case = load_case(case_folder)
    return evaluate_case(case, extract_case(case))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m resauce.baseline_a <case folder>")
        return 2
    print(json.dumps(evaluate_folder(argv[0]).to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
