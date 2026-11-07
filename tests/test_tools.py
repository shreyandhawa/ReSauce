"""Tests for the case-authoring tools in tools/ (Milestone 2 Step 4)."""

import json
import shutil
from pathlib import Path

import pytest

from resauce.loader import load_case
from tools import check_dev, fill_offsets, make_briefs, show_case

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_CASE = Path(__file__).parent / "fixtures" / "format" / "valid_dataset" / "cases" / "SYN-0001"
DEV = ROOT / "data" / "dev-v1"
REFERENCE = ROOT / "reference" / "dev-v1"
PLAN_TEXT = (ROOT / "docs" / "dataset-plan.md").read_text(encoding="utf-8")

# Fixture text of SYN-0001-D01.v2:
# "Placeholder note text for format testing. Amended version."


def answer_with(quote):
    return {"case_id": "SYN-0001", "fields": {"onset": {"evidence": [
        {"role": "test", "document_id": "SYN-0001-D01", "version": 2, "quote": quote, "start": None, "end": None}
    ]}}}


# ---------------------------------------------------------------------------
# fill_offsets
# ---------------------------------------------------------------------------


def test_fill_offsets_one_match():
    case = load_case(FIXTURE_CASE)
    answer = answer_with("Amended version")
    assert fill_offsets.fill_answer(answer, case) == []
    ref = answer["fields"]["onset"]["evidence"][0]
    assert (ref["start"], ref["end"]) == (42, 57)
    assert fill_offsets.check_answer(answer, case) == []


def test_fill_offsets_no_match():
    case = load_case(FIXTURE_CASE)
    answer = answer_with("seizure")
    problems = fill_offsets.fill_answer(answer, case)
    assert len(problems) == 1 and "found 0 times" in problems[0]
    assert answer["fields"]["onset"]["evidence"][0]["start"] is None


def test_fill_offsets_several_matches():
    case = load_case(FIXTURE_CASE)
    problems = fill_offsets.fill_answer(answer_with("te"), case)
    assert len(problems) == 1 and "found 3 times" in problems[0] and "lengthen" in problems[0]


def test_fill_offsets_counts_overlapping_matches():
    assert fill_offsets.find_all("aaa", "aa") == [0, 1]


