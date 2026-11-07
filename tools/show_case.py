"""Print one case as plain readable text (for the readability check, plan §9 check 10).

Usage (from the project folder):
    .venv/bin/python -m tools.show_case SYN-0010

Prints the case details, then every document version in order of
documentation time, then the research record versions. It reads only the case
folder in data/, so it never shows intended answers or scenario labels.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from resauce.loader import DataFormatError, load_case, study_day
from resauce.models import Case

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dev-v1"


def _day(case: Case, when) -> str:
    return f"Day {study_day(case, when):+d}"


def render(case: Case) -> str:
    out = [
        f"CASE {case.case_id}",
        f"Age at infusion: {case.age_at_infusion}",
        f"Infusion date (Day 0): {case.infusion_date.isoformat()}",
        f"Documents: {len({d.document_id for d in case.documents})} "
        f"({len(case.documents)} version(s))",
        "",
    ]
    for doc in sorted(case.documents, key=lambda d: (d.documented_at, d.document_id, d.version)):
        out.append("=" * 78)
        out.append(
            f"{doc.version_id} | {doc.status} | {doc.note_type} | {doc.author_role}"
        )
        out.append(
            f"Documented {doc.documented_at.strftime('%Y-%m-%d %H:%M')} "
            f"({_day(case, doc.documented_at)})"
        )
        if doc.amendment_reason is not None:
            out.append(f"Amendment reason: {doc.amendment_reason}")
        out.append("-" * 78)
        out.append(doc.text)
        out.append("")
    out.append("=" * 78)
    out.append(f"RESEARCH RECORD {case.record.record_id}")
    for v in case.record.versions:
        onset = (
            f"{v.onset_date.isoformat()} ({_day(case, v.onset_date)})"
            if v.onset_date
            else "empty"
        )
        grade = v.max_grade if v.max_grade is not None else "empty"
        out.append(
            f"  v{v.version} recorded {v.recorded_at.strftime('%Y-%m-%d %H:%M')} "
            f"({_day(case, v.recorded_at)}): ICANS reported: "
            f"{'yes' if v.icans_reported else 'no'}; onset: {onset}; max grade: {grade}"
        )
        if v.change_reason is not None:
            out.append(f"      change reason: {v.change_reason}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("case_id", help="e.g. SYN-0010")
    parser.add_argument("--data", type=Path, default=DATA, help="dataset folder")
    args = parser.parse_args(argv)
    try:
        case = load_case(args.data / "cases" / args.case_id)
    except DataFormatError as error:
        print(error)
        return 1
    print(render(case))
    return 0


if __name__ == "__main__":
    sys.exit(main())
