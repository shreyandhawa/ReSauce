"""The frozen pipeline as the app runs it: its version, and one live run in stages.

Nothing here changes how the pipeline decides. Each stage calls a public function of the
frozen core (`resauce.loader`, `resauce.extract`, `resauce.timeline`, `resauce.engine`,
`resauce.baseline_a`) and is yielded the moment it finishes, so the screen can show the
run advancing with real results, never with invented delays.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import subprocess
import time
from datetime import date, datetime
from datetime import time as clock_time
from pathlib import Path

from resauce import baseline_a, engine
from resauce import evaluate as ev
from resauce import timeline as T
from resauce.extract import Observation, extract_case
from resauce import v2
from resauce.loader import DataFormatError, load_case, study_day
from resauce.models import EvidenceRef
from resauce.v2 import extract as v2_extract
from resauce.v2.steps import STEPS as V2_STEPS

from app.sources import ROOT

FREEZE_DOC = ROOT / "docs" / "freeze.md"
FREEZE_TAG = "pipeline-freeze-v1"
LINES = ("v1", "v2")  # v1 is the frozen pipeline; v2 is the development line (docs/v2.md)
_FREEZE_ROW = re.compile(r"^\|\s*(src/resauce/[a-z_]+\.py)\s*\|\s*([0-9a-f]{64})\s*\|\s*$")


def _git(*args: str) -> str | None:
    """A git answer, or None when git or the repository is not available (never guessed)."""
    try:
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_table() -> list[tuple[str, str]]:
    rows = []
    for line in FREEZE_DOC.read_text(encoding="utf-8").splitlines():
        match = _FREEZE_ROW.match(line)
        if match:
            rows.append((match.group(1), match.group(2)))
    return rows


_GIT_FACTS: dict | None = None


def pipeline_version() -> dict:
    """The git tag of the freeze and each frozen file's hash: as recorded and as it is now."""
    global _GIT_FACTS
    if _GIT_FACTS is None:  # git facts do not change while the app runs
        _GIT_FACTS = {"tag_commit": _git("rev-parse", f"{FREEZE_TAG}^{{commit}}"),
                      "head_commit": _git("rev-parse", "HEAD")}
    files = []
    for path, expected in _frozen_table():
        target = ROOT / path
        actual = sha256_file(target) if target.is_file() else None
        files.append({"path": path, "expected": expected, "actual": actual, "match": actual == expected})
    return {
        "tag": FREEZE_TAG,
        **_GIT_FACTS,
        "frozen_files": files,
        "frozen_files_match": bool(files) and all(f["match"] for f in files),
        "hashes_from": "docs/freeze.md",
    }


def v2_version() -> dict:
    """The v2 line: its status and the hash of each of its files as they are now (not frozen)."""
    folder = ROOT / "src" / "resauce" / "v2"
    names = ["__init__", *v2.FILES]
    return {"line": v2.LINE, "status": v2.STATUS,
            "files": {f"src/resauce/v2/{n}.py": sha256_file(folder / f"{n}.py") for n in names}}


def jsonable(value):
    """Dates, tuples and dataclasses as plain JSON values."""
    if isinstance(value, (datetime, date, clock_time)):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot show a value of type {type(value).__name__}")  # never hidden as text


def ref(r: EvidenceRef | None) -> dict | None:
    if r is None:
        return None
    return {"document_id": r.document_id, "version": r.version, "start": r.start, "end": r.end, "quote": r.quote}


def error_text(exc: Exception) -> str:
    return " ".join(f"{type(exc).__name__}: {exc}".split())


def problems_of(exc: Exception) -> list[dict]:
    if isinstance(exc, DataFormatError):
        return [{"source": p.source, "field": p.field, "message": p.message} for p in exc.problems]
    return []


def observation_dict(case, index: int, o: Observation) -> dict:
    return {
        "id": index,
        "kind": o.kind,
        "value": jsonable(o.value),
        "status": o.status,
        "evidence": ref(o.evidence),
        "signed": o.signed,
        "documented_at": o.documented_at.isoformat(timespec="minutes"),
        "documented_day": study_day(case, o.documented_at),
        "event_date": o.event_date.isoformat() if o.event_date else None,
        "event_date_end": o.event_date_end.isoformat() if o.event_date_end else None,
        "event_day": study_day(case, o.event_date) if o.event_date else None,
        "event_day_end": study_day(case, o.event_date_end) if o.event_date_end else None,
        "event_time": o.event_time.strftime("%H:%M") if o.event_time else None,
        "time_source": o.time_source,
        "time_evidence": ref(o.time_evidence),
        "details": jsonable(o.details),
        "note": o.note,
    }


