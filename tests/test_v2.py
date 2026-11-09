"""Tests for the v2 text clean-up layer (resauce.v2).

They check the part that decides whether v2 is trustworthy: positions and quotes stay exact
after text is changed, and with nothing to clean v2 gives the same observations as v1.
Only dev cases are loaded.
"""

from pathlib import Path

import pytest

from resauce import extract as v1
from resauce.loader import check_evidence_ref, load_case
from resauce.v2 import extract as v2
from resauce.v2.normalise import Step, normalise
from tests.test_extract import DEV_CASES, make_case

ROOT = Path(__file__).resolve().parent.parent


def test_positions_map_back_through_deletions_and_replacements():
    # "AB-C": delete "-"; "x" becomes the longer "yy".
    step_delete = Step("delete-dash", "", lambda t: [(t.index("-"), t.index("-") + 1, "")])
    step_grow = Step("grow-x", "", lambda t: [(t.index("x"), t.index("x") + 1, "yy")])
    n = normalise("AB-Cx!", (step_delete, step_grow))
    assert n.text == "ABCyy!"
    assert n.to_original(0, 3) == (0, 4)  # "ABC" covers the deleted dash too
    assert n.to_original(3, 4) == (4, 5)  # half of the replacement grows to the whole original "x"
    assert n.to_original(3, 5) == (4, 5)
    assert n.to_original(5, 6) == (5, 6)  # untouched text maps one to one
    assert n.to_original(6, 6) == (6, 6)  # an empty span at the very end


def test_overlapping_proposals_keep_the_earlier_step_and_report_the_other():
    first = Step("first", "", lambda t: [(0, 3, "Q")])
    second = Step("second", "", lambda t: [(2, 4, "Z")])
    n = normalise("abcdef", (first, second))
    assert n.text == "Qdef"
    assert [e.rule_id for e in n.dropped] == ["second"]


def test_quote_is_exact_original_text_after_cleaning():
    original = "Note 2030-03-06.\nNo sei​zure activity.\n"
    case = make_case(original)
    result = v2.extract_case(case)
    seizures = [o for o in result.observations if o.kind == "seizure"]
    assert seizures and all(o.status == "absent" for o in seizures)
    for observation in result.observations:
        check_evidence_ref(case, observation.evidence)  # offsets and quote are against the original
    assert any("​" in o.evidence.quote for o in seizures)  # the quote keeps the original characters


def test_nothing_to_clean_gives_exactly_the_v1_observations():
    for case_id in DEV_CASES:
        case = load_case(ROOT / "data" / "dev-v1" / "cases" / case_id)
        result = v2.extract_case(case)
        assert not any(n.edits for n in result.normalised.values()), case_id
        assert result.observations == v1.extract_case(case), case_id


@pytest.mark.parametrize("text", ["", "plain text, nothing odd."])
def test_text_without_edits_is_returned_unchanged(text):
    n = normalise(text, ())
    assert n.text == text and n.edits == () and n.to_original(0, len(text)) == (0, len(text))


def test_an_edit_that_only_inserts_text_is_refused():
    with pytest.raises(ValueError):
        normalise("abc", (Step("insert", "", lambda t: [(1, 1, "X")]),))
