"""Tests for Baseline B (resauce.baseline_b), evaluation-spec §5.

Only the code that turns a stored answer into a method output is tested; the model is never called.
Small hand-written case: infusion on 2030-03-01, nothing read from data/ or reference/.
"""

import json
from datetime import date, datetime

import pytest

from resauce import evaluate
from resauce.baseline_b import AnswerError, evaluate_case, sha256, user_message
from resauce.models import Case, DocumentVersion, ObservationWindow, RecordVersion, ResearchRecord

TEXT = "Neuro check 2030-03-05 09:00: ICE 6/10. Awake."
CASE = Case("SYN-9999", 50, date(2030, 3, 1),
            ResearchRecord("SYN-9999", "SYN-9999-R",
                           (RecordVersion(1, datetime(2030, 3, 20, 9), True, date(2030, 3, 5), 1, None),)),
            (DocumentVersion("SYN-9999", "SYN-9999-D01", 1, "signed", "nursing_note", "nurse",
                             datetime(2030, 3, 5, 10), None, TEXT),))
WINDOW = ObservationWindow(0, 28)


def stored(answer=None, stop_reason="end_turn", text=None):
    return {"stop_reason": stop_reason, "stop_details": None,
            "answer_text": text if text is not None else json.dumps(answer)}


def answer(reason="in scope", onset="7.7", grade="7.2", evidence=()):
    field = lambda category: {"category": category, "documented_value": "x", "explanation": "y",
                              "evidence": list(evidence)}
    return {"out_of_scope_reason": reason, "onset": field(onset), "max_grade": field(grade)}


def test_categories_are_kept_and_quotes_get_their_offsets():
    quote = {"document_id": "SYN-9999-D01", "version": 1, "quote": "ICE 6/10."}
    output = evaluate_case(CASE, stored(answer(evidence=[quote])))
    assert output["out_of_scope"] is None
    assert output["fields"]["onset"]["category"] == "7.7"
    assert output["fields"]["max_grade"]["category"] == "7.2"
    ref = output["fields"]["max_grade"]["evidence"][0]
    assert TEXT[ref["start"]:ref["end"]] == "ICE 6/10."
    assert evaluate.evidence_validity(CASE, output) == (2, 2)  # the same quote, under both fields


def test_a_quote_not_in_the_document_fails_the_evidence_check():
    wrong = {"document_id": "SYN-9999-D01", "version": 1, "quote": "ICE 6/10 at 09:00."}  # reworded
    elsewhere = {"document_id": "SYN-9999-D01", "version": 2, "quote": "ICE 6/10."}  # no such version
    output = evaluate_case(CASE, stored(answer(evidence=[wrong, elsewhere])))
    assert [e["start"] for e in output["fields"]["onset"]["evidence"]] == [-1, -1]
    assert evaluate.evidence_validity(CASE, output) == (0, 4)


def test_an_out_of_scope_answer_flags_the_case_and_drops_the_field_answers():
    quote = {"document_id": "SYN-9999-D01", "version": 1, "quote": "Awake."}
    output = evaluate_case(CASE, stored(answer(reason="documented death", evidence=[quote])))
    assert output["out_of_scope"]["reason"] == "documented death"
    assert {f["category"] for f in output["fields"].values()} == {"out of scope (documented death)"}
    assert all(f["evidence"] == [] for f in output["fields"].values())
    reference = {"out_of_scope": "documented death", "fields": {"onset": "7.7", "max_grade": "7.7"}}
    scored = evaluate.score_method([("SYN-9999", reference, output)], scores_out_of_scope=True)
    assert scored["out_of_scope"]["reason_matches"] == 1


def test_claude_codes_structured_answer_counts_as_finished_only_when_completed():
    # Claude Code returns the schema answer through its StructuredOutput tool: stop reason "tool_use".
    completed = {**stored(answer()), "stop_reason": "tool_use", "finished": True,
                 "models_reported": ["claude-opus-5-5"]}
    assert evaluate_case(CASE, completed)["fields"]["max_grade"]["category"] == "7.2"
    with pytest.raises(AnswerError):
        evaluate_case(CASE, {**completed, "finished": False})
    with pytest.raises(AnswerError):
        evaluate_case(CASE, {**completed, "models_reported": ["claude-sonnet-5-5"]})


@pytest.mark.parametrize("bad", [
    stored(stop_reason="refusal", text=""),
    stored(stop_reason="max_tokens", text='{"out_of_scope_reason": "in sc'),
    stored(text="not json"),
    stored(text=json.dumps({"onset": {}})),
])
def test_an_unusable_answer_is_an_error_not_a_guess(bad):
    with pytest.raises(AnswerError):
        evaluate_case(CASE, bad)


def test_a_stored_answer_for_other_instructions_or_case_files_is_not_used(tmp_path):
    good = {**stored(answer()), "system_prompt_sha256": "run", "usage": {},
            "user_message_sha256": sha256(user_message(CASE, WINDOW))}
    for name, record in (("matching", good), ("other instructions", {**good, "system_prompt_sha256": "older"}),
                         ("other case files", {**good, "user_message_sha256": "edited"})):
        (tmp_path / "SYN-9999.json").write_text(json.dumps(record))
        entry, _ = evaluate.run_baseline_b(CASE, WINDOW, tmp_path, {"system_prompt_sha256": "run"})
        assert ("output" in entry) == (name == "matching"), name
