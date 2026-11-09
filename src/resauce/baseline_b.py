"""Baseline B: a large language model reads the case and applies the written rules.

Implements docs/evaluation-spec.md §5. The model gets the clinical-methods text
("How to read this document" through §9) as its instructions and one case's
files as JSON, and answers with a schema-constrained JSON object: the
out-of-scope reason, and for onset and maximum grade a §7 category, the
documented value, an explanation and evidence quotes.

The model is called through Claude Code's print mode ("claude -p") on the user's
own Claude plan: the instructions replace Claude Code's system prompt, all tools
are off (the model cannot open any file), and the answer is constrained by a
JSON schema. Run these in your own terminal, not inside a Claude Code session:

    python -m resauce.baseline_b check              # one tiny test request, no case data
    python -m resauce.baseline_b run [--workers N]  # one request per case, each answer stored

`run` skips cases that already have a stored answer, so an interrupted run can
be resumed; it never asks again for a stored case. Scoring (the evaluation runner)
reads only the stored answers and never calls the model.

The functions that build the request and turn an answer into a method output
are pure and tested without calling the model. Standard library only.
This module never reads reference answers or pipeline outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from resauce.engine import load_window
from resauce.loader import load_case
from resauce.models import Case, ObservationWindow

ROOT = Path(__file__).resolve().parents[2]
METHODS_DOC = ROOT / "docs" / "clinical-methods.md"
DEFAULT_DATA = ROOT / "data" / "dev-v1"
DEFAULT_OUT = ROOT / "results" / "baseline_b"

# evaluation-spec §5. Fixed before the run; changing any of these makes a new, separate run.
MODEL = "claude-opus-5-5"
EFFORT = "high"
CASE_TIMEOUT_SECONDS = 1800
CHECK_TIMEOUT_SECONDS = 180

# USD per million tokens for claude-opus-5-5, from Anthropic's listed prices (claude-api reference,
# cached 2026-10-06). Cache writes are 1.25 x input (5-minute cache). Used only to report what the measured
# tokens would cost on the API; a run on the user's Claude plan is not billed per token.
PRICES = {"input": 4.00, "output": 20.00, "cache_write": 5.00, "cache_read": 0.20}
PRICES_SOURCE = "Anthropic listed prices for claude-opus-5-5, claude-api reference cached 2026-10-06"

OUT_OF_SCOPE_REASONS = ("age under 18", "CAPD assessment", "record Grade 5", "documented death",
                        "developmental delay")  # A29, with the labels the reference answers use
IN_SCOPE = "in scope"
ONSET_CATEGORIES = ("7.1", "7.4", "7.5", "7.6", "7.7", "7.8")  # §7 table: categories allowed for onset
GRADE_CATEGORIES = ("7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8")  # ... and for maximum grade

INSTRUCTIONS = """\
You are checking whether a clinical research record agrees with the clinical documents behind it. All data is \
fictional and synthetic; no real patient is involved.

The rules for this check are the ReSauce clinical methods document, given below between <clinical_methods> tags. \
Apply them as written, including the operational definitions and the assumptions in §9. Where the rules say a \
field cannot be decided from the documents, use the review categories (7.4 or 7.5) rather than guessing.

You will receive one case: its facts (age at infusion, and the infusion date, which is Day 0), the observation \
window, every version of the research record, and every version of every clinical document with its metadata.

Answer:
1. Is the case out of scope (§5, A29)? Give one of the listed reasons, or "in scope".
2. For the current version of the research record, give the §7 category for the ICANS onset date and for the \
maximum ICANS grade, the value the documents support, a short explanation, and the evidence.

Evidence: list the passages each answer rests on. Copy every quote exactly, character for character, from one \
document version, and give that version's document_id (for example "SYN-0001-D02") and its version number. Keep \
quotes to the sentence or phrase that matters. The list may be empty when no passage applies.

