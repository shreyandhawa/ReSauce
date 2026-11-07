"""Create seeded case IDs and writing briefs for the development set.

Usage (from the project folder):
    .venv/bin/python -m tools.make_briefs

Writes reference/dev-v1/ordering.json (which case ID belongs to which
scenario, and how that order was made) and reference/dev-v1/briefs.json (one
writing brief per case). The scenario table is read from docs/dataset-plan.md.
The same seed and the same plan always give byte-identical output.

Every random choice uses ONE random.Random(SEED) generator, in a fixed order:
ID shuffle, writing style, document count, age, infusion date, extra record
versions, unsigned extras, extra amendments, out-of-window documents, normal
EEG/imaging reports, extra "not assessable" periods. Changing that order
changes the output.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "docs" / "dataset-plan.md"
OUT = ROOT / "reference" / "dev-v1"

SEED = 20261107
STYLES = ["terse", "abbreviation-heavy", "templated", "verbose", "with typos", "mixed"]
# Distinct documents per case (versions not counted): 72 values, 60 of them 4-8.
DOC_COUNTS = {3: 4, 4: 12, 5: 13, 6: 13, 7: 12, 8: 10, 9: 3, 10: 2, 11: 2, 12: 1}
YEARS = range(2031, 2037)  # 6 fictional years x 12 cases

# Features a scenario requires (forced on). Source: dataset-plan.md v0.3.
FORCED_STYLE = {"SC-57": "templated"}  # §2.14: templated/flowsheet notes
FORCED_AMENDED = {"SC-30", "SC-31", "SC-32", "SC-62", "SC-63"}
FORCED_MULTI_RECORD = {"SC-27", "SC-29", "SC-33", "SC-34", "SC-62", "SC-63"}
FORCED_NOT_ASSESSABLE = {"SC-17", "SC-67"}
FORCED_UNSIGNED = {"SC-32": "unsigned later version", "SC-68": "unsigned document"}
UNGRADEABLE_SYMPTOM = {"SC-47", "SC-52", "SC-53", "SC-60", "SC-67"}  # §2.1
# Features a scenario forbids (forced off), with the reason (see README).
NO_OUT_OF_WINDOW = {"SC-60"}  # plus every OOS scenario
NO_NORMAL_REPORT = {"SC-09", "SC-10", "SC-11", "SC-12", "SC-13", "SC-27", "SC-28"}

# How many cases get each optional feature (beyond the forced ones).
N_OUT_OF_WINDOW = 7
N_NORMAL_REPORT = 18  # 9 EEG + 9 imaging
N_EXTRA_AMENDED = 8
N_UNSIGNED_DOCUMENT = 2
N_UNSIGNED_LATER = 2
N_EXTRA_MULTI = {"Pos": 4, "Neg": 3, "Flag": 3}
N_EXTRA_NOT_ASSESSABLE = 3
MIN_CORE_DOCUMENTS = 3  # documents left for the scenario after extra documents

RULES_FOR_ALL_CASES = [
    "Follow dataset-plan.md §5 (construction), §5.2 (distractors), §6 (realism), §7 (leakage) and the avoid rules of §10.2.",
    "'documents' counts distinct documents (document IDs), including any out-of-window document, normal report or unsigned document; versions are not counted.",
    "Every document version and record version from 2 onward has a realistic, non-null reason that reveals nothing.",
    "Out-of-window document: its documentation date and every date it mentions lie outside Day 0 to Day +28. Its neurological observation is a Grade 0 assessment (e.g. ICE 10/10) or an excluded symptom (e.g. tremor), never a qualifying finding or a free symptom word.",
    "Extra (random) amendment: changes no neurological content, no sedating drug and no event time (e.g. a corrected vital sign). In a case with a multi-version record it is documented before record version 1.",
    "Extra record versions use only the allowed patterns of §5.1: 'same values re-entered'; 'corrected to agreeing value' (only on the named 7.7 field, with every record version recorded after the last document, so 7.6 condition (c) fails); 'change still disagrees' (Pos only, on the named discrepancy field).",
    "Normal EEG or imaging report: plainly normal, inside the window, not near a finding in a way that could read as a conflicting assessment.",
    "Extra 'not assessable' period: a non-sedation reason (e.g. off the unit for a scan); after the documented onset; not on the day of the documented maximum grade; not on the record's onset date; at least 2 calendar days from any qualifying finding; applies only to its own documentation date.",
    "Unsigned extra: contains no neurological observation and no sedating drug. An 'unsigned later version' differs from its signed version only in non-neurological content.",
    "No sedating drug in the same note as any finding, or in the 24 hours before it, unless the scenario needs one (A30).",
    "Free symptom words for cognition or speech (e.g. 'confused', 'word-finding difficulty') only where 'ungradeable_symptom' is 'required', in a note with no ICE total and no consciousness description, on a calendar day with no ICE assessment (NEW-13, NEW-14).",
    "Consciousness wording clearly fits one Table 6 category or is plainly normal, except in SC-23 (NEW-15).",
    "No relative-time range phrase ('overnight', 'last night') in a note documented on Day 0 or Day +29 (NEW-16); no competing cause in the same note as, or within 2 calendar days before, a finding dated by a range (NEW-17).",
    "Style 'with typos': typos never change numbers, scores, dates or times, negations, or the words of any observation the intended answer relies on.",
    "No death except SC-69; no CAPD except SC-55; no record Grade 5 except SC-56; no age under 18 except SC-54; no baseline developmental delay anywhere.",
]


def read_scenarios(plan_text: str) -> list[dict]:
    """Return the 72 scenario rows of dataset-plan.md §2, sorted by number."""
    scenarios = []
    for line in plan_text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not re.fullmatch(r"SC-[0-9]{2}", cells[0]):
            continue
        sc_id, text, rules, onset, grade, kind = cells
        scenarios.append(
            {
                "scenario_id": sc_id,
                "scenario": text,
                "rules": rules,
                "expected_onset": onset,
                "expected_grade": grade,
                "type": kind.split()[0].rstrip(","),
                "plain": "plain" in kind,
                "no_icans": "no ICANS" in kind,
                "onset_cat": _category(onset),
                "grade_cat": _category(grade),
            }
        )
    scenarios.sort(key=lambda s: int(s["scenario_id"][3:]))
    return scenarios


def _category(cell: str) -> str | None:
    match = re.match(r"7\.[1-8]", cell)
    return match.group(0) if match else None


def build(plan_text: str, seed: int = SEED) -> tuple[dict, dict]:
    """Return (ordering, briefs) as plain dicts, ready to be written as JSON."""
    rng = random.Random(seed)
    scenarios = read_scenarios(plan_text)
    input_order = [s["scenario_id"] for s in scenarios]

    shuffled = input_order[:]
    rng.shuffle(shuffled)
    id_of = {sc: f"SYN-{i + 1:04d}" for i, sc in enumerate(shuffled)}
    ordering = {
        "seed": seed,
        "generator": "Python random.Random(seed) (Mersenne Twister); list shuffled with random.shuffle",
        "python_version": sys.version.split()[0],
        "input_order": input_order,
        "id_to_scenario": {id_of[sc]: sc for sc in sorted(input_order, key=id_of.get)},
    }

    by_sc = {s["scenario_id"]: s for s in scenarios}
    briefs = {sc: {"case_id": id_of[sc], **_public(by_sc[sc])} for sc in input_order}
    forced: dict[str, list[str]] = {sc: [] for sc in input_order}
    oos = {sc for sc in input_order if by_sc[sc]["type"] == "OOS"}

    def pool(counts: dict) -> list:
        items = [value for value, n in counts.items() for _ in range(n)]
        rng.shuffle(items)
        return items

    # Writing style: 12 of each; forced styles are taken out of the pool first.
    styles = [s for s in STYLES for _ in range(len(input_order) // len(STYLES))]
    for sc, style in FORCED_STYLE.items():
        styles.remove(style)
        briefs[sc]["writing_style"] = style
        forced[sc].append(f"writing_style {style} (scenario)")
    rng.shuffle(styles)
    for sc in input_order:
        if sc not in FORCED_STYLE:
            briefs[sc]["writing_style"] = styles.pop()

    for sc, count in zip(input_order, pool(DOC_COUNTS)):
        briefs[sc]["documents"] = count

    for sc in input_order:
        if sc == "SC-54":
            briefs[sc]["age_at_infusion"] = rng.randint(13, 17)
            forced[sc].append("age 13-17 (scenario: under 18; avoids CAPD age and the age-12 conflict)")
        else:
            briefs[sc]["age_at_infusion"] = rng.randint(18, 85)

    years = pool({year: 12 for year in YEARS})
    months = pool({month: 6 for month in range(1, 13)})
    for sc, year, month in zip(input_order, years, months):
        day = rng.randint(1, calendar.monthrange(year, month)[1])
        briefs[sc]["infusion_date"] = f"{year:04d}-{month:02d}-{day:02d}"

    # Record versions.
    for sc in input_order:
        briefs[sc]["multi_version_record"] = None
    for sc in sorted(FORCED_MULTI_RECORD):
        briefs[sc]["multi_version_record"] = {"source": "scenario", "pattern": "as the scenario describes", "field": None}
        forced[sc].append("multi_version_record (scenario)")
    for kind, n in N_EXTRA_MULTI.items():
        eligible = [sc for sc in input_order if by_sc[sc]["type"] == kind and sc not in FORCED_MULTI_RECORD]
        for sc in rng.sample(eligible, n):
            pattern, field = rng.choice(_record_patterns(by_sc[sc]))
            briefs[sc]["multi_version_record"] = {"source": "random", "pattern": pattern, "field": field}

    # Unsigned versions (counted as extra documents or as amended notes).
    extra_docs = {sc: 0 for sc in input_order}

    def room(sc: str) -> bool:
        return briefs[sc]["documents"] - extra_docs[sc] - 1 >= MIN_CORE_DOCUMENTS

    for sc in input_order:
        briefs[sc]["unsigned_version"] = None
    for sc, kind in FORCED_UNSIGNED.items():
        briefs[sc]["unsigned_version"] = {"kind": kind, "source": "scenario"}
        forced[sc].append(f"{kind} (scenario)")
    eligible = [
        sc for sc in input_order
        if sc not in FORCED_UNSIGNED and sc not in FORCED_AMENDED and sc not in oos
    ]
    for sc in rng.sample([sc for sc in eligible if room(sc)], N_UNSIGNED_DOCUMENT):
        briefs[sc]["unsigned_version"] = {"kind": "unsigned document", "source": "random"}
        extra_docs[sc] += 1
    eligible = [sc for sc in eligible if briefs[sc]["unsigned_version"] is None]
    for sc in rng.sample(eligible, N_UNSIGNED_LATER):
        briefs[sc]["unsigned_version"] = {"kind": "unsigned later version", "source": "random"}

    # Amended notes: forced, unsigned later versions, then random signed ones.
    for sc in input_order:
        unsigned = briefs[sc]["unsigned_version"]
        if sc in FORCED_AMENDED:
            briefs[sc]["amended_note"] = "scenario"
            forced[sc].append("amended_note (scenario)")
        elif unsigned and unsigned["kind"] == "unsigned later version":
            briefs[sc]["amended_note"] = "unsigned later version"
        else:
            briefs[sc]["amended_note"] = None
    eligible = [sc for sc in input_order if briefs[sc]["amended_note"] is None]
    for sc in rng.sample(eligible, N_EXTRA_AMENDED):
        briefs[sc]["amended_note"] = "random (signed, no neurological change)"

    # Out-of-window documents.
    for sc in input_order:
        briefs[sc]["out_of_window_document"] = False
        if sc in oos or sc in NO_OUT_OF_WINDOW:
            forced[sc].append("no out_of_window_document")
    eligible = [sc for sc in input_order if sc not in oos and sc not in NO_OUT_OF_WINDOW and room(sc)]
    for sc in rng.sample(eligible, N_OUT_OF_WINDOW):
        briefs[sc]["out_of_window_document"] = True
        extra_docs[sc] += 1

    # Normal EEG or imaging reports.
    for sc in input_order:
        briefs[sc]["normal_report_distractor"] = None
        if sc in NO_NORMAL_REPORT:
            forced[sc].append("no normal_report_distractor")
    eligible = [sc for sc in input_order if sc not in NO_NORMAL_REPORT and room(sc)]
    kinds = pool({"eeg": N_NORMAL_REPORT // 2, "imaging": N_NORMAL_REPORT - N_NORMAL_REPORT // 2})
    for sc, kind in zip(rng.sample(eligible, N_NORMAL_REPORT), kinds):
        briefs[sc]["normal_report_distractor"] = kind
        extra_docs[sc] += 1

    # "Not assessable" periods: forced, else only in the narrow eligible set.
    for sc in input_order:
        briefs[sc]["not_assessable_period"] = None
    for sc in sorted(FORCED_NOT_ASSESSABLE):
        briefs[sc]["not_assessable_period"] = "scenario"
        forced[sc].append("not_assessable_period (scenario)")
    eligible = [sc for sc in input_order if _may_add_not_assessable(by_sc[sc])]
    for sc in input_order:
        if sc not in FORCED_NOT_ASSESSABLE and sc not in eligible:
            forced[sc].append("no not_assessable_period")
    for sc in rng.sample(eligible, N_EXTRA_NOT_ASSESSABLE):
        briefs[sc]["not_assessable_period"] = "random (non-sedation reason)"

    for sc in input_order:
        b = briefs[sc]
        b["ungradeable_symptom"] = "required" if sc in UNGRADEABLE_SYMPTOM else "forbidden"
        b["death"] = "required (documented inside the window)" if sc == "SC-69" else "forbidden"
        b["forced"] = forced[sc]

    ordered = sorted(briefs.values(), key=lambda b: b["case_id"])
    result = {
        "generated_by": "tools/make_briefs.py",
        "seed": seed,
        "dataset_plan": {"file": "docs/dataset-plan.md", "version": "0.3", "sha256": hashlib.sha256(plan_text.encode("utf-8")).hexdigest()},
        "rules_for_all_cases": RULES_FOR_ALL_CASES,
        "totals": _totals(ordered),
        "briefs": ordered,
    }
    return ordering, result


def _public(s: dict) -> dict:
    keys = ("scenario_id", "scenario", "rules", "expected_onset", "expected_grade", "type", "plain", "no_icans")
    return {key: s[key] for key in keys}


def _record_patterns(s: dict) -> list[tuple[str, str | None]]:
    """Allowed extra record-history patterns for a non-revision scenario (§5.1)."""
    patterns: list[tuple[str, str | None]] = [("same values re-entered", None)]
    if s["no_icans"]:
        return patterns
    for field, cat in (("onset", s["onset_cat"]), ("max_grade", s["grade_cat"])):
        if cat == "7.7":
            patterns.append(("corrected to agreeing value", field))
        if s["type"] == "Pos" and cat in ("7.1", "7.2", "7.3"):
            patterns.append(("change still disagrees", field))
    return patterns


def _may_add_not_assessable(s: dict) -> bool:
    """User decision 1: Pos/Neg, grade 7.2 or 7.7, onset 7.7, ICANS recorded."""
    return (
        s["type"] in ("Pos", "Neg")
        and not s["no_icans"]
        and s["grade_cat"] in ("7.2", "7.7")
        and s["onset_cat"] == "7.7"
        and s["scenario_id"] not in FORCED_NOT_ASSESSABLE
    )


def _totals(briefs: list[dict]) -> dict:
    def count(key, value=None):
        return sum(1 for b in briefs if (b[key] == value if value is not None else bool(b[key])))

    return {
        "cases": len(briefs),
        "writing_style": {s: count("writing_style", s) for s in STYLES},
        "documents": {str(n): count("documents", n) for n in DOC_COUNTS},
        "age_under_18": sum(1 for b in briefs if b["age_at_infusion"] < 18),
        "infusion_years": {str(y): sum(1 for b in briefs if b["infusion_date"].startswith(str(y))) for y in YEARS},
        "out_of_window_document": count("out_of_window_document"),
        "amended_note": count("amended_note"),
        "multi_version_record": count("multi_version_record"),
        "normal_report_distractor": {k: count("normal_report_distractor", k) for k in ("eeg", "imaging")},
        "not_assessable_period": count("not_assessable_period"),
        "unsigned_version": count("unsigned_version"),
        "ungradeable_symptom_required": count("ungradeable_symptom", "required"),
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    ordering, briefs = build(PLAN.read_text(encoding="utf-8"))
    write_json(OUT / "ordering.json", ordering)
    write_json(OUT / "briefs.json", briefs)
    print(f"Wrote {OUT / 'ordering.json'} and {OUT / 'briefs.json'}")
    print(json.dumps(briefs["totals"], indent=2))


if __name__ == "__main__":
    main()
