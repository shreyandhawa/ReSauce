"""Tests for the synthetic data loader (docs/data-format.md).

Invalid inputs are made by copying the valid fixture into pytest's tmp_path
and changing one thing, so only one valid fixture needs to be maintained.
"""

import json
import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from resauce.loader import (
    DataFormatError,
    check_evidence_ref,
    load_case,
    load_dataset,
    study_day,
)
from resauce.models import EvidenceRef

FIXTURE = Path(__file__).parent / "fixtures" / "format" / "valid_dataset"

DATASET = "dataset.json"
CASE1 = "cases/SYN-0001"
CASE1_JSON = f"{CASE1}/case.json"
RECORD1 = f"{CASE1}/record.json"
DOCS1 = f"{CASE1}/documents"
D01V1 = f"{DOCS1}/SYN-0001-D01.v1.json"
D01V2 = f"{DOCS1}/SYN-0001-D01.v2.json"
D02V1 = f"{DOCS1}/SYN-0001-D02.v1.json"
CASE2 = "cases/SYN-0002"
RECORD2 = f"{CASE2}/record.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def dataset_dir(tmp_path):
    """A fresh, editable copy of the valid fixture."""
    target = tmp_path / "valid_dataset"
    shutil.copytree(FIXTURE, target)
    return target


def edit_json(path, change):
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def set_field(key, value):
    def change(data):
        data[key] = value

    return change


def delete_field(key):
    def change(data):
        del data[key]

    return change


def set_record_field(index, key, value):
    def change(data):
        data["versions"][index][key] = value

    return change


def problems_of(dataset_dir):
    with pytest.raises(DataFormatError) as info:
        load_dataset(dataset_dir)
    return info.value.problems


def find(problems, source, field, words):
    """Return problems from the given file and field whose message has words."""
    return [
        p
        for p in problems
        if p.source == str(source) and p.field == field and words in p.message
    ]


# ---------------------------------------------------------------------------
# Valid fixture
# ---------------------------------------------------------------------------


def test_valid_dataset_loads():
    dataset = load_dataset(FIXTURE)
    assert dataset.dataset_id == "SYN-DS-FORMAT-TEST"
    assert dataset.dataset_version == "0.1.0"
    assert dataset.observation_window.start_day == 0
    assert dataset.observation_window.end_day == 28


def test_cases_and_documents_are_in_deterministic_order():
    dataset = load_dataset(FIXTURE)
    assert [case.case_id for case in dataset.cases] == ["SYN-0001", "SYN-0002"]
    assert [d.version_id for d in dataset.cases[0].documents] == [
        "SYN-0001-D01.v1",
        "SYN-0001-D01.v2",
        "SYN-0001-D02.v1",
    ]


def test_loading_twice_gives_equal_results():
    assert load_dataset(FIXTURE) == load_dataset(FIXTURE)


def test_both_amendment_versions_are_kept():
    case = load_case(FIXTURE / CASE1)
    v1 = case.get_document_version("SYN-0001-D01", 1)
    v2 = case.get_document_version("SYN-0001-D01", 2)
    assert v1 is not None and v2 is not None
    assert v1.text == "Placeholder note text for format testing."
    assert v2.text == "Placeholder note text for format testing. Amended version."
    assert v1.amendment_reason is None
    assert v2.amendment_reason == "Placeholder amendment reason for format testing."
    assert v2.version_id == "SYN-0001-D01.v2"
    assert case.get_document_version("SYN-0001-D01", 3) is None


def test_document_fields_are_parsed():
    case = load_case(FIXTURE / CASE1)
    document = case.get_document_version("SYN-0001-D02", 1)
    assert document.case_id == "SYN-0001"
    assert document.status == "unsigned"
    assert document.note_type == "nursing_note"
    assert document.author_role == "nurse"
    assert document.documented_at == datetime(2030, 3, 5, 22, 40)
    # Text is returned exactly as written, including the line break.
    assert document.text == "Placeholder note text for format testing.\nSecond placeholder line."


