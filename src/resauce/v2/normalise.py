"""Text clean-up that keeps every position traceable to the original note.

Real notes are messier than the synthetic ones: odd invisible characters, abbreviations,
misspellings. v2 cleans the text *before* the v1 extractor reads it. The clean-up must never
break the rule that every quote is the exact original text, so each change is recorded as an
edit and a map from clean-text positions back to original positions is kept.

How a step works
----------------
A step looks at the ORIGINAL text and returns edits: "replace original[start:end] with this".
All steps see the original, never each other's output, so the map stays simple. If two steps
want overlapping text, the earlier step in the list wins and the later one is dropped (and
reported in `NormalisedText.dropped`, never hidden).

This module holds no clinical knowledge. Steps that do (abbreviations, spellings) live in
steps.py and must be listed in docs/clinical-methods.md before they are added.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

# A proposed change to the original text: (start, end, replacement). End is exclusive.
Proposal = tuple[int, int, str]


@dataclass(frozen=True)
class Step:
    """One named clean-up rule."""

    rule_id: str  # short and stable, shown to the user, e.g. "invisible-characters"
    description: str  # plain words: what it does and why
    propose: Callable[[str], list[Proposal]]


@dataclass(frozen=True)
class Edit:
    """One change actually made: original[start:end] became `replacement`."""

    rule_id: str
    start: int  # offsets into the ORIGINAL text
    end: int
    original: str
    replacement: str


@dataclass(frozen=True)
class NormalisedText:
    """The cleaned text, the edits that made it, and the map back to the original."""

    original: str
    text: str
    edits: tuple[Edit, ...]
    dropped: tuple[Edit, ...]  # proposals refused because they overlapped an earlier edit
    _starts: tuple[int, ...]  # for each character of `text`: where its original text begins
    _ends: tuple[int, ...]  # ... and where it ends (exclusive)

    def to_original(self, start: int, end: int) -> tuple[int, int]:
        """Map a span of the cleaned text to the span of original text it came from.

        A span that touches part of a replaced region grows to cover that whole region, so
        the quote is always complete original text. An empty span maps to an empty span.
        """
        if not 0 <= start <= end <= len(self.text):
            raise ValueError(f"span {start}-{end} is outside the cleaned text (length {len(self.text)})")
        if start == end:
            point = self._starts[start] if start < len(self.text) else len(self.original)
            return point, point
        return self._starts[start], self._ends[end - 1]


def normalise(original: str, steps: tuple[Step, ...]) -> NormalisedText:
    """Apply the steps to `original`. With no applicable edits the text is returned unchanged."""
    accepted: list[Edit] = []
    dropped: list[Edit] = []
    for step in steps:
        for start, end, replacement in step.propose(original):
            if not 0 <= start < end <= len(original):
                # An edit must replace or delete at least one original character: text that exists
                # in no original note could never be quoted.
                raise ValueError(f"step {step.rule_id!r} proposed an invalid edit: {start}-{end}")
            edit = Edit(step.rule_id, start, end, original[start:end], replacement)
            overlaps = any(start < e.end and e.start < end for e in accepted)
            (dropped if overlaps else accepted).append(edit)
    accepted.sort(key=lambda e: (e.start, e.end))

    pieces: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    cursor = 0

    def keep(upto: int) -> None:
        nonlocal cursor
        for i in range(cursor, upto):
            pieces.append(original[i])
            starts.append(i)
            ends.append(i + 1)
        cursor = upto

    for edit in accepted:
        keep(edit.start)
        for char in edit.replacement:  # every new character points at the whole original region
            pieces.append(char)
            starts.append(edit.start)
            ends.append(edit.end)
        cursor = edit.end
    keep(len(original))
    return NormalisedText(original, "".join(pieces), tuple(accepted), tuple(dropped), tuple(starts), tuple(ends))
