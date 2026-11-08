"""Tests for the rules engine (resauce.engine).

A few focused tests on small hand-written cases, one per rule that decides
an answer, plus one test that runs the engine over the 20 dev cases
(docs/evaluation-spec.md §1) and checks every cited quote. Held-out cases
are never loaded, and no reference answer is read.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from resauce.engine import evaluate_case, evaluate_folder
from resauce.extract import extract_case
from resauce.loader import check_evidence_ref, load_case
from resauce.models import Case, DocumentVersion, EvidenceRef, ObservationWindow, RecordVersion, ResearchRecord

ROOT = Path(__file__).resolve().parent.parent
DEV_CASES = (
    "SYN-0001", "SYN-0003", "SYN-0006", "SYN-0008", "SYN-0010", "SYN-0013", "SYN-0017",
    "SYN-0021", "SYN-0026", "SYN-0027", "SYN-0037", "SYN-0038", "SYN-0043", "SYN-0044",
    "SYN-0047", "SYN-0054", "SYN-0056", "SYN-0065", "SYN-0067", "SYN-0070",
)
WINDOW = ObservationWindow(0, 28)


def make_case(notes, records):
    """A case with infusion on 2030-03-01.

    notes: (text, documented_at, note_type) tuples, one signed document each.
    records: (recorded_at, icans_reported, onset, grade) tuples, one per record version.
    """
    documents = tuple(
        DocumentVersion("SYN-9999", f"SYN-9999-D{n:02d}", 1, "signed", note_type, "nurse",
                        datetime.fromisoformat(at), None, text)
        for n, (text, at, note_type) in enumerate(notes, start=1))
    versions = tuple(
        RecordVersion(n, datetime.fromisoformat(at), reported, date.fromisoformat(onset) if onset else None,
                      grade, None if n == 1 else "revised")
        for n, (at, reported, onset, grade) in enumerate(records, start=1))
    case = Case("SYN-9999", 50, date(2030, 3, 1), ResearchRecord("SYN-9999", "SYN-9999-R", versions), documents)
    return evaluate_case(case, extract_case(case), WINDOW).to_dict()


def test_ice_alone_gives_the_wrong_grade():
    # clinical-methods §3.5: ICE 8 (Grade 1) but awakens only to touch (Grade 3).
    result = make_case(
        [("Neuro check 2030-03-07 09:00: ICE 8/10. Opens eyes only when gently shaken by the shoulder, "
          "then answers questions. No sedating medication in the previous 24 h.",
          "2030-03-07T10:00", "nursing_note")],
        [("2030-03-20T09:00", True, "2030-03-07", 1)])
    grade = result["fields"]["max_grade"]
    assert grade["category"] == "7.2"
    assert grade["documented_value"] == {"grade": 3}
    assert result["fields"]["onset"]["category"] == "7.7"


def test_missing_is_not_absent():
    # §7.1 / §7.4: a record onset before the first finding is a mismatch only
    # if a formal Grade 0 assessment documents no ICANS on the record's date.
    finding = ("Neuro check 2030-03-07 09:00: ICE 6/10.", "2030-03-07T10:00", "nursing_note")
    record = [("2030-03-20T09:00", True, "2030-03-05", 2)]
    assert make_case([finding], record)["fields"]["onset"]["category"] == "7.4"

    grade0 = ("Neuro check 2030-03-05 09:00: ICE 10/10, alert.", "2030-03-05T10:00", "nursing_note")
    onset = make_case([grade0, finding], record)["fields"]["onset"]
    assert onset["category"] == "7.1"
    assert onset["signed_difference_days"] == -2


def test_competing_cause_makes_the_grade_ambiguous():
    # §7.5 example: the Grade 3 finding coincides with lorazepam; no clinician statement.
    result = make_case(
        [("Neuro check 2030-03-06 09:00: ICE 8/10; awakens only when gently shaken; "
          "received lorazepam 2 h ago.", "2030-03-06T10:00", "nursing_note")],
        [("2030-03-20T09:00", True, "2030-03-06", 1)])
    grade = result["fields"]["max_grade"]
    assert grade["category"] == "7.5"
    # The §7.5 example's two readings (Grade 3 -> 7.2, Grade 1 -> 7.7). The engine
    # also lets the ICE 8 be attributed to lorazepam (a third reading, 7.3).
    assert {"7.2", "7.7"} <= {r["category"] for r in grade["readings"]}
    assert "attribution" in grade["difference_note"]


def test_legitimate_revision_needs_new_documentation():
    # §7.6 / A28: record revised Grade 2 -> 3 after an EEG report documented in between.
    notes = [("Neuro check 2030-03-06 09:00: ICE 5/10.", "2030-03-06T10:00", "nursing_note")]
    records = [("2030-03-09T09:00", True, "2030-03-06", 2), ("2030-03-11T09:00", True, "2030-03-06", 3)]
    eeg = "EEG 2030-03-08: non-convulsive seizures on EEG, resolved with levetiracetam."
    revised = make_case(notes + [(eeg, "2030-03-10T12:00", "eeg_report")], records)
    assert revised["fields"]["max_grade"]["category"] == "7.6"
    assert revised["fields"]["max_grade"]["record_history"]["c"] is True

    unexplained = make_case(notes + [(eeg, "2030-03-08T12:00", "eeg_report")], records)
    assert unexplained["fields"]["max_grade"]["category"] == "7.7"
    assert "revision without new documentation" in [f["flag"] for f in unexplained["other_flags"]]


def test_onset_mismatch_with_a_date_range():
    # §6.1 / A26: "overnight" in a 2030-03-07 note gives the range 03-06 to 03-07.
    notes = [("Overnight ICE 6/10.", "2030-03-07T10:00", "nursing_note")]
    inside = make_case(notes, [("2030-03-20T09:00", True, "2030-03-06", 2)])["fields"]["onset"]
    assert inside["category"] == "7.7"
    assert inside["documented_value"]["range"] == ["2030-03-06", "2030-03-07"]

    later = make_case(notes, [("2030-03-20T09:00", True, "2030-03-09", 2)])["fields"]["onset"]
    assert later["category"] == "7.1"
    assert later["signed_difference_days"] == 2  # measured to the nearest end of the range


def _all_evidence(value):
    """Every evidence entry anywhere in a result."""
    if isinstance(value, dict):
        if {"document_id", "version", "start", "end", "quote"} <= value.keys():
            yield value
        for item in value.values():
            yield from _all_evidence(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_evidence(item)


@pytest.mark.parametrize("case_id", DEV_CASES)
def test_every_dev_case_runs_and_its_quotes_validate(case_id):
    folder = ROOT / "data" / "dev-v1" / "cases" / case_id
    result = evaluate_folder(folder).to_dict()
    case = load_case(folder)
    for field in ("onset", "max_grade"):
        assert result["fields"][field]["category"]
    for entry in _all_evidence(result):
        check_evidence_ref(case, EvidenceRef(entry["document_id"], entry["version"],
                                             entry["start"], entry["end"], entry["quote"]))