def test_record_history_and_current_version():
    case = load_case(FIXTURE / CASE1)
    record = case.record
    assert record.record_id == "SYN-0001-R"
    assert [v.version for v in record.versions] == [1, 2]
    assert record.versions[0].max_grade == 2
    assert record.versions[0].change_reason is None
    assert record.current.version == 2
    assert record.current.max_grade == 3
    assert record.current.recorded_at == datetime(2030, 3, 12, 16, 30)
    assert record.current.onset_date == date(2030, 3, 4)
    assert record.current.change_reason == "Placeholder change reason for format testing."


def test_case_fields_and_case_without_documents_folder():
    case = load_case(FIXTURE / CASE2)
    assert not (FIXTURE / CASE2 / "documents").exists()
    assert case.case_id == "SYN-0002"
    assert case.age_at_infusion == 58
    assert case.infusion_date == date(2030, 6, 15)
    assert case.documents == ()
    current = case.record.current
    assert current.icans_reported is False
    assert current.onset_date is None
    assert current.max_grade is None


def test_study_day():
    case = load_case(FIXTURE / CASE1)  # infusion date 2030-03-01
    assert study_day(case, date(2030, 3, 1)) == 0
    assert study_day(case, date(2030, 3, 7)) == 6
    assert study_day(case, datetime(2030, 3, 7, 23, 59)) == 6
    assert study_day(case, date(2030, 2, 27)) == -2
    assert study_day(case, date(2030, 4, 1)) == 31  # crosses a month boundary


def test_study_day_rejects_other_types():
    case = load_case(FIXTURE / CASE1)
    with pytest.raises(TypeError):
        study_day(case, "2030-03-07")


def test_valid_evidence_reference_passes():
    case = load_case(FIXTURE / CASE1)
    ref = EvidenceRef("SYN-0001-D01", 2, 42, 57, "Amended version")
    assert check_evidence_ref(case, ref) is None


def test_hidden_files_are_ignored(dataset_dir):
    (dataset_dir / "cases" / ".DS_Store").write_bytes(b"\x00")
    (dataset_dir / DOCS1 / ".DS_Store").write_bytes(b"\x00")
    assert len(load_dataset(dataset_dir).cases) == 2


# ---------------------------------------------------------------------------
# Single-problem rejections
# ---------------------------------------------------------------------------

