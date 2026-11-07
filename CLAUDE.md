# CLAUDE.md

Rules for Claude Code when working on ReSauce. Read this file and `docs/handoff.md` at the start of every session.

## Project
ReSauce is a computational proof of concept. It investigates whether clinical research records accurately reflect the medical documents that support them. The first focus is documented ICANS (immune effector cell-associated neurotoxicity syndrome) following CAR-T cell therapy. It is **not** a clinical decision-making tool and not a wet-lab project.

Planned pipeline, built one milestone at a time:
1. Read synthetic clinical documents and research records.
2. Extract observations with traceable source evidence.
3. Reconstruct clinical event timelines.
4. Identify potential discrepancies and uncertainty.
5. Compare results against simpler verification approaches.
6. Display findings and measured results in a web interface.

The current milestone and status are in `docs/handoff.md`.

## Scientific integrity (non-negotiable)
- Use synthetic data only. Never add real patient data, names, dates of birth, record numbers or any other identifiers.
- Never fabricate, estimate or "fill in" results, metrics or citations. If something is unknown, say so.
- Every extracted observation must link to its source: document ID, location in the document, and the exact quoted text.
- Report uncertainty and ambiguity explicitly. Never hide them.
- Results on synthetic data are not clinical validation. Never describe them as such.
- Comparisons with simpler methods must be measured on the same data. Never assume the outcome.
- Record methods, parameters and data versions so every result can be reproduced.
- Do not implement medical algorithms until a milestone explicitly calls for them.

## Engineering
- The Python core lives in `src/resauce/`. It must not import any UI or web code. The future interface calls the core, never the other way round.
- Prefer simple, proven, maintainable solutions. Add no unnecessary frameworks, AI agents, plugins or infrastructure.
- Every change comes with tests. Run `pytest` and confirm it passes before calling work done.
- Ask the user before adding a dependency, installing software, deleting or overwriting work, or deploying anything.
- Never copy code from other projects.
- Never commit secrets (`.env` files, keys, tokens).
- Do not add "Co-Authored-By" or any other AI attribution lines to commit messages or pull requests.

## Working with the user
The user is a beginner. For every action, explain in plain language:
- what you are doing,
- why it is needed,
- whether they must do anything manually,
- how to verify it worked.

Avoid jargon, and define any technical term the first time you use it.

## Session routine
- Start: read `docs/handoff.md`.
- End: add an entry to `docs/handoff.md` covering what was done, the decisions made and why, next steps, and open questions.

## Commands
```bash
python3 -m venv .venv        # one-time: create the environment
source .venv/bin/activate    # in every new terminal
pip install -e ".[dev]"      # one-time, and again after dependencies change
python -m resauce            # run the program
pytest                       # run the tests
```
