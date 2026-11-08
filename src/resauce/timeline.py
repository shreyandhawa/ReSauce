"""Which content counts, and when it happened (clinical-methods §6).

Used by resauce.engine. Deterministic, standard library only. Nothing here
grades a finding.

- §6.3 / A27: the current version of a document is its latest signed
  version. Unsigned content is never used. Earlier signed versions are kept
  aside for the "superseded-version match" check.
- §6.4 / A13, A31: a whole note that repeats an earlier note once dates,
  times and spacing are ignored is copied forward and gives no new evidence.
  [OPERATIONAL] Only whole-note copies are detected; partly copied text is
  not (not implemented).
- §6.5 / A32: the observation window is applied per observation, by its
  event date (the extractor already falls back to the documentation date,
  §6.1). A date range counts as inside if any of its days is inside.
- An observation whose event time the extractor could not resolve is never
  given a date here; the engine treats it as a reading for review.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from resauce.extract import Observation
from resauce.loader import study_day
from resauce.models import Case, DocumentVersion, EvidenceRef, ObservationWindow

# Kinds listed in the "outside observation window" flag (§7.10: findings,
# assessments and "not assessable" statements).
WINDOW_FLAG_KINDS = (
    "ice_total", "ice_partial", "consciousness", "seizure", "eeg_finding",
    "motor_finding", "icp_sign", "text_only_icp_sign", "not_assessable",
)

_DATE_OR_TIME = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b(?:D|Day|day|DAY)\s?[+\-−]?\s?\d{1,3}\b"
)


@dataclass(frozen=True)
class Selection:
    """The content of one case that the engine may use."""

    current: dict  # document_id -> DocumentVersion used as current
    used: tuple[Observation, ...]  # current, signed, dated inside the window, not copied
    undated: tuple[Observation, ...]  # current, signed, not copied, event time unresolved
    context: tuple[Observation, ...]  # current, signed, not copied, any date (causes, barriers)
    outside_window: tuple[Observation, ...]  # present findings dated outside the window
    copied: tuple[tuple[DocumentVersion, DocumentVersion], ...]  # (copy, earlier original)
    superseded: tuple[DocumentVersion, ...]  # earlier signed versions of current documents
    flags: tuple[dict, ...]  # "unsigned later version", "unsigned document"


def evidence_dict(ref: EvidenceRef, role: str) -> dict:
    """An evidence reference in the intended-answer format."""
    return {"role": role, "document_id": ref.document_id, "version": ref.version,
            "quote": ref.quote, "start": ref.start, "end": ref.end}


def version_id(observation: Observation) -> str:
    return f"{observation.evidence.document_id}.v{observation.evidence.version}"


def select(case: Case, observations: tuple[Observation, ...], window: ObservationWindow,
           swap: DocumentVersion | None = None) -> Selection:
    """Choose current versions and sort observations into used / undated / outside.

    swap replaces the current version of its document (used to test whether
    the record matches a superseded version, §6.3).
    """
    by_document: dict[str, list[DocumentVersion]] = {}
    for document in case.documents:
        by_document.setdefault(document.document_id, []).append(document)

    current: dict[str, DocumentVersion] = {}
    superseded: list[DocumentVersion] = []
    flags: list[dict] = []
    for document_id, versions in by_document.items():
        versions = sorted(versions, key=lambda d: d.version)
        signed = [d for d in versions if d.status == "signed"]
        if not signed:
            flags.append({"flag": "unsigned document", "field": None,
                          "detail": f"{document_id} has no signed version and is not used (§6.3, A27).",
                          "evidence": []})
            continue
        current[document_id] = signed[-1]
        superseded.extend(signed[:-1])
        if versions[-1].status == "unsigned":
            flags.append(_unsigned_later_version(observations, signed[-1], versions[-1]))
    if swap is not None:
        current[swap.document_id] = swap

    copied = _copied_forward(list(current.values()))
    copied_ids = {copy.version_id for copy, _ in copied}
    current_ids = {d.version_id for d in current.values()} - copied_ids

    used, undated, context, outside = [], [], [], []
    for observation in observations:
        if version_id(observation) not in current_ids:
            continue
        context.append(observation)
        if observation.time_source == "unresolved":
            undated.append(observation)
        elif in_window(case, window, observation):
            used.append(observation)
        elif observation.status == "present" and observation.kind in WINDOW_FLAG_KINDS:
            outside.append(observation)
    return Selection(current, tuple(used), tuple(undated), tuple(context), tuple(outside),
                     tuple(copied), tuple(superseded), tuple(flags))


def _unsigned_later_version(observations, signed: DocumentVersion, unsigned: DocumentVersion) -> dict:
    """Flag text for §6.3: what the unsigned later version changes."""
    def content(document):
        return [o for o in observations if version_id(o) == document.version_id and o.kind != "unrecognised"]

    def key(o):
        return (o.kind, str(o.value), o.status)

    old, new = content(signed), content(unsigned)
    added = Counter(map(key, new)) - Counter(map(key, old))
    removed = Counter(map(key, old)) - Counter(map(key, new))
    parts = [f"adds {k} = {v} ({s})" for k, v, s in added] + [f"removes {k} = {v} ({s})" for k, v, s in removed]
    evidence = ([evidence_dict(o.evidence, "only in the unsigned version") for o in new if key(o) in added]
                + [evidence_dict(o.evidence, "only in the signed version") for o in old if key(o) in removed])
    return {"flag": "unsigned later version", "field": None,
            "detail": f"{unsigned.version_id} is unsigned; {signed.version_id} stays current. "
                      + ("; ".join(parts) if parts else "no extracted observation differs") + ".",
            "evidence": evidence}


def _normalised(text: str) -> str:
    return " ".join(_DATE_OR_TIME.sub("#", text).lower().split())


def _copied_forward(documents: list[DocumentVersion]) -> list[tuple[DocumentVersion, DocumentVersion]]:
    """Whole notes that repeat an earlier note apart from dates, times and spacing (A31)."""
    copied, seen = [], {}
    for document in sorted(documents, key=lambda d: d.documented_at):
        key = _normalised(document.text)
        if key in seen:
            copied.append((document, seen[key]))
        else:
            seen[key] = document
    return copied


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------


def days(observation: Observation) -> tuple[date, date]:
    """First and last event day (the same day unless the time is a range)."""
    start = observation.event_date
    return start, observation.event_date_end or start


def in_window(case: Case, window: ObservationWindow, observation: Observation) -> bool:
    first, last = days(observation)
    return study_day(case, first) <= window.end_day and study_day(case, last) >= window.start_day


def latest_moment(observation: Observation) -> datetime:
    """The latest moment the event can have happened (end of range, end of day if no time)."""
    _, last = days(observation)
    if observation.event_time is not None and observation.event_date_end is None:
        return datetime.combine(last, observation.event_time)
    return datetime.combine(last, time(23, 59, 59))


def earliest_moment(observation: Observation) -> datetime:
    first, _ = days(observation)
    if observation.event_time is not None and observation.event_date_end is None:
        return datetime.combine(first, observation.event_time)
    return datetime.combine(first, time(0, 0))


def within_24_hours_before(cause: Observation, finding: Observation) -> bool:
    """A30: the cause falls within the 24 hours before the finding's event time.

    The finding's time is its latest possible moment (the end of a range, as
    A30 says). The cause counts if any part of its own time span overlaps
    those 24 hours: the cautious reading.
    """
    if cause.event_date is None or finding.event_date is None:
        return False
    end = latest_moment(finding)
    return earliest_moment(cause) <= end and latest_moment(cause) >= end - timedelta(hours=24)


def onset_from(candidates: list[tuple[date, date, object]]) -> tuple[date, date, list]:
    """Documentation-derived onset (§6.2, A26) from (first day, last day, item) candidates.

    The onset is the earliest exact date. If the earliest candidate is a
    range that starts before every exactly dated candidate, the onset is the
    range from its start to the earlier of its end and the earliest exact
    date. Returns (first, last, deciding items).
    """
    exact = [c for c in candidates if c[0] == c[1]]
    ranges = [c for c in candidates if c[0] != c[1]]
    first_exact = min((c[0] for c in exact), default=None)
    if ranges:
        start = min(c[0] for c in ranges)
        if first_exact is None or start < first_exact:
            earliest = [c for c in ranges if c[0] == start]
            end = min(c[1] for c in earliest)
            if first_exact is not None:
                end = min(end, first_exact)
            deciding = [c[2] for c in earliest] + [c[2] for c in exact if c[0] == end]
            return start, end, deciding
    return first_exact, first_exact, [c[2] for c in exact if c[0] == first_exact]