SINGLE_PROBLEM_CASES = [
    # (test id, file, change, expected field, words expected in the message)
    ("synthetic missing", CASE1_JSON, delete_field("synthetic"), "synthetic", "missing"),
    ("synthetic false", D01V1, set_field("synthetic", False), "synthetic", "JSON boolean true"),
    ("synthetic string", RECORD1, set_field("synthetic", "true"), "synthetic", 'the string "true"'),
    ("synthetic number", DATASET, set_field("synthetic", 1), "synthetic", "JSON boolean true"),
    ("notice wrong", DATASET, set_field("fictional_notice", "Fictional data."), "fictional_notice", "must be exactly"),
    ("notice missing", D02V1, delete_field("fictional_notice"), "fictional_notice", "missing"),
    ("schema version wrong", CASE1_JSON, set_field("schema_version", "0.2"), "schema_version", '"0.1"'),
    ("unknown field", CASE1_JSON, set_field("infusion_dat", "2030-03-01"), "infusion_dat", "unknown field"),
    ("case_id not folder", CASE1_JSON, set_field("case_id", "SYN-0009"), "case_id", "folder name"),
    ("document case_id", D02V1, set_field("case_id", "SYN-0002"), "case_id", "folder name"),
    ("record case_id", RECORD1, set_field("case_id", "SYN-0002"), "case_id", "folder name"),
    ("record_id wrong", RECORD1, set_field("record_id", "SYN-0001"), "record_id", '"SYN-0001-R"'),
    ("malformed date", CASE1_JSON, set_field("infusion_date", "01/03/2030"), "infusion_date", "YYYY-MM-DD"),
    ("impossible date", CASE1_JSON, set_field("infusion_date", "2030-02-30"), "infusion_date", "real calendar date"),
    ("timestamp timezone", D01V1, set_field("documented_at", "2030-03-03T09:15+01:00"), "documented_at", "no timezone"),
    ("timestamp seconds", D01V1, set_field("documented_at", "2030-03-03T09:15:00"), "documented_at", "no seconds"),
    ("age too high", CASE1_JSON, set_field("age_at_infusion", 121), "age_at_infusion", "between 0 and 120"),
    ("age as string", CASE1_JSON, set_field("age_at_infusion", "64"), "age_at_infusion", "whole number"),
    ("text with CR", D02V1, set_field("text", "Line one.\r\nLine two."), "text", "carriage-return"),
    ("empty text", D02V1, set_field("text", ""), "text", "must not be empty"),
    ("note_type unknown", D02V1, set_field("note_type", "progress_note"), "note_type", "must be one of"),
    ("status unknown", D02V1, set_field("status", "final"), "status", "must be one of"),
    ("author_role unknown", D02V1, set_field("author_role", "chief"), "author_role", "must be one of"),
    ("version is boolean", D02V1, set_field("version", True), "version", "the boolean true"),
    ("amendment on v1", D01V1, set_field("amendment_reason", "Something."), "amendment_reason", "null for version 1"),
    ("max_grade 6", RECORD1, set_record_field(1, "max_grade", 6), "versions[1].max_grade", "between 1 and 5"),
    ("max_grade boolean", RECORD1, set_record_field(1, "max_grade", True), "versions[1].max_grade", "the boolean true"),
    ("max_grade 0", RECORD1, set_record_field(1, "max_grade", 0), "versions[1].max_grade", "between 1 and 5"),
    ("icans false with grade", RECORD2, set_record_field(0, "max_grade", 2), "versions[0].max_grade", "icans_reported is false"),
    ("icans false with onset", RECORD2, set_record_field(0, "onset_date", "2030-06-20"), "versions[0].onset_date", "icans_reported is false"),
    ("icans_reported string", RECORD2, set_record_field(0, "icans_reported", "false"), "versions[0].icans_reported", "true or false"),
    ("record out of time order", RECORD1, set_record_field(1, "recorded_at", "2030-03-09T10:00"), "versions[1].recorded_at", "strictly increasing"),
    ("record same time", RECORD1, set_record_field(1, "recorded_at", "2030-03-10T10:00"), "versions[1].recorded_at", "strictly increasing"),
    ("record version number", RECORD1, set_record_field(1, "version", 3), "versions[1].version", "must be 2"),
    ("change reason on v1", RECORD1, set_record_field(0, "change_reason", "Something."), "versions[0].change_reason", "null for version 1"),
    ("record unknown field", RECORD1, set_record_field(0, "grade", 2), "versions[0].grade", "unknown field"),
    ("record versions empty", RECORD1, set_field("versions", []), "versions", "non-empty list"),
    ("dataset_id prefix", DATASET, set_field("dataset_id", "DS-FORMAT-TEST"), "dataset_id", '"SYN-DS-"'),
    ("window reversed", DATASET, set_field("observation_window", {"start_day": 10, "end_day": 5}), "observation_window.end_day", "must not be smaller"),
    ("window negative", DATASET, set_field("observation_window", {"start_day": -1, "end_day": 5}), "observation_window.start_day", "0 or greater"),
]


@pytest.mark.parametrize(
    ("relative", "change", "field", "words"),
    [case[1:] for case in SINGLE_PROBLEM_CASES],
    ids=[case[0] for case in SINGLE_PROBLEM_CASES],
)
def test_single_problem_is_rejected(dataset_dir, relative, change, field, words):
    path = dataset_dir / relative
    edit_json(path, change)
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, path, field, words), problems


