"""Check the development set and print a plain-language report.

Usage (from the project folder):
    .venv/bin/python -m tools.check_dev

Checks (dataset-plan.md §9):
  1. data/dev-v1 loads with load_dataset (check 1, and check 11 via the loader).
  2. Every intended-answer evidence reference passes check_evidence_ref (check 3),
     and each answer's case ID and scenario ID agree with ordering.json.
  3. Every document version and record version from 2 onward has a reason (check 14).
  4. No answer leakage in data/dev-v1 (check 6): banned words and "SC-" + digit
     are errors; category numbers 7.1-7.8 are warnings for a person to review
     (lab values such as "pH 7.4" are realistic).
  5. Which briefs have a case; every case has an intended answer and vice versa
     (check 2). Missing cases are listed, not errors, while Step 4 is in progress.
  6. Each written case matches its brief (age, infusion date, number of
     documents, out-of-window document, amendment, unsigned version, record
     versions, normal report).
Exit code 1 if any ERROR was found.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from resauce.loader import DataFormatError, check_evidence_ref, load_dataset, study_day
from tools.fill_offsets import iter_evidence, to_evidence_ref

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dev-v1"
REFERENCE = ROOT / "reference" / "dev-v1"

# Leakage: anything here in data/ is an ERROR. Extend freely (lower case).
BANNED_WORDS = [
    "scenario", "intended", "discrepancy", "mismatch", "edge case", "distractor",
    "ground truth", "answer key", "insufficient evidence", "ambiguous evidence",
    "legitimate revision", "out of scope",
]
BANNED_PATTERNS = [re.compile(r"SC-[0-9]", re.IGNORECASE)]
# Category numbers: a WARNING only (a person decides).
CATEGORY_NUMBER = re.compile(r"(?<![0-9.])7\.[1-8](?![0-9])")

ERROR, WARNING, OK, INFO = "ERROR", "WARNING", "ok", "info"


def run_checks(data_dir: Path = DATA, reference_dir: Path = REFERENCE) -> list[tuple[str, list[tuple[str, str]]]]:
    """Run every check. Return [(section title, [(level, message), ...]), ...]."""
    sections = []
    dataset, lines = _check_loads(data_dir)
    sections.append(("1. Dataset loads", lines))
    cases = {case.case_id: case for case in dataset.cases} if dataset else {}
    ordering = json.loads((reference_dir / "ordering.json").read_text(encoding="utf-8"))
    briefs = json.loads((reference_dir / "briefs.json").read_text(encoding="utf-8"))["briefs"]
    answers = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((reference_dir / "intended").glob("*.json"))}
    sections.append(("2. Intended-answer evidence references", _check_answers(answers, cases, ordering)))
    sections.append(("3. Reasons on later versions", _check_reasons(cases)))
    sections.append(("4. Answer leakage in data/", _check_leakage(data_dir)))
    sections.append(("5. Briefs, cases and answers", _check_coverage(briefs, cases, answers, data_dir)))
    sections.append(("6. Cases match their briefs", _check_briefs(briefs, cases, dataset)))
    return sections


def _check_loads(data_dir):
    try:
        dataset = load_dataset(data_dir)
    except DataFormatError as error:
        return None, [(ERROR, str(problem)) for problem in error.problems]
    return dataset, [(OK, f"{dataset.dataset_id} version {dataset.dataset_version} loads: {len(dataset.cases)} case(s)")]


def _check_answers(answers, cases, ordering):
    lines, total = [], 0
    for case_id, answer in answers.items():
        if answer.get("case_id") != case_id:
            lines.append((ERROR, f"{case_id}.json: case_id inside the file is {answer.get('case_id')!r}"))
        expected = ordering["id_to_scenario"].get(case_id)
        if answer.get("scenario_id") != expected:
            lines.append((ERROR, f"{case_id}: scenario_id {answer.get('scenario_id')!r}, ordering.json says {expected!r}"))
        case = cases.get(case_id)
        if case is None:
            continue  # reported in section 5
        for ref in iter_evidence(answer):
            total += 1
            if type(ref["start"]) is not int or type(ref["end"]) is not int:
                lines.append((ERROR, f"{case_id}: quote {ref['quote']!r} has no offsets; run tools.fill_offsets"))
                continue
            try:
                check_evidence_ref(case, to_evidence_ref(ref))
            except DataFormatError as error:
                lines += [(ERROR, f"{case_id}: {problem}") for problem in error.problems]
    if not any(level == ERROR for level, _ in lines):
        lines.append((OK, f"{total} evidence reference(s) in {len(answers)} answer file(s) all match the text"))
    return lines


def _check_reasons(cases):
    lines = []
    for case in cases.values():
        for doc in case.documents:
            if doc.version >= 2 and doc.amendment_reason is None:
                lines.append((ERROR, f"{doc.version_id}: version {doc.version} has no amendment_reason"))
        for version in case.record.versions[1:]:
            if version.change_reason is None:
                lines.append((ERROR, f"{case.case_id} record version {version.version} has no change_reason"))
    return lines or [(OK, "every later document and record version gives a reason")]


def _check_leakage(data_dir):
    lines = []
    for path in sorted(p for p in data_dir.rglob("*") if p.is_file() and not p.name.startswith(".")):
        rel = path.relative_to(data_dir)
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            for word in BANNED_WORDS:
                if word in low:
                    lines.append((ERROR, f"{rel} line {number}: banned word {word!r}"))
            for pattern in BANNED_PATTERNS:
                for match in pattern.finditer(line):
                    lines.append((ERROR, f"{rel} line {number}: banned text {match.group(0)!r}"))
            for match in CATEGORY_NUMBER.finditer(line):
                context = line[max(0, match.start() - 30) : match.end() + 30].strip()
                lines.append((WARNING, f"{rel} line {number}: category-like number {match.group(0)!r} in ...{context}... (review)"))
    return lines or [(OK, "no banned words, no scenario IDs, no category-like numbers")]


def _check_coverage(briefs, cases, answers, data_dir):
    lines = []
    written = [b for b in briefs if b["case_id"] in cases]
    missing = [b["case_id"] for b in briefs if b["case_id"] not in cases]
    lines.append((OK, f"{len(written)} of {len(briefs)} briefs have a case"))
    if missing:
        lines.append((INFO, f"{len(missing)} case(s) not written yet: {_compact(missing)}"))
    for case_id in cases:
        if case_id not in answers:
            lines.append((ERROR, f"{case_id} has a case folder but no intended answer"))
    for case_id in answers:
        if case_id not in cases and not (data_dir / "cases" / case_id).exists():
            lines.append((ERROR, f"intended answer {case_id}.json has no case folder"))
    return lines


def _check_briefs(briefs, cases, dataset):
    lines = []
    if dataset is None:
        return [(INFO, "skipped: the dataset does not load")]
    window = dataset.observation_window
    for brief in briefs:
        case = cases.get(brief["case_id"])
        if case is None:
            continue
        cid, problems = case.case_id, []
        doc_ids = {d.document_id for d in case.documents}
        by_doc = {i: [d for d in case.documents if d.document_id == i] for i in doc_ids}
        if case.age_at_infusion != brief["age_at_infusion"]:
            problems.append(f"age {case.age_at_infusion}, brief says {brief['age_at_infusion']}")
        if case.infusion_date.isoformat() != brief["infusion_date"]:
            problems.append(f"infusion date {case.infusion_date}, brief says {brief['infusion_date']}")
        if len(doc_ids) != brief["documents"]:
            problems.append(f"{len(doc_ids)} documents, brief says {brief['documents']}")
        outside = any(not window.start_day <= study_day(case, d.documented_at) <= window.end_day for d in case.documents)
        if outside != brief["out_of_window_document"]:
            problems.append(f"out-of-window document present: {outside}, brief says {brief['out_of_window_document']}")
        amended = any(len(v) > 1 for v in by_doc.values())
        if amended != bool(brief["amended_note"]):
            problems.append(f"amended note present: {amended}, brief says {brief['amended_note']}")
        unsigned = any(d.status == "unsigned" for d in case.documents)
        if unsigned != bool(brief["unsigned_version"]):
            problems.append(f"unsigned version present: {unsigned}, brief says {brief['unsigned_version']}")
        multi = len(case.record.versions) > 1
        if multi != bool(brief["multi_version_record"]):
            problems.append(f"multi-version record: {multi}, brief says {brief['multi_version_record']}")
        report = {"eeg": "eeg_report", "imaging": "imaging_report"}.get(brief["normal_report_distractor"])
        if report and not any(d.note_type == report for d in case.documents):
            problems.append(f"brief asks for a normal {report}, none found")
        lines += [(ERROR, f"{cid}: {p}") for p in problems]
        if not problems:
            lines.append((OK, f"{cid} matches its brief"))
    return lines or [(INFO, "no cases written yet")]


def _compact(ids: list[str]) -> str:
    return ", ".join(ids) if len(ids) <= 12 else ", ".join(ids[:12]) + f", ... (+{len(ids) - 12} more)"


def main() -> int:
    sections = run_checks()
    counts = {ERROR: 0, WARNING: 0}
    print("ReSauce development set check (tools/check_dev.py)\n")
    for title, lines in sections:
        print(title)
        for level, message in lines:
            counts[level] = counts.get(level, 0) + 1
            print(f"  [{level}] {message}")
        print()
    print(f"Summary: {counts[ERROR]} error(s), {counts[WARNING]} warning(s) for review.")
    print("Result: " + ("FAILED" if counts[ERROR] else "PASSED"))
    return 1 if counts[ERROR] else 0


if __name__ == "__main__":
    sys.exit(main())
