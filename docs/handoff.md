# Handoff log

Progress notes between Claude Code sessions, newest entry first. Read this file at the start of a session and add an entry at the end.

Each entry covers:
- **Status:** where the project stands
- **Done:** what was completed
- **Decisions & why:** the choices made and the reasons behind them
- **Next steps:** what to do next
- **Open questions:** anything waiting on the user
- **How to verify:** commands that prove it works

---

## 2026-11-07: Milestone 1 verification and project move

**Status:** Milestone 1 re-verified. The program runs and `pytest` reports 1 passed.

**Done:**
- A verification run found `python -m resauce` and `pytest` failing with "No module named resauce", even though both had passed at setup.
- Cause: the project was in `~/Documents`, which iCloud syncs. macOS added the "hidden" flag to `.venv/`, and Python 3.14 skips hidden `.pth` files. That broke the link to `src/`. The code itself was fine: with `PYTHONPATH=src` the program ran and the test passed.
- Moved the project to `~/Projects/ReSauce`, which is not synced, and rebuilt `.venv`. All checks pass.

**Decisions & why:**
- Keep the project out of iCloud-synced folders. Syncing also risks conflicts inside `.git/` and `.venv/`.

**How to verify:**
```bash
cd ~/Projects/ReSauce
source .venv/bin/activate
python -m resauce
pytest        # expect: 1 passed
```

---

## 2026-11-07: Milestone 1, project foundation

**Status:** Milestone 1 complete. The project installs, the program runs, and the one test passes.

**Done:**
- Renamed the project from "Elenchra" to "ReSauce".
- Created a Git repository on branch `main`.
- Created the Python project: `pyproject.toml`, the `src/resauce/` package and `tests/`.
- Added a minimal program (`python -m resauce`) that prints the project name, version and Python version. It contains no scientific or medical logic.
- Added one automated test (`tests/test_main.py`).
- Added `CLAUDE.md`, `README.md`, `.gitignore` and this file.

**Decisions & why:**
- Python's built-in `venv` with `pip` and `pyproject.toml`: already on the machine, the most standard approach, and nothing has to be installed system-wide.
- `pytest` is the only dependency. It is the most widely used Python testing tool.
- "src layout": the scientific core sits in `src/resauce/`, separate from the future web interface.
- `requires-python >=3.13`: the machine has Python 3.14.3 (Homebrew, used for `.venv`) and 3.13.12 (python.org).
- Deliberately not added yet: uv, conda, Poetry, Docker, linters, CI and web frameworks. Add them only when there is a real need.

**Environment found:** macOS 26.6.2 (Apple Silicon), Git 2.50.1, Python 3.14.3, Node.js 25.8.0 and npm 11.11.0 (not used yet), and VS Code with the Python extension.

**Next steps:**
- Define Milestone 2 with the user. Pipeline step 1 (reading synthetic documents and research records) is the natural starting point.

**Open questions:**
- Node.js 25 is a short-support release. Consider a long-term-support (LTS) version when the frontend milestone starts.
- No software licence has been chosen yet.

**How to verify:**
```bash
source .venv/bin/activate
python -m resauce
pytest        # expect: 1 passed
```