# ---------------------------------------------------------------------------
# Rejections that need more than one field edit, or produce several problems
# ---------------------------------------------------------------------------


def test_case_id_without_syn_prefix(dataset_dir):
    path = dataset_dir / CASE1_JSON
    edit_json(path, set_field("case_id", "ABC-0001"))
    problems = problems_of(dataset_dir)
    assert find(problems, path, "case_id", '"SYN-" followed by exactly four digits')
    assert find(problems, path, "case_id", "folder name")


def test_document_version_gap(dataset_dir):
    old = dataset_dir / D01V2
    new = dataset_dir / DOCS1 / "SYN-0001-D01.v3.json"
    old.rename(new)
    edit_json(new, set_field("version", 3))
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, dataset_dir / DOCS1, "version", "missing version(s): 2")


def test_document_with_only_version_2(dataset_dir):
    (dataset_dir / D01V1).unlink()
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, dataset_dir / DOCS1, "version", "missing version(s): 1")


def test_duplicate_document_version(dataset_dir):
    path = dataset_dir / D01V2
    edit_json(path, set_field("version", 1))
    edit_json(path, set_field("amendment_reason", None))
    problems = problems_of(dataset_dir)
    assert len(problems) == 2, problems
    assert find(problems, dataset_dir / DOCS1, "version", "version 1 of SYN-0001-D01 appears in more than one file")
    assert find(problems, path, "(file name)", '"SYN-0001-D01.v1.json"')


def test_file_name_not_matching_document_id(dataset_dir):
    old = dataset_dir / D02V1
    new = dataset_dir / DOCS1 / "SYN-0001-D03.v1.json"
    old.rename(new)
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, new, "(file name)", 'must be "SYN-0001-D02.v1.json"')


def test_documented_at_decreasing_across_versions(dataset_dir):
    path = dataset_dir / D01V2
    edit_json(path, set_field("documented_at", "2030-03-02T08:00"))
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, path, "documented_at", "must not decrease")


def test_unexpected_file_in_documents_folder(dataset_dir):
    path = dataset_dir / DOCS1 / "notes.txt"
    path.write_text("x", encoding="utf-8")
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, path, "(file name)", "unexpected item")


@pytest.mark.parametrize("missing", [RECORD1, CASE1_JSON, DATASET])
def test_required_file_missing(dataset_dir, missing):
    path = dataset_dir / missing
    path.unlink()
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, path, "(file)", "required file is missing")


def test_duplicate_json_key(dataset_dir):
    path = dataset_dir / CASE1_JSON
    text = path.read_text(encoding="utf-8")
    text = text.replace('"age_at_infusion"', '"case_id": "SYN-0001",\n  "age_at_infusion"', 1)
    path.write_text(text, encoding="utf-8")
    problems = problems_of(dataset_dir)
    assert len(problems) == 1, problems
    assert find(problems, path, "case_id", "more than once")


def test_invalid_json_syntax_names_the_file(dataset_dir):
    path = dataset_dir / D01V1
    path.write_text('{"case_id": "SYN-0001",', encoding="utf-8")
    with pytest.raises(DataFormatError) as info:
        load_dataset(dataset_dir)
    problems = info.value.problems
    assert len(problems) == 1, problems
    assert find(problems, path, "(file)", "invalid JSON syntax at line 1")
    assert str(path) in str(info.value)


def test_file_not_utf8(dataset_dir):
    path = dataset_dir / CASE1_JSON
    path.write_bytes(b'{"case_id": "SYN-\xff"}')
    problems = problems_of(dataset_dir)
    assert find(problems, path, "(file)", "not valid UTF-8")


def test_nan_is_rejected(dataset_dir):
    path = dataset_dir / CASE1_JSON
    text = path.read_text(encoding="utf-8").replace("64", "NaN")
    path.write_text(text, encoding="utf-8")
    problems = problems_of(dataset_dir)
    assert find(problems, path, "(file)", "NaN")


