"""Where the app's data comes from: results files, case folders and reference answers.

Each split is one results file (written by `python -m resauce.evaluate`) plus the data
folder and reference folder its cases came from. Only case IDs listed in a loaded results
file are ever read or run, so a request can never name an arbitrary folder.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = re.compile(r"SYN-[0-9]{4}")

DEFAULT_SPLITS = (
    (ROOT / "results" / "dev.json", ROOT / "data" / "dev-v1", ROOT / "reference" / "dev-v1"),
    (ROOT / "results" / "held_out.json", ROOT / "data" / "dev-v1", ROOT / "reference" / "dev-v1"),
)


@dataclass(frozen=True)
class Split:
    name: str
    results_path: Path
    data_dir: Path
    reference_dir: Path
    results: dict  # the parsed results file

    def case_folder(self, case_id: str) -> Path:
        return self.data_dir / "cases" / case_id

    def reference_file(self, case_id: str) -> Path:
        return self.reference_dir / "intended" / f"{case_id}.json"


def display_path(path: Path) -> str:
    """A path relative to the repository when possible, for showing on screen."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


class Sources:
    """The loaded splits, and a lookup from case ID to its split and stored result."""

    def __init__(self, triples: list[tuple[Path, Path, Path]]):
        self.splits: list[Split] = []
        self._cases: dict[str, tuple[Split, dict]] = {}
        for results_path, data_dir, reference_dir in triples:
            results_path, data_dir, reference_dir = (Path(p).resolve() for p in (results_path, data_dir, reference_dir))
            for path, kind in ((results_path, "file"), (data_dir, "dir"), (reference_dir, "dir")):
                if not (path.is_file() if kind == "file" else path.is_dir()):
                    raise ValueError(f"not found: {path}")
            results = json.loads(results_path.read_text(encoding="utf-8"))
            name = results.get("split")
            if not name or any(s.name == name for s in self.splits):
                raise ValueError(f"{results_path}: missing or repeated split name {name!r}")
            split = Split(name, results_path, data_dir, reference_dir, results)
            self.splits.append(split)
            for record in results.get("cases", []):
                case_id = record["case_id"]
                if not CASE_ID.fullmatch(case_id):
                    raise ValueError(f"{results_path}: unexpected case ID {case_id!r}")
                if case_id in self._cases:
                    raise ValueError(f"case {case_id} appears in more than one results file")
                self._cases[case_id] = (split, record)

    def find(self, case_id: str) -> tuple[Split, dict] | None:
        """(split, stored record) for a case ID from a loaded results file, else None."""
        if not CASE_ID.fullmatch(case_id):
            return None
        return self._cases.get(case_id)
