"""Rules engine: maximum grade, onset, §7 categories and flags for one case.

Input: a loaded case, the observations from resauce.extract, and the
dataset's observation window. Output: one CaseResult whose fields use the
same keys as the intended answers (category, record_value, documented_value,
signed_difference_days, difference_note, readings, evidence,
record_history), so scoring is a direct comparison. Rules cite
docs/clinical-methods.md v0.4.1 (§ and A numbers). Deterministic, standard
library only. The engine never reads reference answers.

How a case is evaluated:
1. Out of scope first (§5, A29): age under 18, a CAPD assessment, a
   documented death, documented developmental delay, or a record Grade 5.
2. Content (resauce.timeline): latest signed version of each document,
   observations dated inside the window, copied-forward notes left out.
3. Each present observation is graded on its Table 6 domain (§3.3, §3.4,
   §4). When a finding can be read more than one way (a competing cause
   with no clinician statement, a consciousness phrase that fits two
   categories, an assessment barrier, conflicting assessments, ICE 0 with
   no consciousness information, a partial ICE, an unresolved event date,
   a rule not implemented), it becomes a "choice" with several options.
4. Every combination of options is one reading. Each reading gives a
   maximum grade (A2), an onset (§6.2) and a category per field (§7.1-7.9).
5. If all readings agree, that category is used (A23). If not, the choices
   that change the category decide the result: "review: ..." for an
   unresolved date or an unimplemented rule, 7.4 for A6 and A33, otherwise
   7.5 with its reason.
6. §7.6 is checked against the record history; §7.10 flags are added.

[OPERATIONAL] engine choices that clinical-methods does not spell out are
marked where they are made, and listed in docs/handoff.md for review.

Run "python -m resauce.engine <case folder>" to print a case's result.
"""

from __future__ import annotations

import itertools
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from resauce import phrases as P
from resauce import timeline as T
from resauce.extract import Observation, extract_case
from resauce.loader import load_case, study_day
from resauce.models import Case, DocumentVersion, ObservationWindow

FIELDS = ("onset", "max_grade")
MAX_READINGS = 1024  # [OPERATIONAL] a computing limit, not a clinical rule

CONSCIOUSNESS_GRADE = {P.SPONTANEOUS: 1, P.VOICE: 2, P.TACTILE: 3, P.UNAROUSABLE: 4}  # Table 6
DEEP_FOCAL_MOTOR = ("hemiparesis", "hemiplegia", "paraparesis", "paraplegia")  # Table 6, Grade 4
ICP_GRADE = {  # Table 6
    "focal edema": 3,
    "diffuse cerebral edema": 4,
    "papilledema": 4,
    "cranial nerve VI palsy": 4,
    "Cushing's triad": 4,
    "decerebrate or decorticate posturing": 4,
}
ICP_TYPE_NOT_STATED = ("cerebral edema (extent not stated)", "posturing (type not stated)")
ICE_KINDS = ("ice_total", "ice_partial")
ICE_ITEM_MAX = {name: maximum for name, _, maximum in P.ICE_ITEMS}

ICANS_NAME = re.compile(P.ICANS_NAME, re.IGNORECASE)
COMPETING_CAUSE = re.compile("|".join(f"(?:{p})" for p, _ in P.COMPETING_CAUSES), re.IGNORECASE)

# Reasons a finding has more than one reading: (name, section, effect).
# effect: "7.5" (ambiguous evidence), "7.4" (insufficient evidence) or "review".
R_ATTRIBUTION = ("attribution", "§3.4, §7.5, A30, A35", "7.5")
R_CONFLICT = ("conflicting assessments", "§6.4, A23", "7.5")
R_BARRIER = ("assessment barrier", "§4.1, A10", "7.5")
R_WORDING = ("consciousness wording", "§7.5, A15", "7.5")
R_A33 = ("ICE 0 with no consciousness information", "§4.1, A33", "7.4")
R_A6 = ("partially completed ICE", "§4.1, A6", "7.4")
R_UNRESOLVED = ("unresolved event date", "§6.1", "review")
R_ICP_TYPE = ("not implemented", "§3.3: edema extent or posturing type not stated", "review")
R_STATUS_EPILEPTICUS = ("not implemented", "§3.3: status epilepticus without a stated duration", "review")
R_SEIZURE_DURATION = ("not implemented", "§3.3: seizure duration range that spans 5 minutes", "review")
R_MOTOR = ("not implemented", "§3.3: motor finding not named as hemiparesis or paraparesis", "review")


def _top(grades) -> int:
    """Highest grade among options; None (not counted) counts as 0."""
    return max((g for g in grades if g is not None), default=0)


