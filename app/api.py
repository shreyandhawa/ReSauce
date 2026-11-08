"""The app's API: plain functions that return JSON-ready dicts.

Every number comes from a results file or from a live run of the frozen pipeline. Computed
here only: timings, whether a live run equals the stored one, and, for the case list, whether
a method's category equals the reference category (the evaluator's exact-agreement rule and
its out-of-scope reason rule, `resauce.evaluate._same_reason`).
"""

from __future__ import annotations

import dataclasses
import json
import time
from datetime import date, datetime
from datetime import time as clock_time

from resauce import baseline_a, engine
from resauce import evaluate as ev
from resauce.extract import Observation, extract_case
from resauce.loader import load_case, study_day
from resauce.models import FICTIONAL_NOTICE, EvidenceRef

from app.sources import Sources, Split, display_path

# Split headings and disclosures as results/report.md and resauce.evaluate state them.
SPLIT_TITLES = {"dev": "dev", "held_out": "held-out (in-repo, not sealed)"}
SPLIT_DISCLOSURES = {
    "held_out": (ev.HELD_OUT_SEEN[0].upper() + ev.HELD_OUT_SEEN[1:] + ".", ev.HELD_OUT_DISCLOSURE),
}


class NotFound(Exception):
    pass


def _jsonable(value):
    """Dates, tuples and dataclasses as plain JSON values."""
    if isinstance(value, (datetime, date, clock_time)):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot show a value of type {type(value).__name__}")  # never hidden as text


def _ref(ref: EvidenceRef | None) -> dict | None:
    if ref is None:
        return None
    return {"document_id": ref.document_id, "version": ref.version, "start": ref.start, "end": ref.end,
            "quote": ref.quote}


def _error_text(exc: Exception) -> str:
    return " ".join(f"{type(exc).__name__}: {exc}".split())


def _agreement(method: str, reference: dict | None, record: dict | None) -> str | None:
    """"agrees", "disagrees", "error", "n/a" (Baseline A cannot flag out of scope) or None (no reference).

    In scope: every field's category equals the reference category (exact agreement, evaluate §3).
    Reference out of scope: the method flagged the case out of scope with the same reason.
    """
    if not reference:
        return None
    if not record or "error" in record:
        return "error"
    output = record["output"]
    if reference["out_of_scope"]:
        if method != "resauce":
            return "n/a"
        flagged = output.get("out_of_scope")
        same = bool(flagged) and ev._same_reason(flagged["reason"], reference["out_of_scope"])
        return "agrees" if same else "disagrees"
    if output.get("out_of_scope"):
        return "disagrees"
    same = all(output["fields"][n]["category"] == (ev.reference_code(reference["fields"][n]) or
                                                     reference["fields"][n]) for n in ev.FIELDS)
    return "agrees" if same else "disagrees"


def _categories(method_record: dict | None) -> dict:
    """{"onset": cat, "max_grade": cat}, or {"error": text} for a method that failed on the case."""
    if not method_record:
        return {"error": "no result"}
    if "error" in method_record:
        return {"error": method_record["error"]}
    return {name: method_record["output"]["fields"][name]["category"] for name in ev.FIELDS}


