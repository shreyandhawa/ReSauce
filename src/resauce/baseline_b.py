"""Baseline B: a large language model reads the case and applies the written rules.

Implements docs/evaluation-spec.md §5. The model gets the clinical-methods text
("How to read this document" through §9) as its instructions and one case's
files as JSON, and answers with a schema-constrained JSON object: the
out-of-scope reason, and for onset and maximum grade a §7 category, the
documented value, an explanation and evidence quotes.

Two commands (the API key is read from ANTHROPIC_API_KEY or the project's
.env file, and never printed):

    python -m resauce.baseline_b count                    # input tokens per case (free) and input cost
    python -m resauce.baseline_b run --budget USD [--workers N]   # one call per case, each answer stored

`run` skips cases that already have a stored answer, so an interrupted run can
be resumed; it never asks again for a stored case. Scoring (the evaluation runner)
reads only the stored answers and never calls the model.

The functions that build the request and turn an answer into a method output
are pure and tested without the API. The `anthropic` library is imported only
when the model is called, so the rest of ReSauce needs no extra dependency.
This module never reads reference answers or pipeline outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
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
MAX_TOKENS = 64000

# USD per million tokens for claude-opus-5-5, from Anthropic's listed prices (claude-api reference,
# cached 2026-10-06). Cache writes are 1.25 x input (5-minute cache). Used only to report cost.
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


def request_params(case: Case, window: ObservationWindow, system: str) -> dict:
    """Keyword arguments for client.messages.stream (evaluation-spec §5)."""
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_message(case, window)}],
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": ANSWER_SCHEMA}},
    }


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Turning a stored answer into a method output (pure)
# ---------------------------------------------------------------------------


def parse_answer(stored: dict) -> dict:
    """The model's JSON answer, or AnswerError if it declined, was cut off or is not valid JSON."""
    reason = stored.get("stop_reason")
    if reason == "refusal":
        details = stored.get("stop_details") or {}
        raise AnswerError(f"the model declined (category: {details.get('category')})")
    if reason == "max_tokens":
        raise AnswerError("the answer was cut off at max_tokens")
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


def _load_api_key() -> None:
    """Set ANTHROPIC_API_KEY from the project's .env file if it is not already set. Never prints it."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env = ROOT / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip() == "ANTHROPIC_API_KEY" and value.strip():
                os.environ["ANTHROPIC_API_KEY"] = value.strip().strip("'\"")
                return
    raise SystemExit("No API key: put ANTHROPIC_API_KEY=... in the project's .env file (it is git-ignored).")


def _client():
    try:
        import anthropic
    except ImportError:
        raise SystemExit('The anthropic library is not installed: run  pip install -e ".[llm]"') from None
    _load_api_key()
    return anthropic, anthropic.Anthropic()


def call_model(client, params: dict) -> dict:
    """One streamed request. Returns what is stored for the case (raises on network or server failure)."""
    started = time.perf_counter()
    with client.messages.stream(**params) as stream:
        message = stream.get_final_message()
    texts = [block.text for block in message.content if block.type == "text"]
    details = getattr(message, "stop_details", None)
    return {
        "response_id": message.id,
        "model_reported": message.model,
        "stop_reason": message.stop_reason,
        "stop_details": details.to_dict() if details is not None and hasattr(details, "to_dict") else None,
        "answer_text": "".join(texts) if texts else None,
        "text_blocks": len(texts),
        "usage": message.usage.to_dict(),
        "duration_seconds": round(time.perf_counter() - started, 3),
    }


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
    return {"model": MODEL, "effort": EFFORT, "max_tokens": MAX_TOKENS, "thinking": "adaptive (always on)",
            "system_prompt_sha256": sha256(system),
            "answer_schema_sha256": sha256(json.dumps(ANSWER_SCHEMA, sort_keys=True)),
            "fallback_model": None}


def count(data: Path) -> int:
    anthropic, client = _client()
    system = system_prompt()
    total = 0
    for folder in case_folders(data):
        params = request_params(load_case(folder), load_window(folder), system)
        tokens = client.messages.count_tokens(model=params["model"], system=params["system"],
                                              messages=params["messages"]).input_tokens
        total += tokens
    n = len(case_folders(data))
    print(f"{n} cases, {total} input tokens in total (system prompt counted once per case).")
    print(f"Input cost without caching: ${total * PRICES['input'] / 1e6:.2f}. "
          "Output (thinking + answer) is not known before the run.")
    return 0


def _dataset(data: Path) -> dict:
    try:
        d = json.loads((data / "dataset.json").read_text(encoding="utf-8"))
        return {"dataset_id": d.get("dataset_id"), "dataset_version": d.get("dataset_version")}
    except (OSError, ValueError):
        return {"dataset_id": None, "dataset_version": None}


def run(data: Path, out: Path, budget: float, workers: int) -> int:
    anthropic, client = _client()
    system = system_prompt()
    settings = _settings(system)
    responses = out / "responses"
    responses.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "run.json"
    session = {"started_at": datetime.now().astimezone().isoformat(timespec="seconds"), "code_commit": _git_commit(),
               "anthropic_library_version": anthropic.__version__, "workers": workers, "budget_usd": budget}
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

    spent = sum(cost_usd(json.loads(p.read_text(encoding="utf-8"))["usage"]) for p in responses.glob("*.json"))
    todo = [f for f in case_folders(data) if not (responses / f"{f.name}.json").is_file()]
    print(f"{len(todo)} cases to run; ${spent:.2f} already spent in this run; spending cap ${budget:.2f}.")
    lock, stopped = threading.Lock(), []

    def one(folder: Path) -> None:
        nonlocal spent
        with lock:
            if stopped or spent >= budget:
                return
        params = request_params(load_case(folder), load_window(folder), system)
        try:
            stored = call_model(client, params)
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.BadRequestError,
                anthropic.NotFoundError) as exc:  # a setup problem: no further case is requested
            with lock:
                stopped.append(f"{folder.name}: {type(exc).__name__}: {exc}")
            return
        except anthropic.APIError as exc:  # network or server failure after the library's retries: nothing stored
            print(f"{folder.name}: not stored ({type(exc).__name__}); it will be requested again on resume")
            return
        record = {"case_id": folder.name, **settings, "user_message_sha256": sha256(params["messages"][0]["content"]),
                  "requested_at": datetime.now().astimezone().isoformat(timespec="seconds"), **stored}
        _write_json(responses / f"{folder.name}.json", record)
        with lock:
            spent += cost_usd(stored["usage"])
            print(f"{folder.name}: {stored['stop_reason']}, {stored['duration_seconds']:.0f} s, "
                  f"total so far ${spent:.2f}")

    if todo:
        one(todo[0])  # alone first, so the shared instructions are written to the cache once
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(one, todo[1:]))
    left = [f.name for f in case_folders(data) if not (responses / f"{f.name}.json").is_file()]
    print(f"${spent:.2f} spent in this run. Cases without a stored answer: {len(left)}"
          + (f" ({', '.join(left)})" if left else "") + ".")
    if stopped:
        print("Stopped by a setup problem: " + stopped[0])
    return 0 if not left else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m resauce.baseline_b", description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("count", "run"))
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--budget", type=float, help="spending cap in USD: no new case is started once reached")
    parser.add_argument("--workers", type=int, default=4, help="requests at the same time")
    args = parser.parse_args(argv)
    if args.command == "count":
        return count(args.data)
    if args.budget is None:
        parser.error("run needs --budget (the spending cap agreed before the run)")
    return run(args.data.resolve(), args.out, args.budget, args.workers)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
