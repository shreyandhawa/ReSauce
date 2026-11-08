# Pipeline freeze (Step 4)

- **Date:** 2026-11-08
- **Commit with the frozen source and the evaluation at the freeze:** `ec7519e30645b63bda2a9cfd5e257d363f0ccf89` ("Step 5a close-out and evaluation at pipeline freeze"). The freeze record itself (this file and its test) is the next commit, which carries the tag `pipeline-freeze-v1`.
- **Why:** the locked cases (Step 6) must be scored by a pipeline that was fixed before anyone saw them. From this point the pipeline cannot be adjusted to suit the locked results. Results on synthetic data are not clinical validation.

## What is frozen

1. **These files in `src/resauce/`:** `loader.py`, `models.py`, `extract.py`, `phrases.py`, `engine.py`, `timeline.py`, `baseline_a.py`. Their SHA-256 is below, and `tests/test_freeze.py` fails if any of them changes.
2. **The scoring rules in `src/resauce/evaluate.py`** (classes, detection, miss, false alert, precision, recall, F1, exact agreement, out-of-scope scoring; `docs/evaluation-spec.md` §3). This file is **not hashed**, because it may still gain new methods and splits. It is protected by the rule below instead.

`__init__.py` and `__main__.py` (no logic that decides answers) are not in the list.

## What may still be added after the freeze

- **New files**, such as `baseline_b.py`.
- **Changes to `evaluate.py` that only add a method or a split** (for example a new baseline, or another named split). Any change to how an existing method is scored, how a category is classed, or how a rate is computed is **not allowed**.
- Documents, tests for new files, reference answers for new cases, results, the handoff.

Any change to a frozen file means the freeze is broken. It must be disclosed with every later result, and results made before and after it are not comparable without saying so.

## SHA-256 of the frozen files

Computed on the raw file bytes at the commit above (`shasum -a 256 <file>`). The test reads this table.

| File | SHA-256 |
|---|---|
| src/resauce/loader.py | 266eac457326ebddf7fe671c3f67649dee5a9223a73a5f52df28e848e5e0596f |
| src/resauce/models.py | e45bf988b2a576b32c03ed4661b0af4fde62bc6d631b9f02d158fab5aa586dc6 |
| src/resauce/extract.py | 6029339352b64aaefde2552327e0baf121af4ce5f8f86e79d4eaf06e6434601e |
| src/resauce/phrases.py | 14dce4b5c0b5f69032fdd8c50ce26678e7c68f5a6a4ffcf52a779a75f05178af |
| src/resauce/engine.py | 2c4ff93464b197c3f77eabaacdba12b302c6c134633a84ef7233e9f1120b1fda |
| src/resauce/timeline.py | 1ea3efcb7cb128f535bc57b550e90e15b6524a128a10962227e0b33c4e4f04aa |
| src/resauce/baseline_a.py | fb2389c7f041b74da67c554d12d8b90946fd1c764eb241b10ed20aed63eb81e9 |
