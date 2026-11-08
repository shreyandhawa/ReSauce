"""Tests for scoring (resauce.evaluate.score_method), evaluation-spec §3.

Small hand-made inputs only. No real case and no reference answer is read.
Each case has two fields; the one not under test is a quiet 7.7 -> 7.7.
"""

from resauce.evaluate import score_method


def reference(onset, grade, out_of_scope=None):
    return {"out_of_scope": out_of_scope, "fields": {"onset": onset, "max_grade": grade}}


def output(onset, grade, out_of_scope=None):
    return {"out_of_scope": {"reason": out_of_scope} if out_of_scope else None,
            "fields": {"onset": {"category": onset}, "max_grade": {"category": grade}}}


def score(*cases, oos=False):
    return score_method([(f"C{n}", ref, out) for n, (ref, out) in enumerate(cases)],
                        scores_out_of_scope=oos)


def combined(result):
    return result["fields"]["combined"]


def test_a_positive_field_with_any_alert_is_a_detection():
    # Reference 7.2, method says 7.3: still a detection (the exact category is scored separately).
    result = combined(score((reference("7.7", "7.2"), output("7.7", "7.3"))))
    assert result["counts"]["detections"] == 1 and result["counts"]["misses"] == 0
    assert result["precision"]["value"] == 1.0 and result["recall"]["value"] == 1.0
    assert result["exact_agreement_positive_fields"]["n"] == 0  # 7.3 is not 7.2


def test_a_miss_with_a_review_flag_is_still_a_miss():
    result = combined(score((reference("7.1", "7.7"), output("7.4", "7.7"))))
    counts = result["counts"]
    assert counts["detections"] == 0 and counts["misses"] == 1
    assert counts["misses_with_review_flag"] == 1
    assert counts["ref_7.1_flagged_7.4"] == 1  # review flags broken down by reference category
    assert result["recall"]["value"] == 0.0


def test_an_alert_on_a_negative_field_is_a_false_alert():
    result = combined(score((reference("7.7", "7.6"), output("7.1", "7.2"))))
    assert result["counts"]["false_alerts"] == 2
    assert result["precision"]["value"] == 0.0
    assert result["recall"]["value"] is None  # no positive fields


def test_an_alert_on_a_review_field_is_in_neither_precision_nor_recall():
    result = combined(score((reference("7.5", "7.7"), output("7.2", "7.7"))))
    counts = result["counts"]
    assert counts["alerts_on_review_fields"] == 1
    assert counts["detections"] == 0 and counts["false_alerts"] == 0 and counts["misses"] == 0
    assert result["precision"]["d"] == 0


def test_a_review_result_is_counted_separately_from_alerts_and_review_flags():
    result = combined(score((reference("7.1", "7.7"),
                             output("review: unresolved event date (§6.1)", "7.7"))))
    counts = result["counts"]
    assert counts["review_results"] == 1
    assert counts["misses"] == 1 and counts["misses_with_review_result"] == 1
    assert counts["misses_with_review_flag"] == 0 and counts["detections"] == 0


def test_out_of_scope_cases_are_scored_only_on_the_out_of_scope_flag():
    result = score(
        (reference("out of scope (age)", "out of scope (age)", out_of_scope="age under 18"),
         output("out of scope (age)", "out of scope (age)", out_of_scope="Age under 18")),
        # An in-scope case wrongly flagged out of scope: its positive field is a miss.
        (reference("7.1", "7.7"), output("out of scope (age)", "out of scope (age)", out_of_scope="age under 18")),
        oos=True)
    assert result["out_of_scope"]["reference_cases"] == 1
    assert result["out_of_scope"]["reason_matches"] == 1
    assert result["out_of_scope"]["in_scope_wrongly_flagged"] == 1
    counts = combined(result)["counts"]
    assert counts["fields"] == 2  # only the in-scope case's two fields
    assert counts["misses"] == 1 and counts["misses_from_out_of_scope"] == 1


def test_a_case_where_the_method_failed_counts_its_positive_fields_as_misses():
    result = score((reference("7.1", "7.7"), None))
    counts = combined(result)["counts"]
    assert counts["misses"] == 1 and counts["misses_from_errors"] == 1
    assert counts["fields"] == 2 and counts["agree_all"] == 0
    assert result["summary"]["errors"] == 1


def test_a_reference_category_with_a_reason_is_scored_by_its_code():
    result = combined(score((reference("7.5 (attribution)", "7.1 (late)"), output("7.5", "7.1"))))
    counts = result["counts"]
    assert counts["review"] == 1 and counts["detections"] == 1 and counts["unclassified"] == 0
    assert result["exact_agreement_all_fields"]["n"] == 2


def test_a_reference_category_outside_7_1_to_7_9_is_a_reference_error(tmp_path):
    import json
    from resauce.evaluate import read_reference
    (tmp_path / "intended").mkdir()
    answer = {"out_of_scope": None, "fields": {"onset": {"category": "7.5 (attribution)"},
                                               "max_grade": {"category": "unclear"}}}
    (tmp_path / "intended" / "C1.json").write_text(json.dumps(answer))
    try:
        read_reference(tmp_path, "C1")
    except ValueError as exc:
        assert "unclear" in str(exc)
    else:
        raise AssertionError("expected a reference error")
