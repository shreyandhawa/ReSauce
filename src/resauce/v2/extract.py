"""v2 extraction: clean the text, run the frozen v1 extractor, map every quote back.

The v1 extractor (resauce.extract) is not changed and is called as it is. v2 only changes the
text it reads. Each observation it returns is then re-pointed at the ORIGINAL note: the quote
is the exact original text at original offsets, so the rule "every observation links to its
exact quoted source" holds for v2 as for v1. A failure of that check means a bug in this
module and is raised, not hidden.

Not changed by v2: the timeline, the rules engine, the scoring. They take the observations
that come out of here, so `engine.evaluate_case(case, extract_case(case).observations, window)`
is the whole v2 pipeline.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from resauce import extract as v1
from resauce.loader import check_evidence_ref
from resauce.models import Case, EvidenceRef
from resauce.v2.normalise import NormalisedText, Step, normalise
from resauce.v2.steps import STEPS


@dataclass(frozen=True)
class Extraction:
    """Observations (in original-text coordinates) and what the clean-up changed per document."""

    observations: tuple[v1.Observation, ...]
    normalised: dict[str, NormalisedText]  # keyed by document version ID, e.g. "SYN-0001-D01.v1"


def extract_case(case: Case, steps: tuple[Step, ...] = STEPS) -> Extraction:
    """Extract observations from every document version, after cleaning each text."""
    normalised = {d.version_id: normalise(d.text, steps) for d in case.documents}
    cleaned_case = dataclasses.replace(case, documents=tuple(
        dataclasses.replace(d, text=normalised[d.version_id].text) for d in case.documents))

    observations = []
    for observation in v1.extract_case(cleaned_case):
        evidence = _to_original(case, normalised, observation.evidence)
        time_evidence = (_to_original(case, normalised, observation.time_evidence)
                         if observation.time_evidence is not None else None)
        mapped = dataclasses.replace(observation, evidence=evidence, time_evidence=time_evidence)
        check_evidence_ref(case, mapped.evidence)  # against the ORIGINAL case
        if mapped.time_evidence is not None:
            check_evidence_ref(case, mapped.time_evidence)
        observations.append(mapped)
    return Extraction(tuple(observations), normalised)


def _to_original(case: Case, normalised: dict[str, NormalisedText], ref: EvidenceRef) -> EvidenceRef:
    document = case.get_document_version(ref.document_id, ref.version)
    start, end = normalised[document.version_id].to_original(ref.start, ref.end)
    return EvidenceRef(ref.document_id, ref.version, start, end, document.text[start:end])
