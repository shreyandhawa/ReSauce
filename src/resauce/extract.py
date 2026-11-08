"""Extraction stage: turn note text into observations with quoted evidence.

Deterministic, standard library only. It assigns no grade and no category:
later stages do that. Every observation carries the exact quoted text it
came from (document ID, version, offsets, quote), checked with
loader.check_evidence_ref. Anything the rules cannot parse is reported as an
"unrecognised" observation, never guessed.

How a document is read:
1. Text is split into lines, lines into sentences (". ", "? ", "! "), and
   sentences into clauses (";", "|", " - ", "->"). Commas do not end a
   clause, so a list such as "No hemorrhage, edema, infarct" stays whole.
2. Each finder (ICE, consciousness, seizure, ...) looks for its closed
   phrase list (resauce.phrases) in each clause. The evidence quote is the
   clause (for chained ICE totals, the part of the clause around one total).
3. Status: "absent" if a negation word comes before the phrase in the
   clause (at most NEGATION_MAX_WORDS words before, not across a scope
   terminator) or a ": none"-style value follows it; "uncertain" if a hedge
   word is present or the line is a plan; otherwise "present".
4. Event time, first rule that applies (clinical-methods §6.1, A26):
   a. a date in the clause (YYYY-MM-DD, or Day +N converted with the
      infusion date). A date written right next to the finding wins;
      otherwise two different dates make the time "unresolved";
   b. an A26 table phrase (overnight, yesterday, this morning, N days ago),
      counted from the documentation date;
   c. another relative phrase: documentation date, marked imprecise;
   d. a date or time earlier in the same line [OPERATIONAL];
   e. the note's header date (and time, if the header gives exactly one)
      [OPERATIONAL]. Steps d and e are ReSauce choices, not §6.1 rules: a
      date written in the note is used before falling back to the
      documentation time;
   f. the documentation time (time-imprecise, §6.1).
   Two different A26 phrases in one clause also make the time "unresolved".
   An event time later than the documentation time is "unresolved".
5. A clause that still contains a neurological word (phrases.NEURO_TRIGGER)
   that no rule used becomes an "unrecognised" observation.
6. [OPERATIONAL] Spelling variants (a ReSauce choice; clinical-methods has no rule
   about spelling): a word of 6 or more letters that is exactly one letter
   away from a word of the closed lists (phrases.VOCABULARY) is tried in
   its place. If the clause then matches a finder, the observation is made
   from the original text, with status "uncertain" (never "present") and the
   note "spelling variant of <word>"; details keep the status the finding
   would have had ("status_without_variant"). This includes a negated
   variant ("no seizre"): we cannot be sure the word means what the list
   word means. There is no list of misspellings; swapped letters and typos
   inside words with optional parts or stems are not found.

Run "python -m resauce.extract <case folder>" to print a case's observations.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from functools import lru_cache

from resauce import phrases as P
from resauce.loader import check_evidence_ref, load_case
from resauce.models import Case, DocumentVersion, EvidenceRef

STATUSES = ("present", "absent", "uncertain")
TIME_SOURCES = ("in_text", "relative", "note_header", "documented_at", "unresolved")

KINDS = (
    "ice_total",
    "ice_partial",
    "consciousness",
    "seizure",
    "eeg_finding",
    "motor_finding",
    "icp_sign",
    "text_only_icp_sign",
    "excluded_symptom",
    "ungradeable_symptom",
    "not_assessable",
    "competing_cause",
    "attribution",
    "assessment_barrier",
    "out_of_scope_mention",
    "unrecognised",
)


@dataclass(frozen=True)
class Observation:
    """One thing a note says, with its quoted evidence and event time."""

    kind: str  # one of KINDS
    value: object  # e.g. ICE total 7, a Table 6 category, a term such as "tremor"
    status: str  # one of STATUSES
    evidence: EvidenceRef
    signed: bool  # whether the document version is signed
    documented_at: datetime
    event_date: date | None  # None only when time_source is "unresolved"
    event_date_end: date | None  # last day of a date range ("overnight"), else None
    event_time: time | None
    time_source: str  # one of TIME_SOURCES
    time_evidence: EvidenceRef | None  # quote of the date, time or phrase used
    details: dict = field(default_factory=dict)  # extra parsed facts
    note: str | None = None  # plain-words cue or reason


def _rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


NEGATION = _rx(P.NEGATION_BEFORE)
PSEUDO_NEGATION = _rx(P.PSEUDO_NEGATION)
TERMINATOR = _rx(P.SCOPE_TERMINATORS)
NEGATION_AFTER = _rx(P.NEGATION_AFTER_VALUE)
HEDGE_BEFORE = _rx(P.HEDGE_BEFORE)
HEDGE_AFTER = _rx(P.HEDGE_AFTER)
PLAN_LINE = _rx(P.PLAN_LINE)
ASSESSMENT_LINE = _rx(P.ASSESSMENT_LINE)
NOT_A_FINDING_AFTER = _rx(P.NOT_A_FINDING_AFTER)
NEGATION_STOPS_AT_COMMA = _rx(P.NEGATION_STOPS_AT_COMMA)

DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
TIME = re.compile(r"(?<![\d.:/])([01]?\d|2[0-3]):([0-5]\d)(?!\d)")
STUDY_DAY = re.compile(P.STUDY_DAY, re.IGNORECASE)
RELATIVE_TABLE = tuple((_rx(p), start, end) for p, start, end in P.RELATIVE_TABLE)
DAYS_AGO = _rx(P.DAYS_AGO)
RELATIVE_OTHER = _rx(P.RELATIVE_OTHER)
HEADER_LABEL = _rx(P.HEADER_LABEL)
CLOCK_HHMM = _rx(P.CLOCK_HHMM)
CLOCK_HHMM_CONTEXT = _rx(P.CLOCK_HHMM_CONTEXT)
WORD = re.compile(r"\b[A-Za-z]{%d,}\b" % P.MIN_VARIANT_LENGTH)

ICE_WORD = _rx(P.ICE_WORD)
ICE_ANCHOR = _rx(P.ICE_ANCHOR)
PAIN_WORD = _rx(P.PAIN_WORD)
ICE_AFTER = _rx(P.ICE_AFTER)
ICE_DOTTED = _rx(P.ICE_DOTTED)
ICE_BARE = _rx(P.ICE_BARE)
ICE_CONDITION = _rx(P.ICE_CONDITION)
ICE_NOT_A_SCORE = _rx(P.ICE_NOT_A_SCORE)
OUT_OF_TEN = re.compile(r"(?<![\d/.])(\d{1,2})\s*/\s*10\b")

NEURO_TRIGGER = _rx(P.NEURO_TRIGGER)
LABEL = _rx(P.FIELD_LABELS)

SENTENCE_END = re.compile(r"(?<!\.\.)(?:(?<=[.!?])|(?<=[.!?][\"')]))\s+")  # not after "....." leaders
CLAUSE_END = re.compile(r";|\||\s-\s|->")


FINDERS = tuple(_rx(pattern) for pattern in P.FINDER_PATTERNS)


@lru_cache(maxsize=None)
def _near_words(word: str) -> tuple[str, ...]:
    """Closed-list words exactly one letter away from a word (none if it is itself listed)."""
    lower = word.lower()
    if lower in P.VOCABULARY:
        return ()
    return tuple(sorted(w for w in P.VOCABULARY if P.one_letter_apart(lower, w)))


@dataclass(frozen=True)
class _Variant:
    """One misspelt word tried as a closed-list word (module docstring, point 6)."""

    typo: str  # the word as written
    word: str  # the closed-list word it was replaced by
    start: int  # where the replacement word sits in `corrected`
    corrected: str  # the clause text with the word replaced

    @property
    def end(self) -> int:
        return self.start + len(self.word)

    def to_original(self, position: int, is_end: bool) -> int:
        """Map an offset in the corrected clause text back to the clause as written."""
        if position <= self.start:
            return position
        if position >= self.end:
            return position + len(self.typo) - len(self.word)
        return self.start + (len(self.typo) if is_end else 0)


class _VariantMatch:
    """A finder match found after correcting one word. It behaves like a regex
    match, but its offsets point into the clause as written."""

    def __init__(self, match: re.Match, variant: _Variant):
        self._match, self._variant = match, variant
        self.variant = (variant.typo, variant.word)

    def group(self, index: int = 0):
        return self._match.group(index)

    def start(self) -> int:
        return self._variant.to_original(self._match.start(), False)

    def end(self) -> int:
        return self._variant.to_original(self._match.end(), True)


def _variants(text: str) -> list[_Variant]:
    """Spelling variants in a clause. A word is kept only if exactly one
    closed-list word, put in its place, makes some finder match there."""
    found = []
    for word in WORD.finditer(text):
        usable = []
        for candidate in _near_words(word.group(0)):
            corrected = text[: word.start()] + candidate + text[word.end() :]
            end = word.start() + len(candidate)
            if any(m.start() < end and word.start() < m.end() for rx in FINDERS for m in rx.finditer(corrected)):
                usable.append(_Variant(word.group(0), candidate, word.start(), corrected))
        if len(usable) == 1:
            found.append(usable[0])
    return found


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def extract_case(case: Case) -> tuple[Observation, ...]:
    """Extract observations from every document version of a case.

    Every evidence reference (and time evidence) is checked with
    check_evidence_ref; a DataFormatError means a bug in this module.
    """
    observations: list[Observation] = []
    for document in case.documents:
        observations.extend(_Reader(case, document).read())
    for observation in observations:
        check_evidence_ref(case, observation.evidence)
        if observation.time_evidence is not None:
            check_evidence_ref(case, observation.time_evidence)
    return tuple(observations)


# ---------------------------------------------------------------------------
# Text pieces
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Span:
    start: int  # offsets into the document text
    end: int


def _pieces(start: int, text: str, splitter: re.Pattern) -> list[_Span]:
    """Split text (which begins at document offset start) into spans."""
    spans, position = [], 0
    for match in splitter.finditer(text):
        spans.append(_Span(start + position, start + match.start()))
        position = match.end()
    spans.append(_Span(start + position, start + len(text)))
    return [span for span in spans if text[span.start - start : span.end - start].strip()]


def _trim(text: str, span: _Span) -> _Span:
    """Shrink a span to drop surrounding spaces and trailing ", and"."""
    piece = text[span.start : span.end]
    left = len(piece) - len(piece.lstrip())
    right_piece = re.sub(r"[\s,;]+(?:and\s*)?$", "", piece.rstrip())
    return _Span(span.start + left, span.start + max(len(right_piece), left + 1))


def _number(word: str) -> int:
    return int(word) if word.isdigit() else P.NUMBER_WORDS[word.lower()]


# ---------------------------------------------------------------------------
# Reading one document version
# ---------------------------------------------------------------------------


@dataclass
class _Clause:
    span: _Span
    line: _Span
    sentence: _Span
    is_plan: bool
    is_assessment: bool
    used: list[_Span] = field(default_factory=list)  # words some rule recognised
    produced: bool = False


class _Reader:
    def __init__(self, case: Case, document: DocumentVersion):
        self.case = case
        self.doc = document
        self.text = document.text
        self.observations: list[Observation] = []
        self.mentions_ice = bool(ICE_WORD.search(self.text))
        # Four-digit numbers equal to one of these years are years, not clock times.
        self.years = ({case.infusion_date.year, document.documented_at.year}
                      | {int(m.group(1)) for m in DATE.finditer(self.text)})
        self.header = self._find_header()

    # -- structure ---------------------------------------------------------

    def _clauses(self) -> list[_Clause]:
        clauses = []
        position = 0
        for raw_line in self.text.split("\n"):
            line = _Span(position, position + len(raw_line))
            position = line.end + 1
            if not raw_line.strip():
                continue
            is_plan = bool(PLAN_LINE.match(raw_line))
            is_assessment = bool(ASSESSMENT_LINE.match(raw_line))
            for sentence in _pieces(line.start, raw_line, SENTENCE_END):
                sentence_text = self.text[sentence.start : sentence.end]
                for clause in _pieces(sentence.start, sentence_text, CLAUSE_END):
                    clauses.append(_Clause(clause, line, sentence, is_plan, is_assessment))
        return clauses

    def read(self) -> list[Observation]:
        clauses = self._clauses()
        self._read_ice_totals(clauses)
        self._read_ice_items(clauses)
        for clause in clauses:
            self._read_clause(clause)
        for clause in clauses:
            self._check_unrecognised(clause)
        return self._deduplicated()

    def _deduplicated(self) -> list[Observation]:
        seen, result = set(), []
        for observation in self.observations:
            key = (observation.kind, str(observation.value), observation.status,
                   observation.evidence.start, observation.evidence.end)
            if key not in seen:
                seen.add(key)
                result.append(observation)
        return result

    # -- making observations ----------------------------------------------

    def _ref(self, span: _Span) -> EvidenceRef:
        return EvidenceRef(
            document_id=self.doc.document_id,
            version=self.doc.version,
            start=span.start,
            end=span.end,
            quote=self.text[span.start : span.end],
        )

    def _add(self, kind, value, status, quote_span, clause, match_span=None,
             details=None, note=None, time_window=None):
        if kind not in KINDS or status not in STATUSES:
            raise ValueError(f"unknown observation kind or status: {kind!r}, {status!r}")
        quote_span = _trim(self.text, quote_span)
        timing = self._event_time(time_window or clause.span, clause.line, match_span or quote_span)
        notes = [n for n in (note, timing["note"]) if n]
        self.observations.append(
            Observation(
                kind=kind,
                value=value,
                status=status,
                evidence=self._ref(quote_span),
                signed=self.doc.status == "signed",
                documented_at=self.doc.documented_at,
                event_date=timing["date"],
                event_date_end=timing["date_end"],
                event_time=timing["time"],
                time_source=timing["source"],
                time_evidence=self._ref(timing["evidence"]) if timing["evidence"] else None,
                details=details or {},
                note="; ".join(notes) or None,
            )
        )
        clause.produced = True

    def _status(self, clause: _Clause, match: _Span, *, negatable: bool = True) -> tuple[str, str | None]:
        """Decide present / absent / uncertain for a phrase inside a clause."""
        before = self.text[clause.span.start : match.start]
        after = self.text[match.end : clause.span.end]
        terminators = list(TERMINATOR.finditer(before))
        if terminators:
            before = before[terminators[-1].end() :]
        if negatable:
            masked = PSEUDO_NEGATION.sub(" ", before)
            negations = list(NEGATION.finditer(masked))
            if negations:
                last, reach = negations[-1], masked[negations[-1].end() :]
                stops = NEGATION_STOPS_AT_COMMA.match(last.group(0)) and "," in reach
                if not stops and len(reach.split()) <= P.NEGATION_MAX_WORDS:
                    return "absent", f"negated by '{last.group(0)}'"
            value = NEGATION_AFTER.match(after)
            if value:
                return "absent", f"negated by '{value.group(0).strip()}'"
        hedge = HEDGE_BEFORE.search(before) or HEDGE_AFTER.match(after)
        if hedge:
            return "uncertain", f"hedged by '{hedge.group(0).strip()}'"
        if clause.is_plan:
            return "uncertain", "in a plan or recommendation line"
        return "present", None

    # -- ICE totals --------------------------------------------------------

    def _read_ice_totals(self, clauses: list[_Clause]) -> None:
        """Find ICE totals, sentence by sentence (totals can chain across ';')."""
        by_sentence: dict[tuple[int, int], list[_Clause]] = {}
        for clause in clauses:
            by_sentence.setdefault((clause.sentence.start, clause.sentence.end), []).append(clause)
        for (s_start, s_end), sentence_clauses in by_sentence.items():
            sentence_text = self.text[s_start:s_end]
            totals: list[tuple[_Span, int, str]] = []  # (span of number, value, form)
            previous_end, chain = 0, False
            for match in OUT_OF_TEN.finditer(sentence_text):
                value = int(match.group(1))
                lead = sentence_text[previous_end : match.start()]
                anchors = list(ICE_ANCHOR.finditer(lead))
                anchored = bool(anchors) and (self.mentions_ice or anchors[-1].group(0) != "total")
                pain_after_anchor = PAIN_WORD.search(lead[anchors[-1].end() :] if anchors else lead)
                is_ice = (
                    value <= 10
                    and not pain_after_anchor
                    and (anchored or chain or ICE_AFTER.match(sentence_text[match.end() :]))
                )
                if is_ice:
                    totals.append((_Span(s_start + match.start(), s_start + match.end()), value, "N/10"))
                    if anchors:
                        start = s_start + previous_end + anchors[0].start()
                        self._mark_used(sentence_clauses, _Span(start, s_start + match.end()))
                    chain = True
                previous_end = match.end()
            for pattern, form in ((ICE_DOTTED, "dotted"), (ICE_BARE, "bare")):
                for match in pattern.finditer(sentence_text):
                    if int(match.group(1)) <= 10:
                        totals.append((_Span(s_start + match.start(1), s_start + match.end(1)), int(match.group(1)), form))
                        self._mark_used(sentence_clauses, _Span(s_start + match.start(), s_start + match.end()))
            totals.sort(key=lambda item: item[0].start)
            for index, (number, value, form) in enumerate(totals):
                clause = next(c for c in sentence_clauses if c.span.start <= number.start < c.span.end)
                window_start = clause.span.start
                window_end = clause.span.end
                if index > 0 and totals[index - 1][0].end > clause.span.start:
                    window_start = totals[index - 1][0].end
                if index + 1 < len(totals) and totals[index + 1][0].start < clause.span.end:
                    window_end = totals[index + 1][0].start
                window = _Span(window_start, window_end)
                status, note = self._status(clause, number, negatable=False)
                condition = ICE_CONDITION.search(self.text[window.start : number.start])
                if condition:
                    status, note = "uncertain", f"a condition, not a result ('{condition.group(0).strip()}')"
                self._add("ice_total", value, status, window, clause, number,
                          details={"form": form}, note=note, time_window=window)

    def _mark_used(self, clauses: list[_Clause], span: _Span) -> None:
        for clause in clauses:
            if span.start < clause.span.end and clause.span.start < span.end:
                clause.used.append(span)

    # -- ICE items (A6, A34) ----------------------------------------------

    def _items_in_line(self, line: _Span) -> list[tuple[str, int, _Span]]:
        """ICE item scores written as 'label N/M', 'label N of M' or 'label (0-M) .... N'."""
        text = self.text[line.start : line.end]
        found = []
        for name, label, maximum in P.ICE_ITEMS:
            pattern = _rx(
                rf"(?:{label})[^\d/\n]{{0,40}}?(\d)\s*(?:/|of)\s*{maximum}\b"
                rf"|(?:{label})\s*\(0-{maximum}\)\s*\.{{2,}}\s*(\d)\b"
            )
            for match in pattern.finditer(text):
                score = int(match.group(1) or match.group(2))
                if score <= maximum:
                    found.append((name, score, _Span(line.start + match.start(), line.start + match.end())))
        for letter, name in P.ICE_ITEM_LETTERS.items():
            maximum = dict((n, m) for n, _, m in P.ICE_ITEMS)[name]
            for match in re.finditer(rf"(?<![\w&]){letter}\s+(\d)\s*/\s*{maximum}\b", text):
                found.append((name, int(match.group(1)), _Span(line.start + match.start(), line.start + match.end())))
        return sorted(found, key=lambda item: item[2].start)

    def _read_ice_items(self, clauses: list[_Clause]) -> None:
        """Group item scores with their total; report items without a total.

        Items on the same line as a total belong to it. A run of item-only
        lines belongs to a total on the line just after or just before it.
        Otherwise items belong to a total within 3 lines after (or else
        before) them. Items with no total are reported as "ice_partial" (A6).
        A complete item set that disagrees with its total is "unrecognised".
        """
        lines = sorted({(c.line.start, c.line.end) for c in clauses})
        totals_by_line: dict[int, list[Observation]] = {}
        for observation in self.observations:
            if observation.kind == "ice_total" and observation.status == "present":
                for start, end in lines:
                    if start <= observation.evidence.start < end:
                        totals_by_line.setdefault(start, []).append(observation)
        items_by_line = {start: self._items_in_line(_Span(start, end)) for start, end in lines}

        groups: list[tuple[list, list[Observation]]] = []
        index = 0
        while index < len(lines):
            start = lines[index][0]
            if not items_by_line[start]:
                index += 1
                continue
            if start in totals_by_line:
                groups.append((items_by_line[start], totals_by_line[start]))
                index += 1
                continue
            run_items, run_end = [], index
            while run_end < len(lines) and items_by_line[lines[run_end][0]] and lines[run_end][0] not in totals_by_line:
                run_items += items_by_line[lines[run_end][0]]
                run_end += 1
            nearby = [lines[i][0] for i in range(run_end, min(run_end + 3, len(lines)))]
            nearby += [lines[i][0] for i in range(index - 1, max(index - 4, -1), -1)]
            owner = next((start for start in nearby if start in totals_by_line), None)
            groups.append((run_items, totals_by_line[owner] if owner is not None else []))
            index = run_end

        for items, totals in groups:
            for clause in clauses:
                for _, _, span in items:
                    if clause.span.start <= span.start < clause.span.end:
                        clause.used.append(span)
            scores = {}
            for name, score, _ in items:
                scores.setdefault(name, []).append(score)
            complete = len(scores) == 5 and all(len(v) == 1 for v in scores.values())
            item_sum = sum(v[0] for v in scores.values()) if complete else None
            span = _Span(items[0][2].start, items[-1][2].end)
            clause = next(c for c in clauses if c.span.start <= span.start < c.span.end)
            details = {"items": {name: v[0] if len(v) == 1 else v for name, v in scores.items()},
                       "all_five_items": complete, "item_sum": item_sum}
            if not totals:
                status = "uncertain" if clause.is_plan else "present"
                self._add("ice_partial", None, status, span, clause, details=details,
                          note="ICE item scores without a stated total (A6, A34)",
                          time_window=_Span(span.start, span.end))
            elif complete and item_sum not in {o.value for o in totals}:
                self._add("unrecognised", "ICE items do not add up to the stated total", "uncertain",
                          span, clause, details={**details, "stated_totals": [o.value for o in totals]},
                          time_window=_Span(span.start, span.end))

    # -- all other finders, clause by clause --------------------------------

    def _read_clause(self, clause: _Clause) -> None:
        text = self.text[clause.span.start : clause.span.end]
        base = clause.span.start
        sentence = self.text[clause.sentence.start : clause.sentence.end]
        line = self.text[clause.line.start : clause.line.end]
        is_imaging = self.doc.note_type == "imaging_report"

        variants = _variants(text)

        def matches(pattern):
            compiled = _rx(pattern)
            spans = []
            for m in compiled.finditer(text):
                spans.append((m.start(), m.end()))
                yield m, _Span(base + m.start(), base + m.end())
            for variant in variants:
                for found in compiled.finditer(variant.corrected):
                    if not (found.start() < variant.end and variant.start < found.end()):
                        continue  # does not use the corrected word
                    m = _VariantMatch(found, variant)
                    if any(m.start() < end and start < m.end() for start, end in spans):
                        continue  # the pattern already matched here without the correction
                    yield m, _Span(base + m.start(), base + m.end())

        def finding(kind, value, m, span, details=None, negatable=True):
            if NOT_A_FINDING_AFTER.match(text[m.end():]):
                clause.used.append(span)
                return
            status, note = self._status(clause, span, negatable=negatable)
            if hasattr(m, "variant"):
                status, note, details = self._as_variant(status, note, details, m.variant)
            clause.used.append(span)
            self._add(kind, value, status, clause.span, clause, span, details=details, note=note)

        for m in LABEL.finditer(text):
            clause.used.append(_Span(base + m.start(), base + m.end()))
        for m in ICE_NOT_A_SCORE.finditer(text):
            clause.used.append(_Span(base + m.start(), base + m.end()))
        if text.strip() == "ICE":
            clause.used.append(clause.span)

        # Level of consciousness (A15).
        taken: list[_Span] = []
        for pattern, category in P.CONSCIOUSNESS:
            for m, span in matches(pattern):
                if any(span.start < t.end and t.start < span.end for t in taken):
                    continue
                taken.append(span)
                finding("consciousness", category, m, span, details={"candidates": (category,)})
        for pattern, candidates in P.CONSCIOUSNESS_AMBIGUOUS:
            for m, span in matches(pattern):
                finding("consciousness", None, m, span, details={"candidates": candidates},
                        negatable=True)
        for m, span in matches(P.CONSCIOUSNESS_UNMAPPED):
            finding("consciousness", None, m, span,
                    details={"candidates": (), "phrase": m.group(0)},
                    negatable=True)
        depressed = bool(taken)
        for m, span in matches(P.CONSCIOUSNESS_AWAKE):
            if depressed:
                clause.used.append(span)  # recognised, but the clause reports depressed consciousness
            else:
                finding("consciousness", P.AWAKE, m, span, details={"candidates": ()})

        # Seizures (Table 6).
        for m, span in matches(P.SEIZURE):
            details = self._seizure_details(text, sentence, line)
            finding("seizure", details.pop("type"), m, span, details=details)
        for pattern, value in P.EEG_FINDINGS:
            for m, span in matches(pattern):
                finding("eeg_finding", value, m, span)

        # Motor findings, excluding weakness from deconditioning (§4.2).
        deconditioning = bool(_rx(P.DECONDITIONING).search(sentence))
        for m, span in matches(P.MOTOR):
            if deconditioning and m.group(0).lower() == "weakness":
                continue
            finding("motor_finding", m.group(0).lower(), m, span)

        # Raised ICP / edema (Table 6) and text-only signs (A12).
        for m, span in matches(P.EDEMA):
            extent, organ, word = (m.group(1) or "").lower(), m.group(2), m.group(3).lower()
            if not organ and (word == "swelling" or not is_imaging):
                continue
            if extent in P.EDEMA_DIFFUSE:
                value = "diffuse cerebral edema"
            elif extent in P.EDEMA_FOCAL:
                value = "focal edema"
            else:
                value = "cerebral edema (extent not stated)"
            finding("icp_sign", value, m, span)
        for pattern, value in P.ICP_SIGNS:
            for m, span in matches(pattern):
                finding("icp_sign", value, m, span)
        for pattern, value in P.TEXT_ONLY_ICP:
            for m, span in matches(pattern):
                finding("text_only_icp_sign", value, m, span)

        # Excluded symptoms (§4.2) and ungradeable symptoms (A21).
        for pattern, value in P.EXCLUDED:
            for m, span in matches(pattern):
                finding("excluded_symptom", value, m, span)
        for m, span in matches(P.HEMORRHAGE):
            if m.group(1) or is_imaging:
                finding("excluded_symptom", "intracranial hemorrhage", m, span)
        if deconditioning:
            for m, span in matches(P.DECONDITIONING_SIGN):
                finding("excluded_symptom", "weakness or balance problem from deconditioning or immobility", m, span)
        for pattern, value in P.UNGRADEABLE:
            for m, span in matches(pattern):
                if deconditioning and value == "unsteadiness":
                    continue
                finding("ungradeable_symptom", value, m, span)

        # "Not assessable" statements (A7). The phrase is itself negative,
        # so no negation check; one observation per clause.
        for m, span in matches(P.NOT_ASSESSABLE):
            if not any(o.kind == "not_assessable" and o.evidence.start >= clause.span.start
                       and o.evidence.end <= clause.span.end for o in self.observations):
                finding("not_assessable", None, m, span, negatable=False)
            clause.used.append(span)

        # Competing causes (A35).
        for pattern, value in P.COMPETING_CAUSES:
            for m, span in matches(pattern):
                finding("competing_cause", value, m, span, details={"term": m.group(0)})

        # Clinician attribution statements (A9).
        for m, span in matches(P.ATTRIBUTION_CUE):
            clause.used.append(span)
            status = "uncertain" if clause.is_plan else "present"
            details = {"cause_text": text[m.end():].strip(" .,:"), "author_role": self.doc.author_role}
            note = None
            if hasattr(m, "variant"):
                status, note, details = self._as_variant(status, note, details, m.variant)
            self._add("attribution", m.group(0).lower(), status, clause.span, clause, span,
                      details=details, note=note)
        if clause.is_assessment:
            for m, span in matches(P.ICANS_NAME):
                clause.used.append(span)
                status, note, details = "present", None, {"author_role": self.doc.author_role}
                if hasattr(m, "variant"):
                    status, note, details = self._as_variant(status, note, details, m.variant)
                self._add("attribution", "assessment names ICANS", status, clause.span, clause, span,
                          details=details, note=note)
                break

        # Assessment barriers (A10) and out-of-scope triggers (§5, A29).
        for pattern, value in P.ASSESSMENT_BARRIERS:
            for m, span in matches(pattern):
                finding("assessment_barrier", value, m, span, details={"term": m.group(0)})
        for pattern, value in P.OUT_OF_SCOPE_MENTIONS:
            for m, span in matches(pattern):
                finding("out_of_scope_mention", value, m, span, details={"term": m.group(0)})

    @staticmethod
    def _as_variant(status: str, note: str | None, details: dict | None, variant: tuple[str, str]):
        """A finding found through a spelling variant is never "present" (module docstring, point 6)."""
        typo, word = variant
        details = {**(details or {}), "spelling_variant_of": word, "written_as": typo,
                   "status_without_variant": status}
        cue = f"spelling variant of {word}"
        return "uncertain", "; ".join(n for n in (note, cue) if n), details

    def _seizure_details(self, clause_text: str, sentence: str, line: str) -> dict:
        """Seizure facts. Duration, termination and repetition come from the
        sentence; return to baseline from the whole line. Facts not
        written stay None."""
        details: dict = {
            "type": "eeg" if (re.search(P.SEIZURE_EEG_CONTEXT, clause_text, re.I)
                              or self.doc.note_type == "eeg_report") else "clinical",
            "duration_text": None, "min_seconds": None, "max_seconds": None,
            "termination": None, "return_to_baseline": None, "repetitive": None,
        }
        duration = _rx(P.SEIZURE_DURATION).search(sentence)
        if duration:
            qualifier = (duration.group(1) or "").lower()
            unit = 60 if duration.group(4).lower().startswith("m") else 1
            low = _number(duration.group(2)) * unit
            high = int(duration.group(3)) * unit if duration.group(3) else low
            details["duration_text"] = duration.group(0).strip()
            if qualifier in ("under", "less than", "<"):
                details["max_seconds"] = high
            elif qualifier in ("over", "more than", ">"):
                details["min_seconds"] = low
            else:
                details["min_seconds"], details["max_seconds"] = low, high
        if _rx(P.SEIZURE_SELF_TERMINATED).search(sentence):
            details["termination"] = "self-terminated"
        elif _rx(P.SEIZURE_WITH_INTERVENTION).search(sentence):
            details["termination"] = "resolved with intervention"
        if _rx(P.SEIZURE_BASELINE_NO).search(line):
            details["return_to_baseline"] = False
        elif _rx(P.SEIZURE_BASELINE_YES).search(line):
            details["return_to_baseline"] = True
        if _rx(P.SEIZURE_REPETITIVE).search(sentence):
            details["repetitive"] = True
        return details

    # -- unrecognised --------------------------------------------------------

    def _check_unrecognised(self, clause: _Clause) -> None:
        text = list(self.text[clause.span.start : clause.span.end])
        for span in clause.used:
            for i in range(max(span.start, clause.span.start), min(span.end, clause.span.end)):
                text[i - clause.span.start] = " "
        leftover = NEURO_TRIGGER.search("".join(text))
        if leftover:
            self._add("unrecognised", "neurological wording not parsed", "uncertain", clause.span, clause,
                      details={"word": leftover.group(0)})

    # -- time --------------------------------------------------------------

    def _dates_in(self, span: _Span) -> list[tuple[date, _Span]]:
        """Calendar dates and Day +N mentions inside a span."""
        text = self.text[span.start : span.end]
        found = []
        for m in DATE.finditer(text):
            try:
                found.append((date(int(m.group(1)), int(m.group(2)), int(m.group(3))),
                              _Span(span.start + m.start(), span.start + m.end())))
            except ValueError:
                continue
        for m in STUDY_DAY.finditer(text):
            if m.group(1):
                sign = -1 if m.group(1) in "-−" else 1
                days = sign * int(m.group(2))
            else:
                days = int(m.group(3) or m.group(4) or m.group(5))
            found.append((self.case.infusion_date + timedelta(days=days),
                          _Span(span.start + m.start(), span.start + m.end())))
        return sorted(found, key=lambda item: item[1].start)

    def _times_in(self, span: _Span) -> list[tuple[time, _Span]]:
        text = self.text[span.start : span.end]
        found = [(time(int(m.group(1)), int(m.group(2))), _Span(span.start + m.start(), span.start + m.end()))
                 for m in TIME.finditer(text)]
        for m in CLOCK_HHMM.finditer(text):
            # HHMM counts only at the start of a line, after a date or Day +N, or after "at".
            position = span.start + m.start()
            if int(m.group(1) + m.group(2)) in self.years:
                continue  # "2030" in a note from 2030 is a year
            line_start = self.text.rfind("\n", 0, position) + 1
            if CLOCK_HHMM_CONTEXT.search(self.text[line_start:position]):
                found.append((time(int(m.group(1)), int(m.group(2))), _Span(position, span.start + m.end())))
        return sorted(found, key=lambda item: item[1].start)

    def _find_header(self) -> dict | None:
        """The note's own date: one date on the first line, or a labelled line near the top."""
        position = 0
        for index, raw_line in enumerate(self.text.split("\n")[: P.HEADER_MAX_LINES]):
            line = _Span(position, position + len(raw_line))
            position = line.end + 1
            dates = self._dates_in(line)
            if not dates or (index > 0 and not HEADER_LABEL.match(raw_line)):
                continue
            if len({d for d, _ in dates}) != 1:
                if index == 0:
                    continue
                return None
            times = self._times_in(line)
            header_time = times[0] if len(times) == 1 else None
            return {"date": dates[0], "time": header_time}
        return None

    def _event_time(self, window: _Span, line: _Span, finding: _Span) -> dict:
        documented = self.doc.documented_at
        result = {"date": None, "date_end": None, "time": None, "source": "unresolved",
                  "evidence": None, "note": None}
        window_text = self.text[window.start : window.end]
        dates = self._dates_in(window)
        times = self._times_in(window)
        nearest_time = min(times, key=lambda t: abs(t[1].start - finding.start)) if times else None

        def evidence(*spans):
            spans = [s for s in spans if s is not None]
            return _Span(min(s.start for s in spans), max(s.end for s in spans))

        distinct = {d for d, _ in dates}
        if len(distinct) > 1:
            after = [(d, s) for d, s in dates if s.start >= finding.end
                     and re.fullmatch(r"\s*(?:on|at|,|\()?\s*", self.text[finding.end : s.start])]
            before = [(d, s) for d, s in dates if s.end <= finding.start
                      and re.fullmatch(r"[\s:,(]*", self.text[s.end : finding.start])]
            attached = after or before  # "8/10 on DATE" wins over a date just before
            if len({d for d, _ in attached}) == 1:
                dates, distinct = attached, {attached[0][0]}
        if len(distinct) > 1:
            result["note"] = "several different dates in the clause; event date not chosen"
            return result
        if distinct:
            day, day_span = dates[0]
            result.update(date=day, source="in_text")
            if nearest_time:
                result["time"] = nearest_time[0]
            result["evidence"] = evidence(day_span, nearest_time[1] if nearest_time else None) \
                if not nearest_time or abs(nearest_time[1].start - day_span.start) < 60 else day_span
        else:
            relative = self._relative(window_text, window.start)
            if relative == "several":
                result["note"] = "several relative time phrases giving different dates; event date not chosen"
                return result
            if relative:
                start_back, end_back, phrase_span, in_table = relative
                if in_table:
                    result.update(date=documented.date() - timedelta(days=start_back), source="relative",
                                  evidence=phrase_span, note="relative time (A26)")
                    if start_back != end_back:
                        result["date_end"] = documented.date() - timedelta(days=end_back)
                    elif nearest_time:
                        result["time"] = nearest_time[0]
                else:
                    result.update(date=documented.date(), source="documented_at", evidence=None,
                                  note=f"relative phrase '{self.text[phrase_span.start:phrase_span.end]}' "
                                       "is not in the A26 table; documentation date used (time-imprecise)")
                return self._not_after_documentation(result)
            earlier_dates = self._dates_in(_Span(line.start, window.start))
            earlier_times = self._times_in(_Span(line.start, window.start))
            if earlier_dates:
                day, day_span = earlier_dates[-1]
                result.update(date=day, source="in_text", evidence=day_span)
            elif self.header:
                day, day_span = self.header["date"]
                result.update(date=day, source="note_header", evidence=day_span)
            else:
                result.update(date=documented.date(), source="documented_at")
            if nearest_time:
                result["time"] = nearest_time[0]
                time_span = nearest_time[1]
            elif earlier_times:
                result["time"], time_span = earlier_times[-1]
            elif result["source"] == "note_header" and self.header["time"]:
                result["time"], time_span = self.header["time"]
            else:
                time_span = None
            if result["source"] == "documented_at":
                result["note"] = "no event date in the note; documentation date used (time-imprecise)"
                if time_span is not None:
                    result["evidence"] = time_span
            elif time_span is not None and abs(time_span.start - result["evidence"].start) < 60:
                result["evidence"] = evidence(result["evidence"], time_span)
        return self._not_after_documentation(result)

    def _relative(self, text: str, offset: int):
        """Find relative time phrases: (days back for start, for end, span, in A26 table).

        Returns "several" when the window holds A26 phrases that give
        different dates, so the caller reports the time as unresolved.
        """
        found = []
        for pattern, start_back, end_back in RELATIVE_TABLE:
            for m in pattern.finditer(text):
                found.append((start_back, end_back, _Span(offset + m.start(), offset + m.end()), True))
        for m in DAYS_AGO.finditer(text):
            days = _number(m.group(1))
            found.append((days, days, _Span(offset + m.start(), offset + m.end()), True))
        if len({(f[0], f[1]) for f in found}) > 1:
            return "several"
        if found:
            return found[0]
        m = RELATIVE_OTHER.search(text)
        if m:
            return 0, 0, _Span(offset + m.start(), offset + m.end()), False
        return None

    def _not_after_documentation(self, result: dict) -> dict:
        """An event cannot happen after it was written down."""
        if result["date"] is None:
            return result
        moment = datetime.combine(result["date"], result["time"] or time(0, 0))
        if moment > self.doc.documented_at:
            return {"date": None, "date_end": None, "time": None, "source": "unresolved",
                    "evidence": result["evidence"],
                    "note": "event time found in the text is later than the documentation time"}
        return result


