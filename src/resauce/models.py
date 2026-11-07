"""In-memory shapes of ReSauce synthetic data.

The file format is specified in docs/data-format.md. These classes only hold
data that the loader has already checked. They contain no clinical, ICANS or
grading logic.

All classes are frozen (their values cannot be changed after creation), and
collections are stored as tuples, so loaded data cannot be altered by mistake.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

SCHEMA_VERSION = "0.1"
FICTIONAL_NOTICE = "FICTIONAL SYNTHETIC DATA. NOT A REAL PATIENT."

DOCUMENT_STATUSES = ("signed", "unsigned")

NOTE_TYPES = (
    "physician_progress_note",
    "nursing_note",
    "neurology_consult",
    "ice_assessment",
    "eeg_report",
    "imaging_report",
    "discharge_summary",
    "other",
)

AUTHOR_ROLES = (
    "attending_physician",
    "resident_physician",
    "advanced_practice_provider",
    "nurse",
    "neurologist",
    "radiologist",
    "other",
)


@dataclass(frozen=True)
class ObservationWindow:
    """Days after infusion (Day 0) that a dataset covers, inclusive."""

    start_day: int
    end_day: int


@dataclass(frozen=True)
class DocumentVersion:
    """One version of one clinical document."""

    case_id: str
    document_id: str
    version: int
    status: str
    note_type: str
    author_role: str
    documented_at: datetime
    amendment_reason: str | None
    text: str

    @property
    def version_id(self) -> str:
        """Identifier of this exact version, e.g. "SYN-0001-D01.v2"."""
        return f"{self.document_id}.v{self.version}"


@dataclass(frozen=True)
class RecordVersion:
    """One entry in a research record's change history."""

    version: int
    recorded_at: datetime
    icans_reported: bool
    onset_date: date | None
    max_grade: int | None
    change_reason: str | None


@dataclass(frozen=True)
class ResearchRecord:
    """The research record of one case, with its full change history."""

    case_id: str
    record_id: str
    versions: tuple[RecordVersion, ...]

    @property
    def current(self) -> RecordVersion:
        """The latest version of the record."""
        return self.versions[-1]


@dataclass(frozen=True)
class Case:
    """One synthetic patient case: case facts, record and documents."""

    case_id: str
    age_at_infusion: int
    infusion_date: date
    record: ResearchRecord
    documents: tuple[DocumentVersion, ...]

    def get_document_version(
        self, document_id: str, version: int
    ) -> DocumentVersion | None:
        """Return the given document version, or None if the case has none."""
        for document in self.documents:
            if document.document_id == document_id and document.version == version:
                return document
        return None


@dataclass(frozen=True)
class Dataset:
    """A named, versioned collection of synthetic cases."""

    dataset_id: str
    dataset_version: str
    description: str
    observation_window: ObservationWindow
    cases: tuple[Case, ...]


@dataclass(frozen=True)
class EvidenceRef:
    """A citation of exact text inside one document version.

    start and end are 0-based, end-exclusive Python string indices into the
    document version's text, so text[start:end] must equal quote.
    """

    document_id: str
    version: int
    start: int
    end: int
    quote: str
