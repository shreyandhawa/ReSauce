# ReSauce

ReSauce is a computational research project. It checks whether clinical research records accurately reflect the medical documents behind them. The first focus is ICANS, a neurological complication that can follow CAR-T cell therapy.

> **Important:** ReSauce works only with synthetic (made-up) data. It is a proof of concept, not a medical device or a clinical decision-making tool. Its results are not clinical validation.

**Status:** Milestone 1 (project foundation). For now the program only confirms that your setup works. It does not perform any analysis yet.

## What you need
- Python 3.13 or newer. Check with `python3 --version`.
- Git. Check with `git --version`.

## One-time setup
Open a terminal in the project folder (in VS Code, choose **Terminal → New Terminal**) and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

What these commands do:
1. Create `.venv/`, a private folder that holds this project's Python packages.
2. Switch the terminal to that private environment. Your prompt will then start with `(.venv)`.
3. Install the project and its testing tool (pytest) into the environment.

## Everyday use
Every time you open a new terminal, switch to the environment first:

```bash
source .venv/bin/activate
```

Run the program:

```bash
python -m resauce
```

You should see:

```
ReSauce 0.1.0
Python 3.14.3
Environment is set up. No analysis is performed yet.
```

The Python version may differ on your machine.

Run the tests:

```bash
pytest
```

You should see `1 passed`.

## Using VS Code
- Press **Cmd+Shift+P**, choose **Python: Select Interpreter**, and pick the entry that mentions `.venv`.
- To run tests by clicking, open the **Testing** panel (the flask icon on the left). Choose **pytest** if VS Code asks.

## Project layout
```
src/resauce/     the Python code (the scientific core)
tests/           automated tests
docs/handoff.md  progress log between work sessions
pyproject.toml   project name, version and required packages
CLAUDE.md        rules Claude Code follows on this project
.gitignore       files Git must never save (secrets, temporary files)
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `pytest: command not found` or `No module named resauce` | Run `source .venv/bin/activate`, then try again. |
| The environment stops working after a Python upgrade | Delete the `.venv` folder with `rm -rf .venv` (it's safe; setup recreates it), then repeat the one-time setup. |
| `python: command not found` | Use `python3` outside the environment. Once the environment is active, `python` works. |