def test_top_level_must_be_object(dataset_dir):
    path = dataset_dir / CASE1_JSON
    path.write_text("[]", encoding="utf-8")
    problems = problems_of(dataset_dir)
    assert find(problems, path, "(file)", "JSON object at the top level")


# ---------------------------------------------------------------------------
# Several problems reported together
# ---------------------------------------------------------------------------


def test_all_problems_in_one_case_are_reported_together(dataset_dir):
    case_folder = dataset_dir / CASE1
    edit_json(dataset_dir / CASE1_JSON, set_field("infusion_date", "2030/03/01"))
    edit_json(dataset_dir / RECORD1, set_record_field(1, "max_grade", 6))
    edit_json(dataset_dir / D02V1, set_field("note_type", "unknown_type"))

    with pytest.raises(DataFormatError) as info:
        load_case(case_folder)
    error = info.value
    assert len(error.problems) == 3, error.problems
    assert find(error.problems, dataset_dir / CASE1_JSON, "infusion_date", "YYYY-MM-DD")
    assert find(error.problems, dataset_dir / RECORD1, "versions[1].max_grade", "between 1 and 5")
    assert find(error.problems, dataset_dir / D02V1, "note_type", "must be one of")

    message = str(error)
    assert message.startswith("3 data format problem(s) found:")
    for path in (CASE1_JSON, RECORD1, D02V1):
        assert str(dataset_dir / path) in message


def test_problems_in_different_cases_are_reported_together(dataset_dir):
    edit_json(dataset_dir / CASE1_JSON, delete_field("synthetic"))
    edit_json(dataset_dir / RECORD2, set_record_field(0, "max_grade", 1))
    problems = problems_of(dataset_dir)
    assert len(problems) == 2, problems
    assert find(problems, dataset_dir / CASE1_JSON, "synthetic", "missing")
    assert find(problems, dataset_dir / RECORD2, "versions[0].max_grade", "icans_reported is false")


# ---------------------------------------------------------------------------
# Evidence references
# ---------------------------------------------------------------------------


@pytest.fixture
def case1():
    return load_case(FIXTURE / CASE1)


def evidence_problems(case, ref):
    with pytest.raises(DataFormatError) as info:
        check_evidence_ref(case, ref)
    return info.value.problems


def test_evidence_quote_mismatch(case1):
    ref = EvidenceRef("SYN-0001-D01", 1, 0, 11, "placeholder")  # wrong case
    problems = evidence_problems(case1, ref)
    assert len(problems) == 1
    assert problems[0].field == "quote"
    assert "does not match" in problems[0].message


def test_evidence_end_out_of_range(case1):
    text = case1.get_document_version("SYN-0001-D01", 1).text
    ref = EvidenceRef("SYN-0001-D01", 1, 0, len(text) + 1, text)
    problems = evidence_problems(case1, ref)
    assert len(problems) == 1
    assert "out of range" in problems[0].message


def test_evidence_negative_start(case1):
    ref = EvidenceRef("SYN-0001-D01", 1, -1, 5, "Place")
    problems = evidence_problems(case1, ref)
    assert "out of range" in problems[0].message


def test_evidence_start_not_before_end(case1):
    ref = EvidenceRef("SYN-0001-D01", 1, 5, 5, "")
    problems = evidence_problems(case1, ref)
    assert len(problems) == 1
    assert "must be smaller than end" in problems[0].message


def test_evidence_unknown_document_version(case1):
    ref = EvidenceRef("SYN-0001-D01", 3, 0, 11, "Placeholder")
    problems = evidence_problems(case1, ref)
    assert len(problems) == 1
    assert "does not exist" in problems[0].message


def test_evidence_offsets_must_be_whole_numbers(case1):
    ref = EvidenceRef("SYN-0001-D01", 1, True, 11, "Placeholder")
    problems = evidence_problems(case1, ref)
    assert problems[0].field == "start"
    assert "whole number" in problems[0].message
