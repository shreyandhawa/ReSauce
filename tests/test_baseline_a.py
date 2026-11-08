"""Tests for Baseline A (resauce.baseline_a), evaluation-spec §4.

Small hand-written cases: infusion on 2030-03-01, nothing read from data/ or reference/.
"""

from datetime import date, datetime

from resauce.baseline_a import evaluate_case
from resauce.extract import extract_case
from resauce.models import Case, DocumentVersion, RecordVersion, ResearchRecord


def run(documents, record):
    """documents: (document number, version, status, documented_at, text); record: (reported, onset, grade)."""
    docs = tuple(
        DocumentVersion("SYN-9999", f"SYN-9999-D{n:02d}", version, status, "nursing_note", "nurse",
                        datetime.fromisoformat(at), None, text)
        for n, version, status, at, text in documents)
    reported, onset, grade = record
    versions = (RecordVersion(1, datetime(2030, 3, 20, 9), reported,
                              date.fromisoformat(onset) if onset else None, grade, None),)
    case = Case("SYN-9999", 50, date(2030, 3, 1), ResearchRecord("SYN-9999", "SYN-9999-R", versions), docs)
    return evaluate_case(case, extract_case(case)).to_dict()["fields"]


def test_latest_version_is_used_even_unsigned_and_dated_by_documentation():
    # v1 (signed) ICE 9 -> Grade 1; v2 (unsigned) ICE 4 -> Grade 2. Event date 03-05, documented 03-08.
    fields = run([(1, 1, "signed", "2030-03-07T10:00", "Neuro check 2030-03-05 09:00: ICE 9/10."),
                  (1, 2, "unsigned", "2030-03-08T10:00", "Neuro check 2030-03-05 09:00: ICE 4/10.")],
                 (True, "2030-03-05", 1))
    assert fields["max_grade"]["category"] == "7.2"
    assert fields["max_grade"]["documented_value"] == {"grade": 2}
    assert fields["onset"]["documented_value"]["date"] == "2030-03-08"
    assert fields["onset"]["category"] == "7.1"
    assert fields["onset"]["signed_difference_days"] == -3


def test_no_graded_finding_means_no_discrepancy():
    # "drowsy" has no approved mapping, so nothing is graded: missing evidence = 7.7.
    fields = run([(1, 1, "signed", "2030-03-06T10:00", "Neuro check 2030-03-06 09:00: patient drowsy.")],
                 (True, "2030-03-06", 2))
    assert fields["onset"]["category"] == "7.7" and fields["max_grade"]["category"] == "7.7"
    assert fields["max_grade"]["documented_value"] == "none found"


def test_a_finding_with_a_record_that_reports_no_icans_is_a_discrepancy():
    # A negated seizure is not a finding; ICE 5 is. No ICANS in the record -> grade 7.2, onset 7.1.
    fields = run([(1, 1, "signed", "2030-03-06T10:00",
                   "Neuro check 2030-03-06 09:00: ICE 5/10. No seizure activity.")],
                 (False, None, None))
    assert fields["max_grade"]["category"] == "7.2"
    assert fields["max_grade"]["documented_value"] == {"grade": 2}
    assert fields["onset"]["category"] == "7.1"


def test_seizure_is_grade_3_and_grade_4_only_when_over_five_minutes():
    def grade_for(text):
        fields = run([(1, 1, "signed", "2030-03-06T10:00", text)], (True, "2030-03-06", 1))
        return fields["max_grade"]["documented_value"]
    assert grade_for("Neuro check 2030-03-06 09:00: witnessed seizure lasting 2 minutes, "
                     "back to baseline.") == {"grade": 3}
    assert grade_for("Neuro check 2030-03-06 09:00: witnessed seizure lasting 8 minutes.") == {"grade": 4}
