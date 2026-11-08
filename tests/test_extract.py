"""Tests for the extraction stage (resauce.extract).

A few focused tests for the trickiest patterns, using small hand-written
notes, plus one test that runs extraction over the 20 dev cases
(docs/evaluation-spec.md §1) and checks every quote. Held-out cases are
never loaded.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from resauce.extract import extract_case
from resauce.loader import check_evidence_ref, load_case
from resauce.models import Case, DocumentVersion, RecordVersion, ResearchRecord

ROOT = Path(__file__).resolve().parent.parent
DEV_CASES = (
    "SYN-0001", "SYN-0003", "SYN-0006", "SYN-0008", "SYN-0010", "SYN-0013", "SYN-0017",
    "SYN-0021", "SYN-0026", "SYN-0027", "SYN-0037", "SYN-0038", "SYN-0043", "SYN-0044",
    "SYN-0047", "SYN-0054", "SYN-0056", "SYN-0065", "SYN-0067", "SYN-0070",
)


def make_case(text, documented_at="2030-03-06T10:00", note_type="nursing_note"):
    """A one-document case; infusion on 2030-03-01."""
    document = DocumentVersion(
        case_id="SYN-9999", document_id="SYN-9999-D01", version=1, status="signed",
        note_type=note_type, author_role="nurse",
        documented_at=datetime.fromisoformat(documented_at), amendment_reason=None, text=text,
    )
    record = ResearchRecord("SYN-9999", "SYN-9999-R", (
        RecordVersion(1, datetime(2030, 3, 20, 9, 0), False, None, None, None),))
    return Case("SYN-9999", 50, date(2030, 3, 1), record, (document,))


def find(observations, kind, value=None):
    return [o for o in observations if o.kind == kind and (value is None or o.value == value)]


def test_negation_before_after_and_terminator():
    case = make_case(
        "Note 2030-03-06.\n"
        "No seizure activity.\n"
        "Sedating meds past 24 h: none\n"
        "No lorazepam was needed because the seizure stopped on its own.\n"
        "Not following commands, confused.\n"
    )
    observations = extract_case(case)
    seizures = find(observations, "seizure")
    assert [s.status for s in seizures] == ["absent", "present"]
    assert seizures[1].details["termination"] == "self-terminated"
    causes = find(observations, "competing_cause")
    assert [c.status for c in causes] == ["absent", "absent"]
    assert find(observations, "ungradeable_symptom", "confusion")[0].status == "present"


def test_ice_totals_chains_pain_scores_and_conditions():
    case = make_case(
        "Summary 2030-03-08.\n"
        "Course: ICE dropped to 7/10 on 2030-03-04 and 4/10 on 2030-03-05.\n"
        "Frontal headache 6/10 since noon.\n"
        "ICE SCORE ........ 8\n"
        "Plan: steroid taper when ICE 10/10.\n",
        documented_at="2030-03-08T12:00",
    )
    totals = find(extract_case(case), "ice_total")
    assert [(t.value, t.event_date, t.status) for t in totals] == [
        (7, date(2030, 3, 4), "present"),
        (4, date(2030, 3, 5), "present"),
        (8, date(2030, 3, 8), "present"),
        (10, date(2030, 3, 8), "uncertain"),
    ]


def test_relative_time_phrases_follow_the_a26_table():
    case = make_case(
        "Confused overnight per family.\n"
        "Tremor yesterday afternoon.\n"
        "Word-finding difficulty from the next morning on.\n"
        "Agitated this morning, drowsy overnight.\n",
        documented_at="2030-03-06T10:00",
    )
    observations = extract_case(case)
    confusion = find(observations, "ungradeable_symptom", "confusion")[0]
    assert (confusion.event_date, confusion.event_date_end, confusion.time_source) == (
        date(2030, 3, 5), date(2030, 3, 6), "relative")
    tremor = find(observations, "excluded_symptom", "tremor")[0]
    assert (tremor.event_date, tremor.time_source) == (date(2030, 3, 5), "relative")
    words = find(observations, "ungradeable_symptom", "word-finding difficulty")[0]
    assert (words.event_date, words.time_source) == (date(2030, 3, 6), "documented_at")
    assert "not in the A26 table" in words.note
    agitation = find(observations, "ungradeable_symptom", "agitation")[0]
    assert (agitation.event_date, agitation.time_source) == (None, "unresolved")


def test_not_assessable_needs_an_explicit_statement():
    case = make_case(
        "Neuro 2030-03-06 06:00: ICE not done, intubated and sedated, unable to assess.\n"
        "Later ICE 9/10, unable to write a sentence.\n"
    )
    observations = extract_case(case)
    not_assessable = find(observations, "not_assessable")
    assert len(not_assessable) == 1
    assert not_assessable[0].event_date == date(2030, 3, 6)
    assert find(observations, "competing_cause")[0].status == "present"


@pytest.mark.parametrize("case_id", DEV_CASES)
def test_every_dev_case_quote_validates(case_id):
    case = load_case(ROOT / "data" / "dev-v1" / "cases" / case_id)
    observations = extract_case(case)
    assert observations
    for observation in observations:
        check_evidence_ref(case, observation.evidence)
        if observation.time_evidence is not None:
            check_evidence_ref(case, observation.time_evidence)


def test_day_without_a_sign_is_read_like_day_plus():
    # "Day 5:" is the same as "Day +5": infusion 2030-03-01 gives 2030-03-06.
    case = make_case("Day 5: ICE 6/10.")
    ice = find(extract_case(case), "ice_total")[0]
    assert (ice.event_date, ice.time_source) == (date(2030, 3, 6), "in_text")


def test_clock_time_without_a_colon_is_a_time_but_a_dose_is_not():
    late = "2030-03-06T21:00"
    time_case = make_case("1900 ICE 6/10.", late)
    assert find(extract_case(time_case), "ice_total")[0].event_time.strftime("%H:%M") == "19:00"
    # "1900 mg" is a dose, even after a date; so is a number that is not a time.
    dose_case = make_case("2030-03-06 1900 mg given. ICE 6/10.", late)
    assert find(extract_case(dose_case), "ice_total")[0].event_time is None
    year_case = make_case("2030 ICE 6/10.", late)  # 2030 is the year of this note
    assert find(extract_case(year_case), "ice_total")[0].event_time is None


def test_spelling_variant_is_uncertain_never_present():
    case = make_case("Note 2030-03-06.\nSeizre noted.\nNo seizre today.\nGeneralised seizure on EEG.\n")
    seizures = find(extract_case(case), "seizure")
    by_quote = {s.evidence.quote: s for s in seizures}
    variant = by_quote["Seizre noted."]
    assert variant.status == "uncertain"
    assert "spelling variant of seizure" in variant.note
    assert variant.details["status_without_variant"] == "present"
    assert by_quote["No seizre today."].status == "uncertain"  # never certain, negated or not
    assert by_quote["No seizre today."].details["status_without_variant"] == "absent"
    assert by_quote["Generalised seizure on EEG."].status == "present"  # no variant: "seizure" is spelt right
