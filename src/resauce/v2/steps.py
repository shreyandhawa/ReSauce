"""The clean-up steps v2 applies, in priority order.

Only steps with no clinical meaning are listed so far: they repair how text was copied, not
what it says. Steps that interpret clinical wording (abbreviations such as "sz", misspellings)
are NOT here yet. Each needs its rule written in docs/clinical-methods.md first, and messy
synthetic cases to show whether it helps, so it is not tuned blind.
"""

from __future__ import annotations

import re

from resauce.v2.normalise import Proposal, Step

# Invisible characters that sometimes arrive in copied text. A zero-width space inside
# "sei​zure" stops the v1 extractor from seeing the word.
_ZERO_WIDTH = re.compile("[​‌‍⁠﻿]")
_NO_BREAK_SPACE = re.compile("[  ]")


def _invisible_characters(text: str) -> list[Proposal]:
    proposals: list[Proposal] = [(m.start(), m.end(), "") for m in _ZERO_WIDTH.finditer(text)]
    proposals += [(m.start(), m.end(), " ") for m in _NO_BREAK_SPACE.finditer(text)]
    return proposals


STEPS: tuple[Step, ...] = (
    Step(
        "invisible-characters",
        "Remove zero-width characters and turn non-breaking spaces into ordinary spaces "
        "(copy-and-paste leftovers that can split a word the extractor should recognise).",
        _invisible_characters,
    ),
)