def ice_grade(total: int) -> int:
    """Table 6 ICE domain; 10 is no impairment (Grade 0, §3.3)."""
    if total == 10:
        return 0
    if total >= 7:
        return 1
    if total >= 3:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Result shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One graded observation in one reading."""

    obs: Observation
    grade: int
    label: str


@dataclass
class Choice:
    """A finding (or a group of conflicting ones) with several readings."""

    about: str
    reasons: list  # of R_* tuples
    options: list  # of (label, tuple[Finding, ...])
    evidence: list  # of (Observation, role)


@dataclass
class Outcome:
    """One field in one reading."""

    category: str
    value: object  # documented_value
    grade: int | None = None
    diff: int | None = None
    note: str | None = None
    evidence: list = field(default_factory=list)  # (Observation, role)
    deciding: list = field(default_factory=list)  # observations the field rests on


@dataclass
class CaseResult:
    case_id: str
    out_of_scope: dict | None
    fields: dict
    case_flags: dict | None
    other_flags: list
    review_items: list

    def to_dict(self) -> dict:
        return {"case_id": self.case_id, "out_of_scope": self.out_of_scope, "fields": self.fields,
                "case_flags": self.case_flags, "other_flags": self.other_flags,
                "review_items": self.review_items}


def _evidence(pairs) -> list[dict]:
    """Evidence entries for (observation, role) pairs, with time evidence, no duplicates."""
    result, seen = [], set()
    for obs, role in pairs:
        refs = [(obs.evidence, role)]
        if obs.time_evidence is not None and role.startswith("first qualifying"):
            refs.append((obs.time_evidence, "time of " + role))
        for ref, r in refs:
            key = (ref.document_id, ref.version, ref.start, ref.end)
            if key not in seen:
                seen.add(key)
                result.append(T.evidence_dict(ref, r))
    return result


def _date_value(case: Case, first: date, last: date) -> dict:
    if first == last:
        return {"date": first.isoformat(), "study_day": study_day(case, first)}
    return {"range": [first.isoformat(), last.isoformat()],
            "study_days": [study_day(case, first), study_day(case, last)]}


def _value_text(value) -> str:
    if isinstance(value, dict):
        if "grade" in value:
            return f"Grade {value['grade']}"
        if "date" in value:
            return value["date"]
        if "range" in value:
            return f"{value['range'][0]} to {value['range'][1]}"
        return next(iter(value.values()))
    return str(value)


def _overlaps(a: Observation, b: Observation) -> bool:
    return (T.version_id(a) == T.version_id(b)
            and a.evidence.start < b.evidence.end and b.evidence.start < a.evidence.end)


# ---------------------------------------------------------------------------
# The engine for one case
# ---------------------------------------------------------------------------


class _Engine:
    def __init__(self, case: Case, observations, window: ObservationWindow,
                 swap: DocumentVersion | None = None):
        self.case, self.observations, self.window = case, observations, window
        self.sel = T.select(case, observations, window, swap)
        self.used = [o for o in self.sel.used if o.status == "present"]
        self.undated = [o for o in self.sel.undated if o.status == "present"]
        self.context = [o for o in self.sel.context if o.status == "present"]
        self.groups: dict = {}  # an assessment: same document version, same event date
        for o in self.used + self.undated:
            self.groups.setdefault((T.version_id(o), o.event_date), []).append(o)
        self.causes = [o for o in self.context if o.kind == "competing_cause"]
        self.statements = [o for o in self.context if o.kind == "attribution"]
        self.barriers = [o for o in self.context if o.kind == "assessment_barrier"]
        self.hemorrhages = [o for o in self.context
                            if o.kind == "excluded_symptom" and o.value == "intracranial hemorrhage"]
        self.excluded_by_clinician: list[Observation] = []
        self.fixed, self.choices = self._findings()
        self.grade0 = self._formal_grade0()
        self.not_assessable = [o for o in self.used if o.kind == "not_assessable"]

    # -- grading one observation (§3.3, §3.4, §4) ---------------------------

    def _group(self, o: Observation) -> list[Observation]:
        return self.groups.get((T.version_id(o), o.event_date), [])

    def _ice(self, o: Observation, total: int, label: str):
        if total != 0:
            return [ice_grade(total)], [], label
        # §3.4 footnote ^, §4.1: ICE 0 needs the consciousness context.
        levels = {g.value for g in self._group(o) if g.kind == "consciousness"}
        unarousable = P.UNAROUSABLE in levels
        arousable = bool(levels & {P.AWAKE, P.SPONTANEOUS, P.VOICE, P.TACTILE})
        if unarousable and not arousable:
            return [4], [], label + " in an unarousable patient"
        if arousable and not unarousable:
            return [3], [], label + " in an arousable patient"
        return [3, 4], [R_A33], label + " with no consciousness information"

    def _base(self, o: Observation):
        """(grade options, reasons, label), or None if the observation is not graded."""
        kind, value = o.kind, o.value
        if kind == "ice_total":
            return self._ice(o, value, f"ICE {value}/10")
        if kind == "ice_partial":
            details = o.details
            if details.get("all_five_items") and details.get("item_sum") is not None:
                return self._ice(o, details["item_sum"], f"ICE items summing to {details['item_sum']}/10")
            # A6: a partial ICE gives no total. It is never graded; it only
            # matters if one of the totals it allows would change a category
            # (then 7.4). Possible totals: unscored items at 0 or full marks.
            low = high = 0
            for name, maximum in ICE_ITEM_MAX.items():
                scores = details["items"].get(name)
                scores = scores if isinstance(scores, list) else [scores] if scores is not None else None
                low += min(scores) if scores else 0
                high += max(scores) if scores else maximum
            grades = {ice_grade(t) for t in range(low, high + 1)}
            if low == 0:
                grades.add(4)  # A33: ICE 0 without consciousness information
            return [None, *sorted(grades)], [R_A6], f"partial ICE ({low}-{high}/10 possible)"
        if kind == "consciousness":
            if value in CONSCIOUSNESS_GRADE:
                # A3: "awakens spontaneously" counts only when drowsiness is documented.
                if value == P.SPONTANEOUS and not self._drowsy(o):
                    return None
                return [CONSCIOUSNESS_GRADE[value]], [], value
            candidates = o.details.get("candidates") or ()
            if value is None and candidates:
                return (sorted({CONSCIOUSNESS_GRADE[c] for c in candidates}), [R_WORDING],
                        "consciousness wording that fits " + " or ".join(candidates))
            return None  # awake, or a word with no approved mapping (A15)
        if kind == "seizure":
            details = o.details
            label = f"{value} seizure"
            low, high = details.get("min_seconds"), details.get("max_seconds")
            if low is not None and (low > 300 or (high is None and low >= 300)):
                # "over 5 minutes" stores its bound as min_seconds with no maximum.
                return [4], [], label + " lasting more than 5 minutes"
            if low is not None and high is not None and low <= 300 < high:
                return [3, 4], [R_SEIZURE_DURATION], label + f" lasting {details.get('duration_text')}"
            if details.get("repetitive") and details.get("return_to_baseline") is False:
                return [4], [], "repetitive seizures without return to baseline"
            if "status epilepticus" in o.evidence.quote.lower():
                return [3, 4], [R_STATUS_EPILEPTICUS], "status epilepticus"
            return [3], [], label
        if kind == "motor_finding":
            if value in DEEP_FOCAL_MOTOR:
                return [4], [], value
            # Table 6 says "deep focal motor weakness such as hemiparesis or
            # paraparesis"; other motor words have no approved mapping.
            return [None, 4], [R_MOTOR], value
        if kind == "icp_sign":
            # §4.2: intracranial hemorrhage, with or without edema, is excluded.
            if any(_overlaps(o, h) for h in self.hemorrhages):
                return None
            if value in ICP_GRADE:
                return [ICP_GRADE[value]], [], value
            if value in ICP_TYPE_NOT_STATED:
                return [3, 4], [R_ICP_TYPE], value
        return None

    def _drowsy(self, o: Observation) -> bool:
        return any(g.kind == "consciousness" and g.value is None and not g.details.get("candidates")
                   for g in self._group(o))

    def _attribution(self, o: Observation) -> str:
        """"kept", "excluded" (a clinician names another cause), "competing" or "none".

        [OPERATIONAL] A clinician statement settles attribution only when it
        is written in the same clause as the finding. A statement naming ICANS
        keeps the finding; one naming a listed competing cause, or saying
        "unrelated", excludes it. Other statements settle nothing.
        """
        for statement in self.statements:
            if not _overlaps(statement, o):
                continue
            if statement.value == "assessment names ICANS":
                return "kept"
            cause = statement.details.get("cause_text", "")
            if ICANS_NAME.search(cause):
                return "kept"
            if statement.value in ("unrelated", "not related") or COMPETING_CAUSE.search(cause):
                return "excluded"
        return "competing" if self._near_causes(o) else "none"

    def _near_causes(self, o: Observation) -> list[Observation]:
        """A30: competing causes in the same note, or within the 24 hours before."""
        return [c for c in self.causes
                if T.version_id(c) == T.version_id(o) or T.within_24_hours_before(c, o)]

    def _findings(self):
        """Fixed findings, and choices for findings with several readings."""
        entries = []  # (observation, grade options, reasons, label)
        for o in self.used + self.undated:
            base = self._base(o)
            if base is None:
                continue
            grades, reasons, label = list(base[0]), list(base[1]), base[2]
            if _top(grades) >= 1:
                attribution = self._attribution(o)
                if attribution == "excluded":
                    self.excluded_by_clinician.append(o)
                    continue
                if attribution == "competing":
                    grades.append(None)
                    reasons.append(R_ATTRIBUTION)
                if self.barriers and o.kind in ICE_KINDS:
                    grades.append(None)
                    reasons.append(R_BARRIER)
                if o.time_source == "unresolved":
                    grades.append(None)
                    reasons.append(R_UNRESOLVED)
            entries.append((o, list(dict.fromkeys(grades)), list(dict.fromkeys(reasons)), label))

        fixed, choices = [], []
        for group in self._conflicts(entries):
            options, reasons, evidence = [], [R_CONFLICT], []
            for o, grades, own_reasons, label in group:
                reasons += [r for r in own_reasons if r not in reasons]
                evidence.append((o, f"conflicting assessment: {label}"))
                for g in grades:
                    text = "not counted" if g is None else f"Grade {g}"
                    options.append((f"use {label} at {o.event_time} ({text})",
                                    () if g is None else (Finding(o, g, label),)))
            choices.append(Choice("assessments within one hour", reasons, options, evidence))
            entries = [e for e in entries if e not in group]
        for o, grades, reasons, label in entries:
            if len(grades) == 1:
                if grades[0] is not None and grades[0] >= 1:
                    fixed.append(Finding(o, grades[0], label))
                continue
            options = [("not counted" if g is None else f"Grade {g}",
                        () if g is None else (Finding(o, g, label),)) for g in grades]
            evidence = [(o, f"finding with several readings: {label}")]
            if R_ATTRIBUTION in reasons:
                evidence += [(c, "competing cause (A30)") for c in self._near_causes(o)]
            if R_BARRIER in reasons:
                evidence += [(b, "assessment barrier (A10)") for b in self.barriers]
            where = o.event_date.isoformat() if o.event_date else "date unresolved"
            choices.append(Choice(f"{label} ({T.version_id(o)}, {where})", reasons, options, evidence))
        return fixed, choices

    @staticmethod
    def _conflicts(entries) -> list[list]:
        """§6.4: ICE totals in different documents within one hour that give different grades."""
        timed = [e for e in entries if e[0].kind in ICE_KINDS and e[0].event_date and e[0].event_time
                 and e[0].event_date_end is None]
        parent = {id(e): id(e) for e in timed}

        def root(x):
            while parent[x] != x:
                x = parent[x]
            return x

        for a, b in itertools.combinations(timed, 2):
            gap = abs(T.earliest_moment(a[0]) - T.earliest_moment(b[0]))
            if (a[0].evidence.document_id != b[0].evidence.document_id
                    and gap <= timedelta(minutes=60) and set(a[1]) != set(b[1])):
                parent[root(id(a))] = root(id(b))
        groups: dict = {}
        for e in timed:
            groups.setdefault(root(id(e)), []).append(e)
        return [g for g in groups.values() if len(g) > 1]

    def _formal_grade0(self) -> dict:
        """§3.3: day -> ICE 10 observations of assessments with no domain criterion met."""
        days: dict = {}
        for (_, day), members in self.groups.items():
            if day is None:
                continue
            tens = [o for o in members if (o.kind == "ice_total" and o.value == 10)
                    or (o.kind == "ice_partial" and o.details.get("all_five_items")
                        and o.details.get("item_sum") == 10)]
            if tens and not any((b := self._base(o)) and _top(b[0]) >= 1 for o in members):
                days.setdefault(day, []).extend(tens)
        return days

    # -- one reading -------------------------------------------------------

    def _onset_outcome(self, qualifying: list[Finding]) -> Outcome:
        record = self.case.record.current
        has_q = bool(qualifying)
        onset = None
        if has_q and all(f.obs.event_date for f in qualifying):
            first, last, deciding = T.onset_from([(*T.days(f.obs), f) for f in qualifying])
            onset = (first, last, deciding)
        value = _date_value(self.case, onset[0], onset[1]) if onset else (
            {"undetermined": "a qualifying finding has an unresolved event date"} if has_q else "none found")
        out = Outcome("", value)
        if onset:
            out.evidence = [(f.obs, f"first qualifying finding ({f.label}, Grade {f.grade})") for f in onset[2]]
            out.deciding = [f.obs for f in onset[2]]
        record_date = record.onset_date

        def grade0_on_record_date():
            found = self.grade0.get(record_date, [])
            out.evidence += [(o, "formal Grade 0 assessment on the record's onset date") for o in found]
            out.deciding += found
            return bool(found)

        if not record.icans_reported:  # §7.9
            if has_q:
                out.category, out.note = "7.1", "record has no onset"
            else:
                out.category = self._no_icans_category(out)
        elif record_date is None:  # §7.8
            out.category, out.note = "7.8", "record has no onset"
        elif not has_q:  # §7.9(c)
            out.note = "no documented onset"
            out.category = "7.1" if grade0_on_record_date() else "7.4"
        elif onset is None:
            out.category = "review: unresolved event date (§6.1)"
        else:
            first, last = onset[0], onset[1]
            if first <= record_date <= last:
                out.category, out.diff = "7.7", 0
            elif record_date > last:
                out.category, out.diff = "7.1", (record_date - last).days
            else:  # record earlier than the documented onset (§7.1, A17, A18)
                out.diff = (record_date - first).days
                out.category = "7.1" if grade0_on_record_date() else "7.4"
        return out

    def _grade_outcome(self, qualifying: list[Finding]) -> Outcome:
        record = self.case.record.current
        grade = max((f.grade for f in qualifying), default=0)
        if qualifying or self.grade0:
            value = {"grade": grade}
        else:
            value = {"undetermined": "no qualifying finding and no formal Grade 0 assessment"}
        out = Outcome("", value, grade=grade)
        top = [f for f in qualifying if f.grade == grade]
        out.evidence = [(f.obs, f"highest grade: {f.label} (Grade {f.grade})") for f in top]
        out.deciding = [f.obs for f in top]

        def unassessed(category_otherwise):  # A25
            if self.not_assessable:
                out.evidence += [(o, "documented 'not assessable' period (A7)") for o in self.not_assessable]
                return "7.4"
            return category_otherwise

        if not record.icans_reported:  # §7.9
            out.category = "7.2" if qualifying else self._no_icans_category(out)
        elif record.max_grade is None:  # §7.8
            out.category, out.note = "7.8", "record has no maximum grade"
        elif not qualifying:  # §7.9(c)
            out.category = unassessed("7.3")
        elif grade > record.max_grade:
            out.category = "7.2"
        elif grade < record.max_grade:
            out.category = unassessed("7.3")
        else:
            out.category = "7.7"
        return out

    def _no_icans_category(self, out: Outcome) -> str:
        """§7.9(b), A21: 7.7 needs a formal Grade 0 assessment and no 'not assessable' period."""
        for day in sorted(self.grade0):
            out.evidence += [(o, "formal Grade 0 assessment") for o in self.grade0[day]]
            out.deciding += self.grade0[day]
        if self.not_assessable:
            out.evidence += [(o, "documented 'not assessable' period (A7)") for o in self.not_assessable]
            return "7.4"
        return "7.7" if self.grade0 else "7.4"

    # -- all readings --------------------------------------------------------

    def field_results(self) -> dict:
        """Field name -> (combined field dict, list of outcomes)."""
        sizes = [len(c.options) for c in self.choices]
        total = 1
        for size in sizes:
            total *= size
        if total > MAX_READINGS:
            review = f"review: not implemented (§7.5 readings: more than {MAX_READINGS}, an engine limit)"
            return {name: (self._field_dict(name, Outcome(review, None), [], []), [])
                    for name in FIELDS}
        assignments = list(itertools.product(*[range(s) for s in sizes]))
        readings = []
        for assignment in assignments:
            findings = list(self.fixed)
            for choice, index in zip(self.choices, assignment):
                findings += choice.options[index][1]
            qualifying = [f for f in findings if f.grade >= 1]
            readings.append({"onset": self._onset_outcome(qualifying),
                             "max_grade": self._grade_outcome(qualifying)})
        results = {}
        for name in FIELDS:
            outcomes = [r[name] for r in readings]
            results[name] = (self._combine(name, assignments, outcomes), outcomes)
        return results

    def _label(self, assignment, only=None) -> str:
        """Describe a reading by its options (only those of the listed choice indices, if given)."""
        parts = [f"{c.about}: {c.options[i][0]}" for n, (c, i) in enumerate(zip(self.choices, assignment))
                 if only is None or n in only]
        return "; ".join(parts) or "single reading"

    def _combine(self, name: str, assignments, outcomes: list[Outcome]) -> dict:
        categories = {o.category for o in outcomes}
        decisive_index = {i for i in range(len(self.choices)) if self._changes(i, assignments, outcomes)}
        readings = []
        if len(outcomes) > 1:
            seen = set()
            for assignment, o in zip(assignments, outcomes):
                key = (json.dumps(o.value, sort_keys=True), o.category)
                if key not in seen:
                    seen.add(key)
                    readings.append({"reading": self._label(assignment, decisive_index or None),
                                     "value": o.value, "category": o.category})
        if len(categories) == 1:  # A23: every reading gives the same category
            if name == "max_grade":
                chosen = min(outcomes, key=lambda o: o.grade)
            else:
                chosen = min(outcomes, key=lambda o: abs(o.diff) if o.diff is not None else 0)
            return self._field_dict(name, chosen, readings, [])

        decisive = [c for i, c in enumerate(self.choices) if i in decisive_index]
        reasons = list(dict.fromkeys(r for c in decisive for r in c.reasons))
        review = [r for r in reasons if r[2] == "review"]
        chosen = outcomes[0]
        extra = [pair for c in decisive for pair in c.evidence]
        evidence = [pair for o in outcomes for pair in o.evidence]
        if review:
            r = review[0]
            if r is R_UNRESOLVED:
                category = "review: unresolved event date (§6.1)"
            else:
                category = f"review: not implemented ({r[1]})"
            value = {"undetermined": "; ".join(f"{_value_text(x['value'])} ({x['category']}) if {x['reading']}"
                                               for x in readings)}
        elif any(r[2] == "7.4" for r in reasons):
            category = "7.4"
            if name == "max_grade":
                grades = [o.grade for o in outcomes]
                value = {"range": [min(grades), max(grades)]}
            else:
                value = {"undetermined": "; ".join(f"{_value_text(x['value'])} if {x['reading']}" for x in readings)}
        else:
            category = "7.5"
            value = {"undetermined": "; ".join(f"{_value_text(x['value'])} if {x['reading']}" for x in readings)}
        note = "reason: " + ", ".join(f"{r[0]} ({r[1]})" for r in reasons)
        combined = Outcome(category, value, grade=chosen.grade, note=note,
                           evidence=evidence, deciding=[d for o in outcomes for d in o.deciding])
        return self._field_dict(name, combined, readings, extra)

    def _changes(self, index: int, assignments, outcomes) -> bool:
        """Does changing this one choice alone change the category?"""
        groups: dict = {}
        for assignment, o in zip(assignments, outcomes):
            rest = assignment[:index] + assignment[index + 1:]
            groups.setdefault(rest, set()).add(o.category)
        return any(len(c) > 1 for c in groups.values())

    def _field_dict(self, name: str, out: Outcome, readings: list, extra_evidence: list) -> dict:
        record = self.case.record.current
        if name == "onset":
            record_value = record.onset_date.isoformat() if record.onset_date else None
        else:
            record_value = record.max_grade
        return {
            "category": out.category,
            "record_value": record_value,
            "documented_value": out.value,
            "signed_difference_days": out.diff if name == "onset" else None,
            "difference_note": out.note,
            "readings": readings,
            "evidence": _evidence(out.evidence + extra_evidence),
            "record_history": None,
            "_deciding": out.deciding,
        }

    # -- §7.6 legitimate revision (A28) -------------------------------------

    def apply_record_history(self, name: str, result: dict) -> dict | None:
        """Fill record_history; turn 7.7 into 7.6 when (a), (b) and (c) hold.

        Returns a "revision without new documentation" flag, or None.
        """
        versions = self.case.record.versions
        if len(versions) < 2:
            return None

        def value(v):
            return (v.icans_reported, v.onset_date if name == "onset" else v.max_grade)

        changes = [i for i in range(1, len(versions)) if value(versions[i]) != value(versions[i - 1])]
        a = bool(changes)
        b = result["category"] == "7.7"
        c = None
        if not a:
            explanation = "The value is the same in every record version, so (a) fails and the field is categorised normally."
        elif not b:
            explanation = (f"The value changed in record v{versions[changes[-1]].version}, but the current value "
                           f"does not meet 7.7, so the usual category applies.")
        else:
            previous, change = versions[changes[-1] - 1], versions[changes[-1]]
            supporting = []
            for o in result["_deciding"]:
                document = self.case.get_document_version(o.evidence.document_id, o.evidence.version)
                if previous.recorded_at < document.documented_at <= change.recorded_at:
                    supporting.append(document.version_id)
            c = bool(supporting)
            if c:
                result["category"] = "7.6"
                explanation = (f"Changed in record v{change.version}; {', '.join(sorted(set(supporting)))} "
                               f"was documented after v{previous.version} and no later than v{change.version}.")
            else:
                explanation = (f"Changed in record v{change.version}; no supporting document version was "
                               f"documented after v{previous.version} ({previous.recorded_at.isoformat()}) "
                               f"and no later than v{change.version} ({change.recorded_at.isoformat()}).")
        result["record_history"] = {"a": a, "b": b, "c": c, "explanation": explanation}
        if a and b and not c:
            return {"flag": "revision without new documentation", "field": name, "detail": explanation,
                    "evidence": _evidence([(o, "evidence for the current value") for o in result["_deciding"]])}
        return None

    # -- §7.10 flags ----------------------------------------------------------

    def possible_qualifying_days(self) -> set:
        days = set()
        for f in self.fixed:
            days.update(_each_day(f.obs))
        for choice in self.choices:
            if R_A6 in choice.reasons or R_MOTOR in choice.reasons:
                continue  # no total (A6) or no approved mapping: not a qualifying finding (A34)
            for _, findings in choice.options:
                for f in findings:
                    if f.obs.event_date:
                        days.update(_each_day(f.obs))
        return days

    def case_flags(self) -> dict:
        gradeable = set(self.possible_qualifying_days())
        for o in self.used:
            if o.kind == "ice_total" or (o.kind == "ice_partial" and o.details.get("all_five_items")):
                gradeable.update(_each_day(o))
        gradeable_days = {study_day(self.case, d) for d in gradeable}
        periods = []
        for o in self.not_assessable:
            days = sorted({study_day(self.case, d) for d in _each_day(o)
                           if self.window.start_day <= study_day(self.case, d) <= self.window.end_day})
            periods.append({"days": days, "evidence": _evidence([(o, "not assessable (A7)")])})
        symptoms = [o for o in self.used if o.kind == "ungradeable_symptom"
                    or (o.kind == "motor_finding" and o.value not in DEEP_FOCAL_MOTOR)]
        return {
            "unassessed_period": {
                "days_without_gradeable_assessment": [
                    d for d in range(self.window.start_day, self.window.end_day + 1) if d not in gradeable_days],
                "not_assessable_periods": periods,
            },
            "ungradeable_neurological_symptom": [
                {"day": study_day(self.case, o.event_date),
                 "evidence": _evidence([(o, f"ungradeable neurological symptom: {o.value}")])}
                for o in symptoms],
        }

    def other_flags(self, fields: dict) -> list:
        flags = list(self.sel.flags)
        if self.sel.outside_window:
            flags.append({"flag": "outside observation window", "field": None,
                          "detail": f"{len(self.sel.outside_window)} observation(s) dated outside Day "
                                    f"{self.window.start_day} to Day +{self.window.end_day}; not used (§6.5, A32).",
                          "evidence": _evidence([(o, f"outside the window: {o.kind}")
                                                 for o in self.sel.outside_window])})
        for o in self.used:
            if o.kind == "text_only_icp_sign":
                flags.append({"flag": "text-only ICP sign", "field": "max_grade",
                              "detail": f"'{o.value}' is a raised-ICP sign in the source text but not in "
                                        "Table 6; not graded (§3.3, A12).",
                              "evidence": _evidence([(o, "text-only ICP sign")])})
        for o in fields["onset"]["_deciding"]:
            if o.time_source == "documented_at":
                flags.append({"flag": "time-imprecise", "field": "onset",
                              "detail": "no event time in the note; documentation time used (§6.1).",
                              "evidence": _evidence([(o, "onset finding dated by documentation time")])})
            elif o.time_source == "relative":
                flags.append({"flag": "relative time", "field": "onset",
                              "detail": "event time from a relative phrase (§6.1, A26).",
                              "evidence": _evidence([(o, "onset finding dated by a relative phrase")])})
        record = self.case.record.current
        if record.icans_reported and record.onset_date:
            day = record.onset_date
            symptoms = [o for o in self.used if day in _each_day(o) and (
                o.kind in ("excluded_symptom", "ungradeable_symptom")
                or (o.kind == "motor_finding" and o.value not in DEEP_FOCAL_MOTOR))]
            if symptoms and day not in self.possible_qualifying_days():
                flags.append({"flag": "record date matches an excluded or sub-threshold symptom",
                              "field": "onset", "detail": "§7.1, A24",
                              "evidence": _evidence([(o, f"{o.kind}: {o.value}") for o in symptoms])})
        qualifying_days = sorted(self.possible_qualifying_days())
        for day in sorted(self.grade0):
            if any(d < day for d in qualifying_days) and any(d > day for d in qualifying_days):
                flags.append({"flag": "recurrence", "field": None,
                              "detail": f"formal Grade 0 assessment on Day +{study_day(self.case, day)} "
                                        "between qualifying findings (§6.5).",
                              "evidence": _evidence([(o, "documented full resolution") for o in self.grade0[day]])})
                break
        return flags

    def review_items(self) -> list:
        items = []
        for o in self.undated:
            if o.kind in T.WINDOW_FLAG_KINDS:
                items.append({"rule": "§6.1", "detail": f"{o.kind} with an unresolved event date; never given a date",
                              "evidence": _evidence([(o, o.note or "unresolved event date")])})
        for o in self.sel.used:
            if o.kind == "unrecognised":
                items.append({"rule": "extraction", "detail": f"unrecognised text: {o.value}",
                              "evidence": _evidence([(o, "not parsed by the extractor")])})
        for copy, original in self.sel.copied:
            items.append({"rule": "§6.4, A13, A31",
                          "detail": f"{copy.version_id} repeats {original.version_id} apart from dates and "
                                    "times; not used as new evidence", "evidence": []})
        for o in self.excluded_by_clinician:
            items.append({"rule": "§3.4, A9", "detail": f"{o.kind} attributed to another cause by a clinician; not graded",
                          "evidence": _evidence([(o, "finding attributed elsewhere")])})
        return items


def _each_day(o: Observation) -> list[date]:
    if o.event_date is None:
        return []
    first, last = T.days(o)
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def _out_of_scope(case: Case, observations) -> dict | None:
    """§5, A29. Mentions count in any document version, signed or not."""
    if case.age_at_infusion < 18:
        return {"reason": "age under 18", "source": f"case.json age_at_infusion = {case.age_at_infusion}",
                "evidence": []}
    for o in observations:
        if o.kind == "out_of_scope_mention" and o.status == "present":
            return {"reason": o.value, "source": f"{T.version_id(o)}",
                    "evidence": _evidence([(o, f"out-of-scope trigger: {o.value}")])}
    if case.record.current.max_grade == 5:
        return {"reason": "record Grade 5", "source": "record.json current version", "evidence": []}
    return None


def evaluate_case(case: Case, observations: tuple[Observation, ...], window: ObservationWindow) -> CaseResult:
    """Grade, date and categorise one case. See the module docstring."""
    out_of_scope = _out_of_scope(case, observations)
    if out_of_scope:
        category = f"out of scope ({out_of_scope['reason']})"
        record = case.record.current
        fields = {name: {"category": category,
                         "record_value": (record.onset_date.isoformat() if record.onset_date else None)
                         if name == "onset" else record.max_grade,
                         "documented_value": None, "signed_difference_days": None, "difference_note": None,
                         "readings": [], "evidence": [], "record_history": None} for name in FIELDS}
        return CaseResult(case.case_id, out_of_scope, fields, None, [], [])

    engine = _Engine(case, observations, window)
    fields = {name: result for name, (result, _) in engine.field_results().items()}
    flags = engine.other_flags(fields)
    for name in FIELDS:
        flag = engine.apply_record_history(name, fields[name])
        if flag:
            flags.append(flag)
    # §6.3: does the record match a superseded version but not the current one?
    for old in engine.sel.superseded:
        swapped = _Engine(case, observations, window, swap=old).field_results()
        for name in FIELDS:
            if fields[name]["category"] not in ("7.7", "7.6") and swapped[name][0]["category"] == "7.7":
                flags.append({"flag": "superseded-version match", "field": name,
                              "detail": f"the record matches superseded {old.version_id} but not the current "
                                        f"version of {old.document_id} (§6.3).",
                              "evidence": _evidence([(o, "evidence with the superseded version")
                                                     for o in swapped[name][0]["_deciding"]])})
    for result in fields.values():
        result.pop("_deciding")
    return CaseResult(case.case_id, None, fields, engine.case_flags(), flags, engine.review_items())


def load_window(case_folder: str | Path) -> ObservationWindow:
    """The observation window from the dataset.json two folders above a case folder."""
    path = Path(case_folder).resolve().parent.parent / "dataset.json"
    if not path.is_file():
        raise FileNotFoundError(f"no dataset.json at {path}: the observation window is declared there")
    window = json.loads(path.read_text(encoding="utf-8"))["observation_window"]
    return ObservationWindow(start_day=int(window["start_day"]), end_day=int(window["end_day"]))


def evaluate_folder(case_folder: str | Path) -> CaseResult:
    """Load, extract and evaluate one case folder."""
    case = load_case(case_folder)
    return evaluate_case(case, extract_case(case), load_window(case_folder))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m resauce.engine <case folder>")
        return 2
    print(json.dumps(evaluate_folder(argv[0]).to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
