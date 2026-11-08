"""The researcher's workspace folder: cases, stored runs, the audit log and exports.

Layout (the case folders follow docs/data-format.md §2, so the frozen loader reads them):

    <workspace>/dataset.json             observation window (engine.load_window reads it)
    <workspace>/cases/<case_id>/...      case.json, record.json, documents/
    <workspace>/runs/<case_id>/<run_id>.json   one file per verification run, never edited
    <workspace>/audit.jsonl              append-only log of runs and review decisions
    <workspace>/exports/                 reports and CSV files

Everything the app writes goes inside the workspace. The workspace and any folder the app
reads must be inside this repository; data/ is only ever read (example cases are copied).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path

from resauce.loader import DataFormatError, load_case
from resauce.models import FICTIONAL_NOTICE

from app.sources import ROOT

CASE_ID = re.compile(r"SYN-[0-9]{4}")
RUN_ID = re.compile(r"[0-9]{8}T[0-9]{6}-[0-9]{6}")
EXAMPLES = ROOT / "data" / "dev-v1"
# Folders of the project itself: a workspace may not be one of them or inside one.
PROTECTED = [ROOT / name for name in ("src", "tests", "data", "reference", "results", "app", "web",
                                      "docs", "tools", ".git", ".venv", ".impeccable", ".claude", ".agents")]
COMMON = {"schema_version": "0.1", "synthetic": True, "fictional_notice": FICTIONAL_NOTICE}


class WorkspaceError(Exception):
    """A request the workspace refuses, with a plain-language reason."""


class FormProblems(Exception):
    """New-case problems, each tied to a form field key (see Workspace.create_case)."""

    def __init__(self, problems: list[dict]):
        super().__init__(f"{len(problems)} problem(s)")
        self.problems = problems


def inside_repo(path: Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if resolved != ROOT and not resolved.is_relative_to(ROOT):
        raise WorkspaceError(
            f"{resolved} is outside the ReSauce folder. This proof of concept only opens folders inside {ROOT}.")
    return resolved


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def folder_fingerprint(folder: Path) -> dict:
    """{relative path: bytes} of every file in a case folder, to tell whether two copies are identical."""
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*"))
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(folder).parts)}


class Workspace:
    def __init__(self, folder: Path):
        folder = inside_repo(folder)
        if folder == ROOT or any(folder == p or folder.is_relative_to(p) for p in PROTECTED):
            raise WorkspaceError(f"{folder} is part of the project itself; choose another folder, e.g. workspace/.")
        self.folder = folder
        self.cases_dir = folder / "cases"
        self.runs_dir = folder / "runs"
        self.exports_dir = folder / "exports"
        self.audit_path = folder / "audit.jsonl"
        self.dataset_path = folder / "dataset.json"
        self.lock = threading.RLock()  # one writer at a time: runs, decisions and audit entries
        for d in (self.cases_dir, self.runs_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)

    # -- cases ---------------------------------------------------------------------------

    def case_ids(self) -> list[str]:
        return sorted(p.name for p in self.cases_dir.iterdir() if p.is_dir() and CASE_ID.fullmatch(p.name))

    def case_folder(self, case_id: str) -> Path:
        if not CASE_ID.fullmatch(case_id or "") or not (self.cases_dir / case_id).is_dir():
            raise KeyError(case_id)
        return self.cases_dir / case_id

    def _ensure_dataset(self) -> None:
        """A dataset.json for the workspace, declaring the same window as the example dataset (§6.5)."""
        if self.dataset_path.is_file():
            return
        window = json.loads((EXAMPLES / "dataset.json").read_text(encoding="utf-8"))["observation_window"]
        _write_json(self.dataset_path, {**COMMON, "dataset_id": "SYN-DS-WORKSPACE", "dataset_version": "1",
                                        "description": "ReSauce workspace. Fictional synthetic cases only. "
                                                       "Observation window copied from data/dev-v1/dataset.json.",
                                        "observation_window": window})

    @staticmethod
    def example_count() -> int:
        return sum(1 for p in (EXAMPLES / "cases").iterdir() if p.is_dir() and CASE_ID.fullmatch(p.name))

    def load_examples(self) -> dict:
        """Copy the dev-v1 synthetic case folders into the workspace (data/ is only read)."""
        if not self.dataset_path.is_file():
            shutil.copyfile(EXAMPLES / "dataset.json", self.dataset_path)
        copied, skipped = [], []
        for source in sorted((EXAMPLES / "cases").iterdir()):
            if not (source.is_dir() and CASE_ID.fullmatch(source.name)):
                continue
            if (self.cases_dir / source.name).exists():
                skipped.append(source.name)
                continue
            shutil.copytree(source, self.cases_dir / source.name)
            copied.append(source.name)
        return {"copied": copied, "skipped_existing": skipped, "source": "data/dev-v1"}

    def import_folder(self, path: str) -> dict:
        """Copy valid case folders from a folder inside the repository into the workspace."""
        if not (path or "").strip():
            raise WorkspaceError("Enter a folder path.")
        source = inside_repo(Path(path.strip()) if Path(path.strip()).is_absolute() else ROOT / path.strip())
        if not source.is_dir():
            raise WorkspaceError(f"No folder at {source}.")
        if source == self.folder or source.is_relative_to(self.folder):
            raise WorkspaceError("That folder is already part of this workspace.")
        if (source / "case.json").is_file():
            candidates = [source]
        elif (source / "cases").is_dir():
            candidates = sorted(p for p in (source / "cases").iterdir() if p.is_dir() and not p.name.startswith("."))
        else:
            raise WorkspaceError("That folder holds neither a case (case.json) nor a dataset (cases/).")
        self._ensure_dataset()
        imported, skipped, invalid = [], [], []
        for folder in candidates:
            if (self.cases_dir / folder.name).exists():
                skipped.append(folder.name)
                continue
            links = [str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_symlink()]
            if links:  # a link could point outside the repository; never followed
                invalid.append({"case": folder.name, "problems": [f"contains a symbolic link ({links[0]}); links are not imported"]})
                continue
            try:
                load_case(folder)
            except DataFormatError as exc:
                invalid.append({"case": folder.name, "problems": [str(p) for p in exc.problems]})
                continue
            shutil.copytree(folder, self.cases_dir / folder.name)
            imported.append(folder.name)
        return {"source": str(source), "imported": imported, "skipped_existing": skipped, "invalid": invalid}

    def create_case(self, form: dict) -> str:
        """Write a new case in the data-format layout, validate it with load_case, then add it.

        Problems come back keyed to the form: "case.<field>", "record.<i>.<field>",
        "doc.<i>.<version>.<field>" (i 0-based), or "form" for anything else.
        """
        case_id = str(form.get("case_id", "")).strip()
        if not CASE_ID.fullmatch(case_id):
            raise FormProblems([{"key": "case.case_id", "message": "must be SYN- followed by exactly 4 digits, e.g. SYN-0901"}])
        if (self.cases_dir / case_id).exists():
            raise FormProblems([{"key": "case.case_id", "message": f"{case_id} already exists in this workspace"}])
        documents = form.get("documents") or []
        versions = form.get("record_versions") or []
        if not versions:
            raise FormProblems([{"key": "form", "message": "add at least one research record version"}])

        self._ensure_dataset()  # engine.load_window needs it, also in a workspace with no example cases
        staging = self.folder / ".staging" / case_id
        if staging.exists():
            shutil.rmtree(staging)
        (staging / "documents").mkdir(parents=True)
        files = {}  # file name -> form key prefix
        try:
            _write_json(staging / "case.json", {**COMMON, "case_id": case_id,
                                                "age_at_infusion": _number(form.get("age_at_infusion")),
                                                "infusion_date": _text(form.get("infusion_date"))})
            files["case.json"] = "case."
            _write_json(staging / "record.json", {**COMMON, "case_id": case_id, "record_id": f"{case_id}-R",
                                                  "versions": [_record_version(i, v) for i, v in enumerate(versions)]})
            files["record.json"] = "record."
            for i, doc in enumerate(documents):
                document_id = f"{case_id}-D{i + 1:02d}"
                for n, v in enumerate(doc.get("versions") or [], start=1):
                    name = f"{document_id}.v{n}.json"
                    _write_json(staging / "documents" / name, {
                        "case_id": case_id, "document_id": document_id, "version": n,
                        "status": _text(v.get("status")) or "signed",
                        "note_type": _text(doc.get("note_type")), "author_role": _text(v.get("author_role") or doc.get("author_role")),
                        "documented_at": _text(v.get("documented_at")),
                        "amendment_reason": _text(v.get("amendment_reason")) if n > 1 else None,
                        "text": v.get("text") if isinstance(v.get("text"), str) else "",
                        **COMMON,
                    })
                    files[name] = f"doc.{i}.{n}."
            if not any((staging / "documents").iterdir()):
                (staging / "documents").rmdir()
            try:
                load_case(staging)
            except DataFormatError as exc:
                raise FormProblems([_form_key(p, files) for p in exc.problems]) from None
            os.replace(staging, self.cases_dir / case_id)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return case_id

    # -- runs ----------------------------------------------------------------------------

    def save_run(self, case_id: str, run: dict) -> None:
        folder = self.runs_dir / case_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{run['run_id']}.json"
        if path.exists():
            raise WorkspaceError(f"run {run['run_id']} already exists")  # runs are never overwritten
        _write_json(path, run)

    def latest_run(self, case_id: str) -> dict | None:
        folder = self.runs_dir / case_id
        if not folder.is_dir():
            return None
        names = sorted(p.name for p in folder.iterdir() if p.suffix == ".json" and RUN_ID.fullmatch(p.stem))
        return json.loads((folder / names[-1]).read_text(encoding="utf-8")) if names else None

    @staticmethod
    def new_run_id() -> str:
        return datetime.now().strftime("%Y%m%dT%H%M%S-%f")

    # -- audit log -----------------------------------------------------------------------

    def append_audit(self, entry: dict) -> dict:
        entry = {"time": now(), **entry}
        line = json.dumps(entry, ensure_ascii=False, sort_keys=False)
        with self.lock, self.audit_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return entry

    def audit_entries(self) -> list[dict]:
        if not self.audit_path.is_file():
            return []
        entries = []
        for number, line in enumerate(self.audit_path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:  # shown, never dropped silently
                    entries.append({"type": "unreadable", "line": number, "text": line})
        return entries

    def export_path(self, name: str) -> Path:
        return self.exports_dir / name


def _text(value):
    if value is None:
        return None
    value = str(value)
    return value if value.strip() else None


def _number(value):
    """A whole number from a form string; anything else is passed on for the loader to report."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = str(value if value is not None else "").strip()
    if re.fullmatch(r"-?[0-9]+", text):
        return int(text)
    return text or None