If the case is out of scope, the field answers are not used; give your best reading anyway."""


def _field_schema(categories: tuple[str, ...], value_hint: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": list(categories)},
            "documented_value": {"type": "string", "description": value_hint},
            "explanation": {"type": "string"},
            "evidence": {"type": "array", "items": {
                "type": "object",
                "properties": {"document_id": {"type": "string"}, "version": {"type": "integer"},
                               "quote": {"type": "string"}},
                "required": ["document_id", "version", "quote"],
                "additionalProperties": False,
            }},
        },
        "required": ["category", "documented_value", "explanation", "evidence"],
        "additionalProperties": False,
    }


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "out_of_scope_reason": {"type": "string", "enum": [IN_SCOPE, *OUT_OF_SCOPE_REASONS]},
        "onset": _field_schema(ONSET_CATEGORIES, "The ICANS onset date the documents support (YYYY-MM-DD), or none"),
        "max_grade": _field_schema(GRADE_CATEGORIES, "The maximum ICANS grade the documents support (0 to 4), or none"),
    },
    "required": ["out_of_scope_reason", "onset", "max_grade"],
    "additionalProperties": False,
}


class AnswerError(Exception):
    """The stored answer cannot be turned into a method output (declined, cut off or not valid JSON)."""


# ---------------------------------------------------------------------------
# Building the request (pure)
# ---------------------------------------------------------------------------


def rules_text(path: Path = METHODS_DOC) -> str:
    """clinical-methods.md from "How to read this document" up to (not including) §10 References."""
    text = path.read_text(encoding="utf-8")
    start = text.find("## How to read this document")
    end = text.find("## 10. References")
    if start < 0 or end < start:
        raise ValueError("clinical-methods.md no longer has the expected headings")
    return text[start:end].rstrip().removesuffix("---").rstrip()


def system_prompt() -> str:
    return f"{INSTRUCTIONS}\n\n<clinical_methods>\n{rules_text()}\n</clinical_methods>"


def case_json(case: Case, window: ObservationWindow) -> dict:
    """The case files, as sent to the model."""
    return {
        "case_id": case.case_id,
        "age_at_infusion": case.age_at_infusion,
        "infusion_date": case.infusion_date.isoformat(),
        "observation_window": {"start_day": window.start_day, "end_day": window.end_day,
                               "meaning": "days after infusion (Day 0), inclusive"},
        "research_record": {
            "record_id": case.record.record_id,
            "versions": [{
                "version": v.version,
                "recorded_at": v.recorded_at.isoformat(timespec="minutes"),
                "icans_reported": v.icans_reported,
                "onset_date": v.onset_date.isoformat() if v.onset_date else None,
                "max_grade": v.max_grade,
                "change_reason": v.change_reason,
            } for v in case.record.versions],
        },
        "documents": [{
            "document_id": d.document_id,
            "version": d.version,
            "status": d.status,
            "note_type": d.note_type,
            "author_role": d.author_role,
            "documented_at": d.documented_at.isoformat(timespec="minutes"),
            "amendment_reason": d.amendment_reason,
            "text": d.text,
        } for d in sorted(case.documents, key=lambda d: (d.document_id, d.version))],
    }


def user_message(case: Case, window: ObservationWindow) -> str:
    return "Case to check:\n\n```json\n" + json.dumps(case_json(case, window), indent=1, ensure_ascii=False) + "\n```"


def claude_command(system: str, schema: dict = ANSWER_SCHEMA) -> list[str]:
    """The Claude Code print-mode command (evaluation-spec §5). The case message goes to its standard input."""
    return ["claude", "-p", "--model", MODEL, "--effort", EFFORT, "--system-prompt", system, "--tools", "",
            "--json-schema", json.dumps(schema), "--output-format", "json", "--no-session-persistence",
            "--strict-mcp-config", "--setting-sources", "project"]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Turning a stored answer into a method output (pure)
# ---------------------------------------------------------------------------


def parse_answer(stored: dict) -> dict:
    """The model's JSON answer, or AnswerError if it came from another model, declined, did not finish or is
    not valid JSON (spec §5)."""
    models = stored.get("models_reported")
    if models is not None and not any(str(m).startswith(MODEL) for m in models):
        raise AnswerError(f"not answered by {MODEL} (reported: {', '.join(map(str, models)) or 'none'})")
    reason = stored.get("stop_reason")
    if reason == "refusal":
        details = stored.get("stop_details") or {}
        raise AnswerError(f"the model declined (category: {details.get('category')})")
    if reason == "max_tokens":
        raise AnswerError("the answer was cut off at max_tokens")
    if reason not in (None, "end_turn"):
        raise AnswerError(f"the answer did not complete ({reason})")
    try:
        answer = json.loads(stored.get("answer_text") or "")
    except json.JSONDecodeError as exc:
        raise AnswerError(f"the answer is not valid JSON ({exc.msg})") from None
    if not isinstance(answer, dict) or not {"out_of_scope_reason", "onset", "max_grade"} <= answer.keys():
        raise AnswerError("the answer is missing required keys")
    return answer


def locate(case: Case, item: dict, role: str) -> dict:
    """An evidence entry with offsets found by exact search in the named document version (spec §5).

    The first occurrence gives the offsets; offsets are -1 when the version or the quote is not found.
    """
    document_id, version, quote = str(item.get("document_id", "")), item.get("version"), str(item.get("quote", ""))
    document = case.get_document_version(document_id, version) if isinstance(version, int) else None
    start = document.text.find(quote) if document is not None and quote else -1
    return {"role": role, "document_id": document_id, "version": version, "quote": quote,
            "start": start, "end": start + len(quote) if start >= 0 else -1}


def evaluate_case(case: Case, stored: dict) -> dict:
    """The method output for one case, in the shape the scorer reads (like engine's to_dict).

    Raises AnswerError for an answer that cannot be used (it then counts as an error, spec §3).
    """
    answer = parse_answer(stored)
    reason = answer["out_of_scope_reason"]
    out_of_scope = None if reason == IN_SCOPE else {"reason": reason, "source": "Baseline B answer", "evidence": []}
    fields = {}
    for name in ("onset", "max_grade"):
        given = answer[name]
        fields[name] = {
            "category": f"out of scope ({reason})" if out_of_scope else given["category"],
            "documented_value": given.get("documented_value"),
            "explanation": given.get("explanation"),
            # Out of scope: the field answers are not used (spec §5), so their quotes are not kept, as for ReSauce.
            "evidence": [] if out_of_scope else
            [locate(case, item, f"Baseline B evidence for {name}") for item in given.get("evidence", [])],
        }
    return {"case_id": case.case_id, "out_of_scope": out_of_scope, "fields": fields}


def load_answer(responses: Path, case_id: str) -> dict | None:
    """The stored answer for a case, or None if the case has not been run."""
    path = responses / f"{case_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def cost_usd(usage: dict) -> float:
    """Cost of one call from its token usage and PRICES."""
    return (usage.get("input_tokens", 0) * PRICES["input"]
            + usage.get("output_tokens", 0) * PRICES["output"]
            + (usage.get("cache_creation_input_tokens") or 0) * PRICES["cache_write"]
            + (usage.get("cache_read_input_tokens") or 0) * PRICES["cache_read"]) / 1_000_000


# ---------------------------------------------------------------------------
# Calling the model
# ---------------------------------------------------------------------------


class ClaudeCodeError(Exception):
    """Claude Code did not return an answer (not logged in, a usage limit, a timeout...): nothing is stored."""


def call_claude(command: list[str], message: str, timeout: int = CASE_TIMEOUT_SECONDS) -> dict:
    """One print-mode request from an empty folder. Returns what is stored for the case.

    The empty folder means no project instructions or settings are loaded. ANTHROPIC_API_KEY and
    ANTHROPIC_AUTH_TOKEN are removed so the request runs on the user's Claude plan, never on a billed key.
    """
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="resauce-baseline-b-") as empty:
        try:
            done = subprocess.run(command, input=message, capture_output=True, text=True, cwd=empty, env=env,
                                  timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            said = " ".join(_text(x) for x in (exc.stderr, exc.stdout)).strip()[:800] or "nothing"
            raise ClaudeCodeError(f"no answer within {timeout} s. Claude Code printed: {said}") from None
        except OSError as exc:
            raise ClaudeCodeError(f"{type(exc).__name__}: {exc}") from None
    try:
        output = json.loads(done.stdout)
    except json.JSONDecodeError:
        raise ClaudeCodeError(f"exit {done.returncode}: {(done.stderr or done.stdout).strip()[:500]}") from None
    if done.returncode != 0 or output.get("is_error") or output.get("subtype") != "success":
        raise ClaudeCodeError(f"{output.get('subtype')}: {str(output.get('result'))[:500]}")
    structured = output.get("structured_output")
    return {
        "route": "Claude Code print mode",
        "stop_reason": output.get("stop_reason") or "end_turn",
        "answer_text": json.dumps(structured, ensure_ascii=False) if structured is not None else output.get("result"),
        "usage": output.get("usage") or {},
        "models_reported": sorted(output.get("modelUsage") or {}),
        "claude_code_cost_usd": output.get("total_cost_usd"),
        "duration_seconds": round(time.perf_counter() - started, 3),
        "cli_output": output,  # everything Claude Code returned, kept as it came
    }


def _text(value) -> str:
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else (value or "")


def claude_code_version() -> str | None:
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _not_inside_claude_code() -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("Run this in your own terminal, not inside a Claude Code session "
                         "(Claude Code cannot be started inside itself).")


def case_folders(data: Path) -> list[Path]:
    return sorted(p for p in (data / "cases").iterdir() if p.is_dir())


def _git_commit() -> str | None:
    try:
        done = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return done.stdout.strip() if done.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _write_json(path: Path, data: dict) -> None:
    """Write in one step (temporary file, then rename), so an interrupted run never leaves half a file."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _settings(system: str) -> dict:
    command = claude_command(system)
    shown = [("<instructions: system_prompt.md>" if arg == system else "<answer_schema.json>"
              if arg == json.dumps(ANSWER_SCHEMA) else arg) for arg in command]
    return {"model": MODEL, "effort": EFFORT, "thinking": "adaptive (always on for this model)",
            "route": "Claude Code print mode on the user's Claude plan", "command": shown,
            "system_prompt_sha256": sha256(system),
            "answer_schema_sha256": sha256(json.dumps(ANSWER_SCHEMA, sort_keys=True)),
            "fallback_model": None}


CHECK_SCHEMA = {"type": "object", "properties": {"extra_context": {"type": "string"}, "model": {"type": "string"}},
                "required": ["extra_context", "model"], "additionalProperties": False}
CHECK_MESSAGE = ('Apart from this message and the system prompt "You are a test.", did you receive any other text, '
                 "context, reminders or instructions? If yes, copy all of it verbatim into extra_context. If not, "
                 "write NONE. In model, give the exact model name you are, if you know it.")


def check(out: Path) -> int:
    """One tiny request with no case data: are the settings accepted, and is anything added to the request?"""
    _not_inside_claude_code()
    out.mkdir(parents=True, exist_ok=True)
    print(f"Sending one tiny test request through Claude Code (no case data). Waiting up to "
          f"{CHECK_TIMEOUT_SECONDS // 60} minutes...", flush=True)
    try:
        stored = call_claude(claude_command("You are a test.", CHECK_SCHEMA), CHECK_MESSAGE, CHECK_TIMEOUT_SECONDS)
    except ClaudeCodeError as exc:
        print(f"The check failed: {exc}")
        return 1
    stored["checked_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    stored["claude_code_version"] = claude_code_version()
    _write_json(out / "check.json", stored)
    print(f"Claude Code {stored['claude_code_version']}; models that answered: {', '.join(stored['models_reported'])}")
    print(f"The model's report of extra context: {stored['answer_text']}")
    print(f"Saved to {display_path(out / 'check.json')}. If this looks right, run: python -m resauce.baseline_b run")
    return 0


def _dataset(data: Path) -> dict:
    try:
        d = json.loads((data / "dataset.json").read_text(encoding="utf-8"))
        return {"dataset_id": d.get("dataset_id"), "dataset_version": d.get("dataset_version")}
    except (OSError, ValueError):
        return {"dataset_id": None, "dataset_version": None}


def run(data: Path, out: Path, workers: int) -> int:
    _not_inside_claude_code()
    system = system_prompt()
    settings = _settings(system)
    command = claude_command(system)
    responses = out / "responses"
    responses.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "run.json"
    session = {"started_at": datetime.now().astimezone().isoformat(timespec="seconds"), "code_commit": _git_commit(),
               "claude_code_version": claude_code_version(), "workers": workers}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["settings"] != settings or manifest["data"] != display_path(data):
            raise SystemExit(f"{manifest_path} was made with different settings, instructions or data; "
                             "that is a new run and needs a new --out folder.")
    else:
        manifest = {"settings": settings, "started_at": session["started_at"], "data": display_path(data),
                    **_dataset(data),
                    "prices_usd_per_million_tokens": PRICES, "prices_source": PRICES_SOURCE,
                    "disclosures": [], "sessions": []}
        (out / "system_prompt.md").write_text(system + "\n", encoding="utf-8")
        (out / "answer_schema.json").write_text(json.dumps(ANSWER_SCHEMA, indent=1) + "\n", encoding="utf-8")
    manifest["sessions"].append(session)
    _write_json(manifest_path, manifest)

    todo = [f for f in case_folders(data) if not (responses / f"{f.name}.json").is_file()]
    print(f"{len(todo)} of {len(case_folders(data))} cases to run, {workers} at a time. "
          "Each takes a minute or more; progress is printed as answers arrive.")
    lock, stopped = threading.Lock(), []

    def one(folder: Path) -> None:
        with lock:
            if stopped:
                return
        message = user_message(load_case(folder), load_window(folder))
        try:
            stored = call_claude(command, message)
        except ClaudeCodeError as exc:  # login, usage limit, timeout...: stop starting cases; resume later
            with lock:
                stopped.append(f"{folder.name}: {exc}")
            return
        record = {"case_id": folder.name, **settings, "user_message_sha256": sha256(message),
                  "requested_at": datetime.now().astimezone().isoformat(timespec="seconds"), **stored}
        _write_json(responses / f"{folder.name}.json", record)
        with lock:
            done = sum(1 for _ in responses.glob("*.json"))
            print(f"{folder.name}: answered in {stored['duration_seconds']:.0f} s ({done} stored)")

    if todo:
        print(f"Sending {todo[0].name} alone first...", flush=True)
        one(todo[0])  # alone first: if the setup is wrong, only one request is spent finding out
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(one, todo[1:]))
    left = [f.name for f in case_folders(data) if not (responses / f"{f.name}.json").is_file()]
    if stopped:
        print("Stopped early: " + stopped[0])
    print(f"Cases without a stored answer: {len(left)}. "
          + ("All answers are stored." if not left else "Run the same command again to continue."))
    return 0 if not left else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m resauce.baseline_b", description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("check", "run"))
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workers", type=int, default=4, help="requests at the same time")
    args = parser.parse_args(argv)
    if args.command == "check":
        return check(args.out)
    return run(args.data.resolve(), args.out, args.workers)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
