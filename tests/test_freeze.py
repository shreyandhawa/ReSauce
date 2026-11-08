"""The frozen pipeline files must still match the hashes recorded in docs/freeze.md.

evaluate.py is not hashed: it may still gain a method or a split, and is protected by the
rule written in docs/freeze.md instead.
"""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ("loader", "models", "extract", "phrases", "engine", "timeline", "baseline_a")


def recorded_hashes() -> dict[str, str]:
    text = (ROOT / "docs" / "freeze.md").read_text(encoding="utf-8")
    return dict(re.findall(r"^\| (src/resauce/\w+\.py) \| ([0-9a-f]{64}) \|$", text, re.MULTILINE))


def test_frozen_files_match_the_recorded_hashes():
    recorded = recorded_hashes()
    assert sorted(recorded) == sorted(f"src/resauce/{name}.py" for name in FROZEN)
    changed = [path for path, digest in recorded.items()
               if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest]
    assert not changed, f"frozen file(s) changed after the pipeline freeze: {changed}"