# ---------------------------------------------------------------------------
# Command line: print the observations of one case
# ---------------------------------------------------------------------------


def _describe(observation: Observation) -> str:
    when = str(observation.event_date) if observation.event_date else "?"
    if observation.event_date_end:
        when += f"..{observation.event_date_end}"
    if observation.event_time:
        when += f" {observation.event_time.strftime('%H:%M')}"
    ref = observation.evidence
    signed = "" if observation.signed else " UNSIGNED"
    value = "" if observation.value is None else f" = {observation.value}"
    if observation.kind == "consciousness" and observation.value is None:
        value = f" = ambiguous, candidates {list(observation.details.get('candidates', ()))}"
        if observation.details.get("phrase"):
            value += f" (phrase '{observation.details['phrase']}' has no approved mapping)"
    line = (f"{ref.document_id}.v{ref.version}{signed} [{ref.start}:{ref.end}] "
            f"{observation.kind}{value} ({observation.status}) | {when} ({observation.time_source})\n"
            f"    \"{ref.quote}\"")
    if observation.note:
        line += f"\n    note: {observation.note}"
    return line


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m resauce.extract <case folder>")
        return 2
    case = load_case(argv[0])
    observations = extract_case(case)
    for observation in observations:
        print(_describe(observation))
    print(f"\n{len(observations)} observation(s) from {len(case.documents)} document version(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