def _timeline_summary(case, observations, window) -> dict:
    """How resauce.timeline sorts each observation: which content the rules may use (§6)."""
    sel = T.select(case, observations, window)
    index = {id(o): i for i, o in enumerate(observations)}
    groups = {"used": sel.used, "undated": sel.undated, "outside_window": sel.outside_window}
    use = {}
    for name, members in groups.items():
        for o in members:
            use[index[id(o)]] = name
    current_ids = {d.version_id for d in sel.current.values()}
    copied_ids = {copy.version_id for copy, _ in sel.copied}
    for i, o in enumerate(observations):
        if i in use:
            continue
        vid = T.version_id(o)
        use[i] = ("copied_forward" if vid in copied_ids else
                  "not_current_version" if vid not in current_ids else "context_only")
    return {
        "window": {"start_day": window.start_day, "end_day": window.end_day},
        "use": [use[i] for i in range(len(observations))],
        "current_versions": sorted(current_ids - copied_ids),
        "copied_forward": [{"copy": c.version_id, "original": o.version_id} for c, o in sel.copied],
    }


def normalisation_dict(extracted) -> dict:
    """What the v2 clean-up changed, in original-text offsets, so the page can mark it."""
    def edit(e):
        return {"rule_id": e.rule_id, "start": e.start, "end": e.end, "original": e.original,
                "replacement": e.replacement}
    documents = [{"version_id": version_id, "edits": [edit(e) for e in n.edits],
                  "dropped": [edit(e) for e in n.dropped]}
                 for version_id, n in extracted.normalised.items() if n.edits or n.dropped]
    return {"rules": [{"rule_id": s.rule_id, "description": s.description} for s in V2_STEPS],
            "documents": documents,
            "total_edits": sum(len(d["edits"]) for d in documents),
            "total_dropped": sum(len(d["dropped"]) for d in documents)}


def run_stages(folder: Path, with_baseline: bool, line: str = "v1"):
    """Yield (stage, payload) as each stage of the pipeline finishes.

    line "v1" is the frozen pipeline. Line "v2" adds a text clean-up before extraction
    (docs/v2.md); its "normalisation" stage arrives just before "extraction", and the
    extraction time then includes the clean-up.

    Stages: load, [normalisation, v2 only], extraction, timeline, verdict (the rules engine
    computes the comparison and the verdict together), baseline (only when asked). A failure
    is yielded as ("error", ...) and ends the run; it is never hidden, as in
    resauce.evaluate.run_case.
    """
    if line not in LINES:
        raise ValueError(f"unknown pipeline line {line!r}")

    def timed(call):
        started = time.perf_counter()
        result = call()
        return result, time.perf_counter() - started

    try:
        (case, window), seconds = timed(lambda: (load_case(folder), engine.load_window(folder)))
    except Exception as exc:
        yield "error", {"stage": "load", "error": error_text(exc), "problems": problems_of(exc)}
        return
    yield "load", {"seconds": seconds, "documents": len({d.document_id for d in case.documents}),
                   "versions": len(case.documents)}

    try:
        if line == "v2":
            extracted, seconds = timed(lambda: v2_extract.extract_case(case))
            observations = extracted.observations
            yield "normalisation", normalisation_dict(extracted)
        else:
            observations, seconds = timed(lambda: extract_case(case))
    except Exception as exc:
        yield "error", {"stage": "extraction", "error": error_text(exc), "problems": []}
        return
    yield "extraction", {"seconds": seconds,
                         "observations": [observation_dict(case, i, o) for i, o in enumerate(observations)]}

    try:
        summary, seconds = timed(lambda: _timeline_summary(case, observations, window))
    except Exception as exc:
        yield "error", {"stage": "timeline", "error": error_text(exc), "problems": []}
        return
    yield "timeline", {"seconds": seconds, **summary}

    methods = [("verdict", "resauce", lambda: engine.evaluate_case(case, observations, window).to_dict())]
    if with_baseline:
        methods.append(("baseline", "baseline_a", lambda: baseline_a.evaluate_case(case, observations).to_dict()))
    for stage, method, call in methods:
        try:
            output, seconds = timed(call)
            output = json.loads(json.dumps(output))  # the same JSON form as a results file
            payload = {"method": method, "seconds": seconds, "output": output,
                       "evidence_valid": list(ev.evidence_validity(case, output))}
        except Exception as exc:  # reported, as the evaluation runner does
            payload = {"method": method, "error": error_text(exc)}
        yield stage, payload


def canonical_sha(value) -> str:
    """SHA-256 of a JSON value in a fixed key order, to tell whether two outputs are identical."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
