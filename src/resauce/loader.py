"""Load and validate ReSauce synthetic data files.

The file format is specified in docs/data-format.md. Validation is strict:
every problem found is collected, and one DataFormatError listing all of
them is raised at the end. This module contains no clinical, ICANS or
grading logic. It only checks the shape of the data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from resauce.models import (
    AUTHOR_ROLES,
    DOCUMENT_STATUSES,
    FICTIONAL_NOTICE,
    NOTE_TYPES,
    SCHEMA_VERSION,
    Case,
    Dataset,
    DocumentVersion,
    EvidenceRef,
    ObservationWindow,
    RecordVersion,
    ResearchRecord,
)

# Patterns use [0-9] rather than \d, because \d also matches non-ASCII digits.
CASE_ID_PATTERN = re.compile(r"SYN-[0-9]{4}")
DATASET_ID_PATTERN = re.compile(r"SYN-DS-[A-Z0-9-]+")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TIMESTAMP_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}")
DOCUMENT_FILE_PATTERN = re.compile(r".+\.v[0-9]+\.json")

COMMON_FIELDS = ("schema_version", "synthetic", "fictional_notice")
DATASET_FIELDS = COMMON_FIELDS + (
    "dataset_id",
    "dataset_version",
    "description",
    "observation_window",
)
WINDOW_FIELDS = ("start_day", "end_day")
CASE_FIELDS = COMMON_FIELDS + ("case_id", "age_at_infusion", "infusion_date")
RECORD_FIELDS = COMMON_FIELDS + ("case_id", "record_id", "versions")
RECORD_VERSION_FIELDS = (
    "version",
    "recorded_at",
    "icans_reported",
    "onset_date",
    "max_grade",
    "change_reason",
)
DOCUMENT_FIELDS = COMMON_FIELDS + (
    "case_id",
    "document_id",
    "version",
    "status",
    "note_type",
    "author_role",
    "documented_at",
    "amendment_reason",
    "text",
)

FILE_LEVEL = "(file)"
FILE_NAME = "(file name)"


@dataclass(frozen=True)
class Problem:
    """One thing wrong with the input data."""

    source: str  # file or folder path, or the evidence reference checked
    field: str  # field name, or "(file)" / "(file name)"
    message: str  # plain-English explanation

    def __str__(self) -> str:
        return f"{self.source}: {self.field}: {self.message}"


class DataFormatError(Exception):
    """Raised when input data breaks the format. Lists every problem found."""

    def __init__(self, problems: list[Problem]):
        self.problems = list(problems)
        super().__init__(self.problems)

    def __str__(self) -> str:
        lines = [f"{len(self.problems)} data format problem(s) found:"]
        lines += [f"  - {problem}" for problem in self.problems]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def load_dataset(path: str | Path) -> Dataset:
    """Load a dataset folder: dataset.json and every case in cases/.

    Cases are returned sorted by case_id. Problems in all files of all cases
    are collected before one DataFormatError is raised.
    """
    root = Path(path)
    problems: list[Problem] = []
    info = _read_dataset_file(root / "dataset.json", problems)
    cases = _load_cases_folder(root / "cases", problems)
    if problems:
        raise DataFormatError(problems)
    return Dataset(
        dataset_id=info["dataset_id"],
        dataset_version=info["dataset_version"],
        description=info["description"],
        observation_window=info["observation_window"],
        cases=tuple(sorted(cases, key=lambda case: case.case_id)),
    )


def load_case(path: str | Path) -> Case:
    """Load one case folder: case.json, record.json and all document versions.

    Documents are returned sorted by document number, then version.
    """
    problems: list[Problem] = []
    case = _load_case(Path(path), problems)
    if problems:
        raise DataFormatError(problems)
    return case


def check_evidence_ref(case: Case, ref: EvidenceRef) -> None:
    """Check that an evidence reference points at real text in the case.

    Raises DataFormatError if the document version does not exist, the
    offsets are not whole numbers or are out of range, start >= end, or the
    quote differs from text[start:end]. Returns None if the reference is valid.
    """
    source = f"evidence reference to {ref.document_id}.v{ref.version}"
    problems: list[Problem] = []

    def add(field: str, message: str) -> None:
        problems.append(Problem(source, field, message))

    for name in ("version", "start", "end"):
        value = getattr(ref, name)
        if not _is_int(value):
            add(name, f"must be a whole number, but found {_describe(value)}")
    if not isinstance(ref.quote, str):
        add("quote", f"must be a string, but found {_describe(ref.quote)}")
    if problems:
        raise DataFormatError(problems)

    document = case.get_document_version(ref.document_id, ref.version)
    if document is None:
        add(
            "document_id",
            f"document version {ref.document_id}.v{ref.version} "
            f"does not exist in case {case.case_id}",
        )
        raise DataFormatError(problems)

    length = len(document.text)
    if ref.start < 0 or ref.end > length:
        add(
            "start/end",
            f"offsets out of range: start={ref.start}, end={ref.end}, but "
            f"offsets must lie between 0 and {length} (the text length)",
        )
    if ref.start >= ref.end:
        add(
            "start/end",
            f"start ({ref.start}) must be smaller than end ({ref.end})",
        )
    if not problems:
        actual = document.text[ref.start : ref.end]
        if ref.quote != actual:
            add(
                "quote",
                f"quote does not match the document text at {ref.start}:{ref.end}; "
                f"quote is {ref.quote!r}, text there is {actual!r}",
            )
    if problems:
        raise DataFormatError(problems)


def study_day(case: Case, when: date | datetime) -> int:
    """Return calendar days from the case's infusion date (Day 0).

    Plain date arithmetic only. A datetime counts by its calendar date.
    Dates before infusion give negative numbers.
    """
    # datetime is a kind of date in Python, so check it first.
    if isinstance(when, datetime):
        when = when.date()
    elif not isinstance(when, date):
        raise TypeError("study_day needs a datetime.date or datetime.datetime")
    return (when - case.infusion_date).days


# ---------------------------------------------------------------------------
# Reading JSON
# ---------------------------------------------------------------------------


class _DuplicateKeyError(Exception):
    def __init__(self, key: str):
        self.key = key


class _NonStandardNumberError(Exception):
    def __init__(self, name: str):
        self.name = name


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(name: str) -> None:
    raise _NonStandardNumberError(name)


def _read_json(path: Path, problems: list[Problem]) -> dict | None:
    """Read one JSON file as UTF-8. Returns the top-level object, or None."""
    source = str(path)

    def add(field: str, message: str) -> None:
        problems.append(Problem(source, field, message))

    if not path.is_file():
        add(FILE_LEVEL, "required file is missing")
        return None
    try:
        # Decode bytes ourselves so line endings are never translated.
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        add(FILE_LEVEL, "file is not valid UTF-8 text")
        return None
    except OSError as error:
        add(FILE_LEVEL, f"file could not be read: {error.strerror}")
        return None
    try:
        data = json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as error:
        add(
            FILE_LEVEL,
            f"invalid JSON syntax at line {error.lineno}, column {error.colno}: "
            f"{error.msg}",
        )
        return None
    except _DuplicateKeyError as error:
        add(error.key, "this key appears more than once in the same JSON object")
        return None
    except _NonStandardNumberError as error:
        add(FILE_LEVEL, f"contains {error.name}, which is not allowed in standard JSON")
        return None
    if not isinstance(data, dict):
        add(FILE_LEVEL, f"must contain a JSON object at the top level, but found {_describe(data)}")
        return None
    return data


# ---------------------------------------------------------------------------
# Field checks
# ---------------------------------------------------------------------------


def _is_int(value: object) -> bool:
    """True for whole numbers. False for booleans (which Python counts as ints)."""
    return type(value) is int


def _describe(value: object) -> str:
    """Describe a JSON value for an error message."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"the boolean {'true' if value else 'false'}"
    if isinstance(value, (int, float)):
        return f"the number {value!r}"
    if isinstance(value, str):
        shown = value if len(value) <= 60 else value[:57] + "..."
        return f"the string {json.dumps(shown, ensure_ascii=False)}"
    if isinstance(value, list):
        return "a list"
    if isinstance(value, dict):
        return "an object"
    return type(value).__name__