def _record_version(index: int, v: dict) -> dict:
    reported = bool(v.get("icans_reported"))
    return {"version": index + 1, "recorded_at": _text(v.get("recorded_at")), "icans_reported": reported,
            "onset_date": _text(v.get("onset_date")), "max_grade": _number(v.get("max_grade")),
            "change_reason": _text(v.get("change_reason")) if index > 0 else None}


_VERSION_FIELD = re.compile(r"versions\[(\d+)\]\.(\w+)")


def _form_key(problem, files: dict) -> dict:
    """Map a loader problem (file path, field, message) to the form field that caused it."""
    name = Path(problem.source).name
    prefix = files.get(name)
    if prefix is None and name == "documents":
        return {"key": "form", "message": problem.message}
    field = problem.field
    if prefix == "record.":
        m = _VERSION_FIELD.fullmatch(field)
        if m:
            return {"key": f"record.{m.group(1)}.{m.group(2)}", "message": problem.message}
    if prefix and prefix.startswith("doc.") and field == "note_type":
        prefix = prefix.rsplit(".", 2)[0] + ".1."  # the form has one document-type field per document
    if prefix and not field.startswith("("):
        return {"key": prefix + field, "message": problem.message}
    return {"key": "form", "message": f"{name}: {problem.message}" if prefix else problem.message}
