"""Fill in start and end offsets for the evidence quotes in intended answers.

Usage (from the project folder):
    .venv/bin/python -m tools.fill_offsets                 # every answer file
    .venv/bin/python -m tools.fill_offsets reference/dev-v1/intended/SYN-0010.json

An evidence reference is any JSON object in the answer file that has the keys
document_id, version, quote, start and end (other keys, e.g. "role", are kept).
For each one, the quote is searched for in that exact document version. It
must occur exactly once; otherwise the author must lengthen the quote. If any
quote fails, the file is left unchanged. After filling, every reference is
checked with resauce.loader.check_evidence_ref.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resauce.loader import DataFormatError, check_evidence_ref, load_case
from resauce.models import Case, EvidenceRef

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dev-v1"
INTENDED = ROOT / "reference" / "dev-v1" / "intended"
REF_KEYS = ("document_id", "version", "quote", "start", "end")


def iter_evidence(node):
    """Yield every evidence-reference object inside a JSON structure."""
    if isinstance(node, dict):
        if all(key in node for key in REF_KEYS):
            yield node
        for value in node.values():
            yield from iter_evidence(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_evidence(item)


def to_evidence_ref(ref: dict) -> EvidenceRef:
    return EvidenceRef(ref["document_id"], ref["version"], ref["start"], ref["end"], ref["quote"])


def find_all(text: str, quote: str) -> list[int]:
    """Start positions of every occurrence of quote in text (overlaps counted)."""
    positions, start = [], text.find(quote)
    while start != -1:
        positions.append(start)
        start = text.find(quote, start + 1)
    return positions


def fill_answer(answer: dict, case: Case) -> list[str]:
    """Set start/end of every reference in answer (in place). Return problems."""
    problems = []
    for ref in iter_evidence(answer):
        name = f"{ref['document_id']}.v{ref['version']}"
        document = case.get_document_version(ref["document_id"], ref["version"])
        quote = ref["quote"]
        if document is None:
            problems.append(f"{name} does not exist in case {case.case_id} (quote {quote!r})")
            continue
        if not isinstance(quote, str) or not quote:
            problems.append(f"{name}: quote must be a non-empty string")
            continue
        found = find_all(document.text, quote)
        if len(found) != 1:
            problems.append(
                f"{name}: quote {quote!r} found {len(found)} times; it must occur "
                "exactly once (fix the quote, or lengthen it so it is unique)"
            )
            continue
        ref["start"], ref["end"] = found[0], found[0] + len(quote)
    return problems


def check_answer(answer: dict, case: Case) -> list[str]:
    """Check every reference with check_evidence_ref. Return problems."""
    problems = []
    for ref in iter_evidence(answer):
        try:
            check_evidence_ref(case, to_evidence_ref(ref))
        except DataFormatError as error:
            problems.extend(str(problem) for problem in error.problems)
    return problems


def fill_file(path: Path, data_dir: Path = DATA) -> list[str]:
    """Fill one answer file. Writes it only if every quote was found once."""
    answer = json.loads(path.read_text(encoding="utf-8"))
    case_dir = data_dir / "cases" / answer["case_id"]
    try:
        case = load_case(case_dir)
    except DataFormatError as error:
        return [f"case {answer['case_id']} does not load:\n{error}"]
    problems = fill_answer(answer, case)
    if problems:
        return problems
    problems = check_answer(answer, case)
    if not problems:
        path.write_text(json.dumps(answer, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path, help="answer files (default: all)")
    parser.add_argument("--data", type=Path, default=DATA, help="dataset folder")
    args = parser.parse_args(argv)
    files = args.files or sorted(INTENDED.glob("*.json"))
    failed = 0
    for path in files:
        problems = fill_file(path, args.data)
        if problems:
            failed += 1
            print(f"FAILED {path.name} (file not changed):")
            for problem in problems:
                print(f"  - {problem}")
        else:
            refs = len(list(iter_evidence(json.loads(path.read_text(encoding="utf-8")))))
            print(f"ok     {path.name}: {refs} evidence reference(s) filled and checked")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