def _range_text(minimum: int | None, maximum: int | None) -> str:
    if minimum is not None and maximum is not None:
        return f"between {minimum} and {maximum}"
    if minimum is not None:
        return f"{minimum} or greater"
    return f"{maximum} or smaller"


class _Fields:
    """Checks the fields of one JSON object and keeps the valid values.

    Valid, parsed values are stored in self.values. Problems are appended to
    the shared problems list. Missing fields are reported once, by
    expect_fields; the other checks skip fields that are missing.
    """

    def __init__(
        self, source: str, data: dict, problems: list[Problem], prefix: str = ""
    ):
        self.source = source
        self.data = data
        self.problems = problems
        self.prefix = prefix
        self.values: dict[str, object] = {}

    def add(self, field: str, message: str) -> None:
        self.problems.append(Problem(self.source, self.prefix + field, message))

    def expect_fields(self, names: tuple[str, ...]) -> None:
        for name in names:
            if name not in self.data:
                self.add(name, "required field is missing")
        for name in self.data:
            if name not in names:
                self.add(
                    name,
                    "unknown field; it is not part of the format (check the spelling)",
                )

    def string(self, field: str, *, allow_empty: bool = True, nullable: bool = False) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        if value is None and nullable:
            self.values[field] = None
            return
        if not isinstance(value, str):
            kind = "a string or null" if nullable else "a string"
            self.add(field, f"must be {kind}, but found {_describe(value)}")
            return
        if not allow_empty and value == "":
            self.add(field, "must not be empty")
            return
        self.values[field] = value

    def integer(
        self,
        field: str,
        *,
        minimum: int | None = None,
        maximum: int | None = None,
        nullable: bool = False,
    ) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        if value is None and nullable:
            self.values[field] = None
            return
        if not _is_int(value):
            kind = "a whole number or null" if nullable else "a whole number"
            self.add(field, f"must be {kind}, but found {_describe(value)}")
            return
        if (minimum is not None and value < minimum) or (
            maximum is not None and value > maximum
        ):
            self.add(
                field,
                f"must be {_range_text(minimum, maximum)}, but found {value}",
            )
            return
        self.values[field] = value

    def boolean(self, field: str) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        if not isinstance(value, bool):
            self.add(
                field,
                f"must be true or false (a JSON boolean), but found {_describe(value)}",
            )
            return
        self.values[field] = value

    def choice(self, field: str, allowed: tuple[str, ...]) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        if not isinstance(value, str) or value not in allowed:
            self.add(
                field,
                f"must be one of: {', '.join(allowed)}; but found {_describe(value)}",
            )
            return
        self.values[field] = value

    def matches(self, field: str, pattern: re.Pattern, explanation: str) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        if not isinstance(value, str) or not pattern.fullmatch(value):
            self.add(field, f"{explanation}, but found {_describe(value)}")
            return
        self.values[field] = value

    def calendar_date(self, field: str, *, nullable: bool = False) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        if value is None and nullable:
            self.values[field] = None
            return
        parsed = None
        if isinstance(value, str) and DATE_PATTERN.fullmatch(value):
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                parsed = None
        if parsed is None:
            alternative = " or null" if nullable else ""
            self.add(
                field,
                "must be a real calendar date written as YYYY-MM-DD"
                f'{alternative}, e.g. "2030-03-01", but found {_describe(value)}',
            )
            return
        self.values[field] = parsed

    def timestamp(self, field: str) -> None:
        if field not in self.data:
            return
        value = self.data[field]
        parsed = None
        if isinstance(value, str) and TIMESTAMP_PATTERN.fullmatch(value):
            try:
                parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M")
            except ValueError:
                parsed = None
        if parsed is None:
            self.add(
                field,
                "must be a real local date and time written as YYYY-MM-DDTHH:MM, "
                'with no seconds and no timezone, e.g. "2030-03-01T09:30", '
                f"but found {_describe(value)}",
            )
            return
        self.values[field] = parsed