class Api:
    def __init__(self, sources: Sources):
        self.sources = sources

    def _find(self, case_id: str) -> tuple[Split, dict]:  # raises NotFound for the HTTP layer
        found = self.sources.find(case_id)
        if found is None:
            raise NotFound(f"no case {case_id!r} in the loaded results files")
        return found

    # -- GET /api/summary ----------------------------------------------------------------

    def summary(self) -> dict:
        splits = []
        for split in self.sources.splits:
            r = split.results
            splits.append({
                "name": split.name,
                "title": _title(split),
                "results_file": display_path(split.results_path),
                "data_dir": display_path(split.data_dir),
                "case_count": len(r.get("cases", [])),
                "metadata": r.get("metadata"),
                "metrics": r.get("metrics"),
                "runtime_seconds": r.get("runtime_seconds"),
                "reference_errors": r.get("reference_errors", []),
                "disclosures": list(SPLIT_DISCLOSURES.get(split.name, ())),
            })
        return {
            "splits": splits,
            "methods": ev.METHOD_TITLES,
            "reference_label": ev.LABEL,
            "limitations": list(ev.LIMITATIONS),
            "scoring": {"positive": ev.POSITIVE, "negative": ev.NEGATIVE, "review": ev.REVIEW},
        }

    # -- GET /api/cases ------------------------------------------------------------------

    def cases(self) -> dict:
        rows = []
        for split in self.sources.splits:
            for record in split.results.get("cases", []):
                reference = record.get("reference")
                ref_fields = {}
                if reference:
                    ref_fields = {n: ev.reference_code(c) or c for n, c in reference["fields"].items()}
                methods = {m: _categories(record.get(m)) for m in ev.METHODS}
                agreement = {m: _agreement(m, reference, record.get(m)) for m in ev.METHODS}
                rows.append({
                    "case_id": record["case_id"],
                    "split": split.name,
                    "split_title": _title(split),
                    "reference": {"out_of_scope": reference["out_of_scope"], "fields": ref_fields} if reference else None,
                    "reference_error": record.get("reference_error"),
                    **methods,
                    "agreement": agreement,
                })
        return {"cases": rows, "methods": ev.METHOD_TITLES}

    # -- GET /api/cases/<id> -------------------------------------------------------------

    def case(self, case_id: str) -> dict:
        split, record = self._find(case_id)
        folder = split.case_folder(case_id)
        case = load_case(folder)
        window = engine.load_window(folder)
        reference = None
        if split.reference_file(case_id).is_file():
            reference = json.loads(split.reference_file(case_id).read_text(encoding="utf-8"))
        return {
            "case_id": case.case_id,
            "split": split.name,
            "split_title": _title(split),
            "results_file": display_path(split.results_path),
            "fictional_notice": FICTIONAL_NOTICE,  # the loader accepts a case only with this notice
            "facts": {"age_at_infusion": case.age_at_infusion, "infusion_date": case.infusion_date.isoformat()},
            "window": {"start_day": window.start_day, "end_day": window.end_day},
            "documents": [{
                "document_id": d.document_id, "version": d.version, "version_id": d.version_id,
                "status": d.status, "note_type": d.note_type, "author_role": d.author_role,
                "documented_at": d.documented_at.isoformat(timespec="minutes"),
                "documented_day": study_day(case, d.documented_at),
                "amendment_reason": d.amendment_reason, "text": d.text,
            } for d in case.documents],
            "record": {"record_id": case.record.record_id, "versions": [{
                "version": v.version, "recorded_at": v.recorded_at.isoformat(timespec="minutes"),
                "icans_reported": v.icans_reported,
                "onset_date": v.onset_date.isoformat() if v.onset_date else None,
                "onset_day": study_day(case, v.onset_date) if v.onset_date else None,
                "max_grade": v.max_grade, "change_reason": v.change_reason,
            } for v in case.record.versions]},
            "stored": {m: record.get(m) for m in ev.METHODS},
            "stored_runtime_seconds": record.get("runtime_seconds"),
            "reference": reference,
            "reference_label": ev.LABEL,
        }

    # -- POST /api/cases/<id>/run --------------------------------------------------------

    def run(self, case_id: str) -> dict:
        """Run the frozen pipeline live on one case folder and compare with the stored run.

        Like evaluate.run_case, a failure becomes an error entry in the response, never hidden.
        """
        split, record = self._find(case_id)
        folder = split.case_folder(case_id)
        timings = {}
        response = {"case_id": case_id, "stored_results_file": display_path(split.results_path),
                    "stored_run_date": (split.results.get("metadata") or {}).get("date"),
                    "timings_seconds": timings, "error": None}

        for stage in ("load", "extract"):
            started = time.perf_counter()
            try:
                if stage == "load":
                    case, window = load_case(folder), engine.load_window(folder)
                else:
                    observations = extract_case(case)
            except Exception as exc:
                response["error"] = f"{stage}: {_error_text(exc)}"
                return response
            finally:
                timings[stage] = time.perf_counter() - started

        runs = {"resauce": lambda: engine.evaluate_case(case, observations, window).to_dict(),
                "baseline_a": lambda: baseline_a.evaluate_case(case, observations).to_dict()}
        outputs, matches = {}, {}
        for method, run in runs.items():
            started = time.perf_counter()
            try:
                output = json.loads(json.dumps(run()))  # the same JSON form as the results file
                outputs[method] = {"output": output, "evidence_valid": ev.evidence_validity(case, output)}
            except Exception as exc:  # reported, as the evaluation runner does; never hidden
                outputs[method] = {"error": _error_text(exc)}
            timings[method] = time.perf_counter() - started
            stored = (record.get(method) or {}).get("output")
            live = outputs[method].get("output")
            matches[method] = None if stored is None or live is None else live == stored

        response.update({
            "observations": [_observation(case, i, o) for i, o in enumerate(observations)],
            "resauce": outputs["resauce"],
            "baseline_a": outputs["baseline_a"],
            "matches_stored": matches,  # compares the method output only, as stored in "output"
        })
        return response


def _title(split: Split) -> str:
    return SPLIT_TITLES.get(split.name, split.name)


def _observation(case, index: int, o: Observation) -> dict:
    return {
        "id": index,
        "kind": o.kind,
        "value": _jsonable(o.value),
        "status": o.status,
        "evidence": _ref(o.evidence),
        "signed": o.signed,
        "documented_at": o.documented_at.isoformat(timespec="minutes"),
        "documented_day": study_day(case, o.documented_at),
        "event_date": o.event_date.isoformat() if o.event_date else None,
        "event_date_end": o.event_date_end.isoformat() if o.event_date_end else None,
        "event_day": study_day(case, o.event_date) if o.event_date else None,
        "event_day_end": study_day(case, o.event_date_end) if o.event_date_end else None,
        "event_time": o.event_time.strftime("%H:%M") if o.event_time else None,
        "time_source": o.time_source,
        "time_evidence": _ref(o.time_evidence),
        "details": _jsonable(o.details),
        "note": o.note,
    }
