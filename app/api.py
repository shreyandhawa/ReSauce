"""The Validation tab's API: the stored evaluation results (results/*.json), read only.

Every number comes from a results file written by `python -m resauce.evaluate`.
"""

from __future__ import annotations

from resauce import evaluate as ev

from app.sources import Sources, Split, display_path

# Split headings and disclosures as results/report.md and resauce.evaluate state them.
SPLIT_TITLES = {"dev": "dev", "held_out": "held-out (in-repo, not sealed)"}
SPLIT_DISCLOSURES = {
    "held_out": (ev.HELD_OUT_SEEN[0].upper() + ev.HELD_OUT_SEEN[1:] + ".", ev.HELD_OUT_DISCLOSURE),
}


class Api:
    def __init__(self, sources: Sources):
        self.sources = sources

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
        with_b = any("baseline_b" in (s["metrics"] or {}) for s in splits)
        return {
            "splits": splits,
            "methods": ev.METHOD_TITLES,
            "reference_label": ev.LABEL,
            "limitations": ev.limitations(with_b),
            "scoring": {"positive": ev.POSITIVE, "negative": ev.NEGATIVE, "review": ev.REVIEW},
        }


def _title(split: Split) -> str:
    return SPLIT_TITLES.get(split.name, split.name)