def _check_common(fields: _Fields) -> None:
    """Check the three fields that every JSON file must carry."""
    data = fields.data
    if "schema_version" in data and data["schema_version"] != SCHEMA_VERSION:
        fields.add(
            "schema_version",
            f'must be the string "{SCHEMA_VERSION}", '
            f"but found {_describe(data['schema_version'])}",
        )
    if "synthetic" in data and data["synthetic"] is not True:
        fields.add(
            "synthetic",
            "must be the JSON boolean true (every file must be marked as "
            f"synthetic data), but found {_describe(data['synthetic'])}",
        )
    if "fictional_notice" in data and data["fictional_notice"] != FICTIONAL_NOTICE:
        fields.add(
            "fictional_notice",
            f'must be exactly "{FICTIONAL_NOTICE}", '
            f"but found {_describe(data['fictional_notice'])}",
        )


def _check_belongs_to_case(fields: _Fields, case_id: str) -> None:
    """Check that a file's case_id equals the case folder name."""
    if "case_id" not in fields.data:
        return
    value = fields.data["case_id"]
    if value != case_id:
        fields.add(
            "case_id",
            f'must be "{case_id}" (the case folder name), but found {_describe(value)}',
        )
        return
    fields.values["case_id"] = value


def _fmt(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------------------
# Dataset and cases
# ---------------------------------------------------------------------------


def _read_dataset_file(path: Path, problems: list[Problem]) -> dict | None:
    data = _read_json(path, problems)
    if data is None:
        return None
    fields = _Fields(str(path), data, problems)
    fields.expect_fields(DATASET_FIELDS)
    _check_common(fields)
    fields.matches(
        "dataset_id",
        DATASET_ID_PATTERN,
        'must be "SYN-DS-" followed by capital letters, digits or hyphens',
    )
    fields.string("dataset_version", allow_empty=False)
    fields.string("description")

    if "observation_window" in data:
        raw = data["observation_window"]
        if not isinstance(raw, dict):
            fields.add(
                "observation_window",
                f"must be an object with start_day and end_day, but found {_describe(raw)}",
            )
        else:
            window = _Fields(str(path), raw, problems, prefix="observation_window.")
            window.expect_fields(WINDOW_FIELDS)
            window.integer("start_day", minimum=0)
            window.integer("end_day", minimum=0)
            if "start_day" in window.values and "end_day" in window.values:
                start = window.values["start_day"]
                end = window.values["end_day"]
                if start > end:
                    window.add(
                        "end_day",
                        f"must not be smaller than start_day ({start}), but found {end}",
                    )
                else:
                    fields.values["observation_window"] = ObservationWindow(start, end)
    return fields.values


def _load_cases_folder(folder: Path, problems: list[Problem]) -> list[Case]:
    if not folder.is_dir():
        problems.append(Problem(str(folder), FILE_LEVEL, "required cases folder is missing"))
        return []
    cases: list[Case] = []
    found_any = False
    for entry in sorted(folder.iterdir()):
        if entry.name.startswith("."):
            continue  # hidden files such as macOS .DS_Store
        if not entry.is_dir():
            problems.append(
                Problem(
                    str(entry),
                    FILE_LEVEL,
                    "unexpected file in the cases folder; it may only contain case folders",
                )
            )
            continue
        found_any = True
        case = _load_case(entry, problems)
        if case is not None:
            cases.append(case)
    if not found_any:
        problems.append(Problem(str(folder), FILE_LEVEL, "contains no case folders"))
    return cases


def _load_case(folder: Path, problems: list[Problem]) -> Case | None:
    """Read one case folder. Returns None if any problem was found in it."""
    start = len(problems)
    case_id = folder.name
    info = _read_case_file(folder / "case.json", case_id, problems)
    record = _read_record_file(folder / "record.json", case_id, problems)
    documents = _read_documents(folder / "documents", case_id, problems)
    if len(problems) > start:
        return None
    return Case(
        case_id=info["case_id"],
        age_at_infusion=info["age_at_infusion"],
        infusion_date=info["infusion_date"],
        record=record,
        documents=documents,
    )


def _read_case_file(path: Path, folder_name: str, problems: list[Problem]) -> dict | None:
    data = _read_json(path, problems)
    if data is None:
        return None
    fields = _Fields(str(path), data, problems)
    fields.expect_fields(CASE_FIELDS)
    _check_common(fields)
    fields.matches(
        "case_id",
        CASE_ID_PATTERN,
        'must be "SYN-" followed by exactly four digits, e.g. "SYN-0001"',
    )
    if "case_id" in data and data["case_id"] != folder_name:
        fields.add(
            "case_id",
            f'must equal the case folder name "{folder_name}", '
            f"but found {_describe(data['case_id'])}",
        )
    # The >=18 scope rule (clinical-methods §5, A16) is deliberately not
    # enforced here; out-of-scope cases are flagged later by the pipeline.
    fields.integer("age_at_infusion", minimum=0, maximum=120)
    fields.calendar_date("infusion_date")
    return fields.values


# ---------------------------------------------------------------------------
# Research record
# ---------------------------------------------------------------------------


def _read_record_file(
    path: Path, case_id: str, problems: list[Problem]
) -> ResearchRecord | None:
    start = len(problems)
    data = _read_json(path, problems)
    if data is None:
        return None
    fields = _Fields(str(path), data, problems)
    fields.expect_fields(RECORD_FIELDS)
    _check_common(fields)
    _check_belongs_to_case(fields, case_id)

    expected_record_id = f"{case_id}-R"
    if "record_id" in data and data["record_id"] != expected_record_id:
        fields.add(
            "record_id",
            f'must be "{expected_record_id}", but found {_describe(data["record_id"])}',
        )

    versions: list[dict] = []
    if "versions" in data:
        raw = data["versions"]
        if not isinstance(raw, list) or not raw:
            fields.add(
                "versions",
                f"must be a non-empty list of record versions, but found {_describe(raw)}",
            )
        else:
            versions = _read_record_versions(fields, raw, problems)

    if len(problems) > start:
        return None
    return ResearchRecord(
        case_id=case_id,
        record_id=expected_record_id,
        versions=tuple(RecordVersion(**values) for values in versions),
    )


def _read_record_versions(
    fields: _Fields, raw: list, problems: list[Problem]
) -> list[dict]:
    versions: list[dict] = []
    previous_time: datetime | None = None
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            fields.add(f"versions[{index}]", f"must be an object, but found {_describe(entry)}")
            continue
        version = _Fields(fields.source, entry, problems, prefix=f"versions[{index}].")
        version.expect_fields(RECORD_VERSION_FIELDS)

        version.integer("version")
        if "version" in version.values and version.values["version"] != index + 1:
            version.add(
                "version",
                f"must be {index + 1}: record versions are numbered 1, 2, 3 ... "
                f"in list order, but found {version.values['version']}",
            )

        version.timestamp("recorded_at")
        recorded_at = version.values.get("recorded_at")
        if recorded_at is not None:
            if previous_time is not None and recorded_at <= previous_time:
                version.add(
                    "recorded_at",
                    f"must be later than the previous version's recorded_at "
                    f"({_fmt(previous_time)}), but found {_fmt(recorded_at)}; "
                    "record times must be strictly increasing",
                )
            previous_time = recorded_at

        version.boolean("icans_reported")
        version.calendar_date("onset_date", nullable=True)
        # 5 is representable only so the pipeline can flag it later (§8).
        version.integer("max_grade", minimum=1, maximum=5, nullable=True)
        version.string("change_reason", allow_empty=False, nullable=True)
        if index == 0 and version.values.get("change_reason") is not None:
            version.add("change_reason", "must be null for version 1 (nothing has changed yet)")

        if version.values.get("icans_reported") is False:
            for name in ("onset_date", "max_grade"):
                if version.values.get(name) is not None:
                    version.add(name, "must be null when icans_reported is false")

        versions.append(version.values)
    return versions


# ---------------------------------------------------------------------------
# Clinical documents
# ---------------------------------------------------------------------------


def _document_sort_key(document: DocumentVersion) -> tuple[int, int]:
    number = int(document.document_id.rsplit("-D", 1)[1])
    return (number, document.version)


def _read_documents(
    folder: Path, case_id: str, problems: list[Problem]
) -> tuple[DocumentVersion, ...]:
    if not folder.exists():
        return ()  # an absent documents folder means the case has no documents
    if not folder.is_dir():
        problems.append(Problem(str(folder), FILE_LEVEL, "must be a folder"))
        return ()
    start = len(problems)
    parsed: list[tuple[Path, dict]] = []
    # Documents with a file whose own document_id or version could not be
    # read. Their numbering is not checked, to avoid misleading extra errors.
    unresolved: set[str] = set()
    for entry in sorted(folder.iterdir()):
        if entry.name.startswith("."):
            continue  # hidden files such as macOS .DS_Store
        if not entry.is_file() or not DOCUMENT_FILE_PATTERN.fullmatch(entry.name):
            problems.append(
                Problem(
                    str(entry),
                    FILE_NAME,
                    "unexpected item in the documents folder; document files "
                    "must be named <document_id>.v<version>.json",
                )
            )
            continue
        values = _read_document_file(entry, case_id, problems)
        if values is None or "document_id" not in values or "version" not in values:
            unresolved.add(entry.name.rsplit(".v", 1)[0])
        if values is not None:
            parsed.append((entry, values))

    _check_document_versions(folder, parsed, unresolved, problems)

    if len(problems) > start:
        return ()
    documents = [DocumentVersion(**values) for _, values in parsed]
    return tuple(sorted(documents, key=_document_sort_key))


def _read_document_file(path: Path, case_id: str, problems: list[Problem]) -> dict | None:
    data = _read_json(path, problems)
    if data is None:
        return None
    fields = _Fields(str(path), data, problems)
    fields.expect_fields(DOCUMENT_FIELDS)
    _check_common(fields)
    _check_belongs_to_case(fields, case_id)
    fields.matches(
        "document_id",
        re.compile(re.escape(case_id) + r"-D[0-9]{2,}"),
        f'must be "{case_id}-D" followed by at least two digits, e.g. "{case_id}-D01"',
    )
    fields.integer("version", minimum=1)
    fields.choice("status", DOCUMENT_STATUSES)
    fields.choice("note_type", NOTE_TYPES)
    fields.choice("author_role", AUTHOR_ROLES)
    fields.timestamp("documented_at")
    fields.string("amendment_reason", allow_empty=False, nullable=True)
    if fields.values.get("version") == 1 and fields.values.get("amendment_reason") is not None:
        fields.add(
            "amendment_reason",
            "must be null for version 1 (the original document is not an amendment)",
        )
    fields.string("text", allow_empty=False)
    if "\r" in fields.values.get("text", ""):
        fields.add(
            "text",
            'must not contain carriage-return characters ("\\r"); '
            'use "\\n" alone for line breaks',
        )

    if "document_id" in fields.values and "version" in fields.values:
        expected = f"{fields.values['document_id']}.v{fields.values['version']}.json"
        if path.name != expected:
            fields.add(
                FILE_NAME,
                f'must be "{expected}" to match document_id and version, '
                f'but is "{path.name}"',
            )
    return fields.values


def _check_document_versions(
    folder: Path,
    parsed: list[tuple[Path, dict]],
    unresolved: set[str],
    problems: list[Problem],
) -> None:
    """Check version numbering and time order across versions of each document."""
    groups: dict[str, list[tuple[int, Path, dict]]] = {}
    for path, values in parsed:
        if "document_id" in values and "version" in values:
            groups.setdefault(values["document_id"], []).append(
                (values["version"], path, values)
            )

    for document_id, entries in sorted(groups.items()):
        entries.sort(key=lambda entry: (entry[0], entry[1].name))
        numbers = [number for number, _, _ in entries]

        for number in sorted(set(numbers)):
            files = [path.name for n, path, _ in entries if n == number]
            if len(files) > 1:
                problems.append(
                    Problem(
                        str(folder),
                        "version",
                        f"version {number} of {document_id} appears in more than "
                        f"one file: {', '.join(files)}",
                    )
                )

        missing = [n for n in range(1, max(numbers) + 1) if n not in numbers]
        if missing and document_id not in unresolved:
            problems.append(
                Problem(
                    str(folder),
                    "version",
                    f"versions of {document_id} must be numbered 1, 2, 3 ... with "
                    f"no gaps; missing version(s): {', '.join(map(str, missing))}",
                )
            )

        previous: tuple[int, datetime] | None = None
        for number, path, values in entries:
            documented_at = values.get("documented_at")
            if documented_at is None:
                continue
            if previous is not None and documented_at < previous[1]:
                problems.append(
                    Problem(
                        str(path),
                        "documented_at",
                        f"{_fmt(documented_at)} is earlier than version {previous[0]} "
                        f"({_fmt(previous[1])}); documentation time must not "
                        "decrease across versions",
                    )
                )
            previous = (number, documented_at)
