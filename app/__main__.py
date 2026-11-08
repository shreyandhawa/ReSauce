"""Start the ReSauce workstation: `python -m app` (from the repository root).

    python -m app                          # uses the workspace folder workspace/ (created if missing)
    python -m app --workspace <folder>     # another workspace folder inside this repository

The workspace holds the researcher's cases, runs, audit log and exports. Synthetic data only.

The Validation tab shows the stored evaluation results (results/dev.json and
results/held_out.json by default). Add another split, for example the locked set after its
final evaluation, by giving a results file, its data folder and its reference folder:

    python -m app --results results/locked.json --data <data folder> --reference <reference folder>

Repeat the three options for more splits. --no-defaults leaves out dev and held-out.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.api import Api
from app.server import serve
from app.sources import DEFAULT_SPLITS, ROOT, Sources
from app.workspace import Workspace, WorkspaceError
from app.workstation import Workstation


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m app", description="ReSauce workstation (synthetic data only).")
    parser.add_argument("--workspace", type=Path, default=ROOT / "workspace", metavar="FOLDER",
                        help="the workspace folder, inside this repository (default: workspace/)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--results", action="append", default=[], type=Path, metavar="FILE",
                        help="a results file from python -m resauce.evaluate (repeatable)")
    parser.add_argument("--data", action="append", default=[], type=Path, metavar="FOLDER",
                        help="the data folder of that results file (holds dataset.json and cases/)")
    parser.add_argument("--reference", action="append", default=[], type=Path, metavar="FOLDER",
                        help="the reference folder of that results file (holds intended/)")
    parser.add_argument("--no-defaults", action="store_true", help="do not load the dev and held-out results")
    args = parser.parse_args(argv)

    if not (len(args.results) == len(args.data) == len(args.reference)):
        parser.error("give --results, --data and --reference the same number of times, one set per split")
    triples = ([] if args.no_defaults else list(DEFAULT_SPLITS)) + list(zip(args.results, args.data, args.reference))

    try:
        workspace = Workspace(args.workspace if args.workspace.is_absolute() else Path.cwd() / args.workspace)
        sources = Sources(triples)
    except (ValueError, WorkspaceError) as exc:
        print(f"Cannot start: {exc}")
        return 1
    print(f"  workspace: {workspace.folder} ({len(workspace.case_ids())} cases)")
    for split in sources.splits:
        print(f"  validation split {split.name}: {len(split.results.get('cases', []))} cases from {split.results_path.name}")
    try:
        serve(Api(sources), Workstation(workspace, sources), args.port)
    except OSError as exc:
        print(f"Could not start on port {args.port}: {exc}. Try another port, e.g. --port 8001.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
