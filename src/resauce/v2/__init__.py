"""ReSauce pipeline v2: v1 plus a text clean-up step before extraction (in development).

v1 (pipeline-freeze-v1) is untouched. See docs/v2.md for the rules this line follows.
"""

LINE = "v2"
STATUS = "in development: not frozen, not evaluated"
FILES = ("normalise", "steps", "extract")  # the modules of this package that make up v2