def test_fill_offsets_leaves_file_unchanged_on_failure(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(FIXTURE_CASE, data / "cases" / "SYN-0001")
    path = tmp_path / "SYN-0001.json"
    original = json.dumps(answer_with("not in the text"), indent=2) + "\n"
    path.write_text(original, encoding="utf-8")
    assert fill_offsets.fill_file(path, data)
    assert path.read_text(encoding="utf-8") == original


def test_fill_offsets_writes_file_on_success(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(FIXTURE_CASE, data / "cases" / "SYN-0001")
    path = tmp_path / "SYN-0001.json"
    path.write_text(json.dumps(answer_with("Amended version")), encoding="utf-8")
    assert fill_offsets.fill_file(path, data) == []
    ref = json.loads(path.read_text(encoding="utf-8"))["fields"]["onset"]["evidence"][0]
    assert (ref["start"], ref["end"]) == (42, 57)


# ---------------------------------------------------------------------------
# make_briefs
# ---------------------------------------------------------------------------


def test_make_briefs_is_deterministic():
    assert make_briefs.build(PLAN_TEXT) == make_briefs.build(PLAN_TEXT)


def test_make_briefs_seed_matters():
    assert make_briefs.build(PLAN_TEXT, seed=1)[1]["briefs"] != make_briefs.build(PLAN_TEXT)[1]["briefs"]


def test_stored_briefs_match_a_fresh_run():
    # The plan fingerprint is left out: briefs.json records the plan version it
    # was made from (v0.3). Later plan edits that keep the scenario table
    # (e.g. v0.3.1) change the fingerprint but not a single brief.
    ordering, briefs = make_briefs.build(PLAN_TEXT)
    stored_briefs = json.loads((REFERENCE / "briefs.json").read_text(encoding="utf-8"))
    stored_ordering = json.loads((REFERENCE / "ordering.json").read_text(encoding="utf-8"))
    for data in (briefs, stored_briefs):
        data.pop("dataset_plan")
    assert stored_briefs == briefs
    assert stored_ordering["id_to_scenario"] == ordering["id_to_scenario"]
    assert stored_ordering["input_order"] == ordering["input_order"]


def test_plan_scenario_rows_match_the_stored_briefs():
    stored = json.loads((REFERENCE / "briefs.json").read_text(encoding="utf-8"))["briefs"]
    keys = ("scenario_id", "scenario", "rules", "expected_onset", "expected_grade", "type", "plain", "no_icans")
    from_briefs = sorted(({k: b[k] for k in keys} for b in stored), key=lambda s: int(s["scenario_id"][3:]))
    from_plan = [{k: s[k] for k in keys} for s in make_briefs.read_scenarios(PLAN_TEXT)]
    assert from_plan == from_briefs


def test_plan_has_72_scenarios_with_the_planned_types():
    scenarios = make_briefs.read_scenarios(PLAN_TEXT)
    assert [s["scenario_id"] for s in scenarios] == [f"SC-{i:02d}" for i in range(1, 73)]
    types = [s["type"] for s in scenarios]
    assert (types.count("Pos"), types.count("Neg"), types.count("Flag"), types.count("OOS")) == (28, 24, 16, 4)


def test_briefs_respect_forced_and_forbidden_features():
    ordering, result = make_briefs.build(PLAN_TEXT)
    briefs = {b["scenario_id"]: b for b in result["briefs"]}
    assert sorted(b["case_id"] for b in briefs.values()) == [f"SYN-{i:04d}" for i in range(1, 73)]
    assert briefs["SC-54"]["age_at_infusion"] < 18
    assert all(18 <= b["age_at_infusion"] <= 85 for sc, b in briefs.items() if sc != "SC-54")
    assert all(3 <= b["documents"] <= 12 for b in briefs.values())
    assert briefs["SC-57"]["writing_style"] == "templated"
    for sc in make_briefs.FORCED_AMENDED:
        assert briefs[sc]["amended_note"] == "scenario"
    for sc in make_briefs.FORCED_MULTI_RECORD:
        assert briefs[sc]["multi_version_record"]["source"] == "scenario"
    for sc, b in briefs.items():
        if b["type"] == "OOS" or sc == "SC-60":
            assert b["out_of_window_document"] is False
        if sc in make_briefs.NO_NORMAL_REPORT:
            assert b["normal_report_distractor"] is None
        if b["not_assessable_period"]:
            assert sc in make_briefs.FORCED_NOT_ASSESSABLE or (
                b["type"] in ("Pos", "Neg") and not b["no_icans"])
        assert (b["death"] != "forbidden") == (sc == "SC-69")
        assert (b["ungradeable_symptom"] == "required") == (sc in make_briefs.UNGRADEABLE_SYMPTOM)
        record = b["multi_version_record"]
        if record and record["source"] == "random" and b["no_icans"]:
            assert record["pattern"] == "same values re-entered"
    totals = result["totals"]
    assert totals["out_of_window_document"] == 7
    assert 0.15 <= totals["amended_note"] / 72 <= 0.25
    assert totals["not_assessable_period"] == 5


# ---------------------------------------------------------------------------
# check_dev
# ---------------------------------------------------------------------------


def errors(sections):
    return [message for _, lines in sections for level, message in lines if level == check_dev.ERROR]


def test_check_dev_passes_on_the_development_set():
    sections = check_dev.run_checks(DEV, REFERENCE)
    assert errors(sections) == []


def test_check_dev_flags_a_banned_word_but_only_warns_on_a_lab_value(tmp_path):
    data = tmp_path / "dev-v1"
    shutil.copytree(DEV, data)
    note = next((data / "cases").glob("*/documents/*.json"))
    content = json.loads(note.read_text(encoding="utf-8"))
    content["text"] += "\nScenario note. ABG pH 7.4."
    note.write_text(json.dumps(content, indent=2), encoding="utf-8")
    lines = check_dev._check_leakage(data)
    assert any(level == check_dev.ERROR and "scenario" in message for level, message in lines)
    assert any(level == check_dev.WARNING and "7.4" in message for level, message in lines)
    assert not any(level == check_dev.ERROR and "7.4" in message for level, message in lines)


# ---------------------------------------------------------------------------
# show_case
# ---------------------------------------------------------------------------


def test_show_case_prints_documents_in_time_order_without_answers():
    case = load_case(DEV / "cases" / "SYN-0043")
    text = show_case.render(case)
    assert "SC-" not in text
    assert "intended" not in text.lower()
    # D02 was documented after midnight, before D03 the same morning.
    assert text.index("SYN-0043-D01.v1") < text.index("SYN-0043-D02.v1") < text.index("SYN-0043-D03.v1")
    assert "RESEARCH RECORD SYN-0043-R" in text


# ---------------------------------------------------------------------------
# The pipeline core stays separate from tools/ and reference/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", sorted((ROOT / "src" / "resauce").glob("*.py")), ids=lambda p: p.name)
def test_core_does_not_use_tools_or_reference(path):
    source = path.read_text(encoding="utf-8")
    assert "import tools" not in source and "from tools" not in source
    assert "reference/" not in source and '"reference"' not in source
