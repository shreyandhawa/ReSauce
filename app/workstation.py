"""The workstation API: cases, live verification, review decisions, audit trail, exports.

Plain methods returning JSON-ready dicts (streams yield dicts). Every value shown comes
from a case folder, a stored run of the frozen pipeline or the audit log.
"""

from __future__ import annotations

import csv
import html
import io
import json

from resauce.loader import load_case, study_day
from resauce.models import FICTIONAL_NOTICE

from app import findings as F
from app.pipeline import canonical_sha, error_text, pipeline_version, problems_of, run_stages
from app.sources import Sources, display_path
from app.workspace import FormProblems, Workspace, WorkspaceError, folder_fingerprint, now


class NotFound(Exception):
    pass


class BadRequest(Exception):
    def __init__(self, message: str, problems: list | None = None):
        super().__init__(message)
        self.problems = problems or []


def _pipeline_brief(version: dict) -> dict:
    """The pipeline version as written into every run and audit entry."""
    return {"tag": version["tag"], "tag_commit": version["tag_commit"], "head_commit": version["head_commit"],
            "frozen_files_match": version["frozen_files_match"],
            "frozen_files": {f["path"]: f["actual"] for f in version["frozen_files"]}}


class Workstation:
    def __init__(self, workspace: Workspace, sources: Sources | None):
        self.ws = workspace
        self.sources = sources  # the stored evaluation runs, for the "matches stored" check

    def _folder(self, case_id: str):
        try:
            return self.ws.case_folder(case_id)
        except KeyError:
            raise NotFound(f"no case {case_id!r} in this workspace") from None

    # -- GET /api/workspace --------------------------------------------------------------

    def info(self) -> dict:
        return {"path": display_path(self.ws.folder), "case_count": len(self.ws.case_ids()),
                "empty": not self.ws.case_ids(), "fictional_notice": FICTIONAL_NOTICE,
                "example_count": self.ws.example_count(),
                "pipeline": pipeline_version()}

    def load_examples(self) -> dict:
        return self.ws.load_examples()

    def import_folder(self, body: dict) -> dict:
        try:
            return self.ws.import_folder(str(body.get("path", "")))
        except WorkspaceError as exc:
            raise BadRequest(str(exc)) from None

    # -- GET /api/cases ------------------------------------------------------------------

    def cases(self) -> dict:
        decisions = F.latest_decisions(self.ws.audit_entries())
        rows = []
        for case_id in self.ws.case_ids():
            row = {"case_id": case_id}
            try:
                case = load_case(self.ws.case_folder(case_id))
            except Exception as exc:
                row.update({"invalid": error_text(exc), "problems": problems_of(exc), "status": "invalid"})
                rows.append(row)
                continue
            current = case.record.current
            run = self.ws.latest_run(case_id)
            items = F.with_decisions(case_id, run, decisions)
            row.update({
                "documents": len({d.document_id for d in case.documents}),
                "document_versions": len(case.documents),
                "record": {"icans_reported": current.icans_reported,
                           "onset_date": current.onset_date.isoformat() if current.onset_date else None,
                           "onset_day": study_day(case, current.onset_date) if current.onset_date else None,
                           "max_grade": current.max_grade, "version": current.version},
                "status": F.status(run, items),
                "open": sum(1 for i in items if i["decision"] is None),
                "open_alerts": sum(1 for i in items if i["decision"] is None and i["tier"] == F.TIER_ALERT),
                "findings": len(items),
                "last_run": run["started_at"] if run else None,
                "out_of_scope": bool(run and (run.get("resauce", {}).get("output") or {}).get("out_of_scope")),
            })
            rows.append(row)
        return {"cases": rows}

    # -- GET /api/cases/<id> -------------------------------------------------------------

    def case(self, case_id: str) -> dict:
        folder = self._folder(case_id)
        try:
            case = load_case(folder)
        except Exception as exc:
            return {"case_id": case_id, "invalid": error_text(exc), "problems": problems_of(exc)}
        run = self.ws.latest_run(case_id)
        decisions = F.latest_decisions(self.ws.audit_entries())
        return {
            "case_id": case.case_id,
            "fictional_notice": FICTIONAL_NOTICE,
            "facts": {"age_at_infusion": case.age_at_infusion, "infusion_date": case.infusion_date.isoformat()},
            "documents": [{
                "document_id": d.document_id, "version": d.version, "version_id": d.version_id,
                "status": d.status, "note_type": d.note_type, "author_role": d.author_role,
                "documented_at": d.documented_at.isoformat(timespec="minutes"),
                "documented_day": study_day(case, d.documented_at),
                "amendment_reason": d.amendment_reason, "text": d.text,
            } for d in case.documents],
            "record": {"record_id": case.record.record_id, "versions": [{
                "version": v.version, "recorded_at": v.recorded_at.isoformat(timespec="minutes"),
                "icans_reported": v.icans_reported,
                "onset_date": v.onset_date.isoformat() if v.onset_date else None,
                "onset_day": study_day(case, v.onset_date) if v.onset_date else None,
                "max_grade": v.max_grade, "change_reason": v.change_reason,
            } for v in case.record.versions]},
            "run": run,
            "findings": F.with_decisions(case_id, run, decisions),
            "stored_available": self._stored(case_id, folder) is not None,
        }

    def _stored(self, case_id: str, folder):
        """(split, stored record) when this case is in a stored evaluation and its folder is byte-identical."""
        if not self.sources:
            return None
        found = self.sources.find(case_id)
        if not found:
            return None
        split, record = found
        original = split.case_folder(case_id)
        if not original.is_dir() or folder_fingerprint(original) != folder_fingerprint(folder):
            return None
        return split, record

    # -- POST /api/cases/<id>/verify (stream) -----------------------------------------------

    def verify(self, case_id: str, with_baseline: bool, reviewer: str | None = None):
        """Run the frozen pipeline on one case; yield each stage as it finishes, then the stored run."""
        folder = self._folder(case_id)
        version = pipeline_version()
        run = {"run_id": self.ws.new_run_id(), "case_id": case_id, "started_at": now(),
               "with_baseline": with_baseline, "pipeline": _pipeline_brief(version),
               "timings_seconds": {}, "error": None, "observations": [], "timeline": None,
               "resauce": {}, "baseline_a": None}
        for stage, payload in run_stages(folder, with_baseline):
            yield {"event": "stage", "stage": stage, **payload}
            if stage == "error":
                run["error"] = payload
                break
            if "seconds" in payload:
                run["timings_seconds"][stage] = payload["seconds"]
            if stage == "extraction":
                run["observations"] = payload["observations"]
            elif stage == "timeline":
                run["timeline"] = {k: v for k, v in payload.items() if k != "seconds"}
            elif stage == "verdict":
                run["resauce"] = {k: payload[k] for k in ("output", "evidence_valid", "error") if k in payload}
            elif stage == "baseline":
                run["baseline_a"] = {k: payload[k] for k in ("output", "evidence_valid", "error") if k in payload}

        output = run["resauce"].get("output")
        run["output_sha256"] = canonical_sha(output) if output is not None else None
        run["stored_comparison"] = self._compare_stored(case_id, folder, run)
        with self.ws.lock:
            self.ws.save_run(case_id, run)
            items = F.with_decisions(case_id, run, F.latest_decisions(self.ws.audit_entries()))
            self.ws.append_audit({
            "type": "run", "case_id": case_id, "run_id": run["run_id"], "with_baseline": with_baseline,
            "reviewer": reviewer or None,
            "error": (run["error"] or {}).get("error") or run["resauce"].get("error"),
            "categories": ({n: f["category"] for n, f in output["fields"].items()} if output else None),
            "out_of_scope": ((output or {}).get("out_of_scope") or {}).get("reason"),
            "findings": len(items), "output_sha256": run["output_sha256"],
            "matches_stored": (run["stored_comparison"] or {}).get("matches"),
            "pipeline": run["pipeline"],
            })
        yield {"event": "done", "run": run, "findings": items, "status": F.status(run, items)}

    def _compare_stored(self, case_id: str, folder, run: dict) -> dict | None:
        stored = self._stored(case_id, folder)
        if stored is None:
            return None
        split, record = stored
        matches = {}
        for method, live in (("resauce", run["resauce"]), ("baseline_a", run["baseline_a"])):
            if live is None:
                continue
            stored_output = (record.get(method) or {}).get("output")
            matches[method] = None if stored_output is None or "output" not in live else live["output"] == stored_output
        return {"results_file": display_path(split.results_path), "split": split.name,
                "stored_run_date": (split.results.get("metadata") or {}).get("date"), "matches": matches}

    def verify_all(self, with_baseline: bool, reviewer: str | None = None):
        ids = self.ws.case_ids()
        yield {"event": "start", "total": len(ids)}
        for index, case_id in enumerate(ids, start=1):
            last = None
            for event in self.verify(case_id, with_baseline, reviewer):
                last = event
            if last and last["event"] == "done":
                run = last["run"]
                yield {"event": "case", "index": index, "total": len(ids), "case_id": case_id,
                       "status": last["status"], "open": sum(1 for i in last["findings"] if i["decision"] is None),
                       "matches_stored": (run.get("stored_comparison") or {}).get("matches")}
        yield {"event": "done", "total": len(ids)}

    # -- POST /api/cases (new case) --------------------------------------------------------

    def create_case(self, body: dict) -> dict:
        try:
            case_id = self.ws.create_case(body)
        except FormProblems as exc:
            raise BadRequest("The case was not saved. Fix the problems shown next to the fields.", exc.problems) from None
        return {"case_id": case_id}

    # -- review ----------------------------------------------------------------------------

    def queue(self) -> dict:
        decisions = F.latest_decisions(self.ws.audit_entries())
        items, cases_with_runs = [], 0
        for case_id in self.ws.case_ids():
            run = self.ws.latest_run(case_id)
            if run is None:
                continue
            cases_with_runs += 1
            items.extend(F.with_decisions(case_id, run, decisions))
        open_items = [i for i in items if i["decision"] is None]
        order = {n: k for k, n in enumerate(("onset", "max_grade"))}
        open_items.sort(key=lambda i: (i["tier"], i["case_id"], order.get(i["field"], 9), i["finding_id"]))
        return {"items": open_items, "decided": len(items) - len(open_items), "cases_verified": cases_with_runs,
                "cases_total": len(self.ws.case_ids())}

    def decide(self, body: dict) -> dict:
        decision = body.get("decision")
        note = str(body.get("note") or "").strip()
        reviewer = str(body.get("reviewer") or "").strip()
        problems = []
        if decision not in F.DECISIONS:
            problems.append({"key": "decision", "message": "choose Confirm discrepancy, Dismiss or Needs clinician"})
        if not note:
            problems.append({"key": "note", "message": "a note is required for every decision"})
        if not reviewer:
            problems.append({"key": "reviewer", "message": "enter the reviewer's name"})
        case_id = str(body.get("case_id") or "")
        self._folder(case_id)
        with self.ws.lock:  # the run checked here is the run the decision is logged against
            return self._decide_locked(body, case_id, decision, note, reviewer, problems)

    def _decide_locked(self, body, case_id, decision, note, reviewer, problems) -> dict:
        run = self.ws.latest_run(case_id)
        if run is None or run.get("run_id") != body.get("run_id"):
            problems.append({"key": "form", "message": "this case was verified again since the item was shown; reload"})
        elif not any(f["finding_id"] == body.get("finding_id") for f in F.with_decisions(case_id, run, {})):
            problems.append({"key": "form", "message": "no such finding in the latest run"})
        if problems:
            raise BadRequest("The decision was not saved.", problems)
        finding = next(f for f in F.with_decisions(case_id, run, {}) if f["finding_id"] == body["finding_id"])
        entry = self.ws.append_audit({
            "type": "decision", "case_id": case_id, "finding_id": finding["finding_id"],
            "field": finding["field"], "finding": finding["label"], "decision": decision,
            "decision_label": F.decision_label(decision, finding["kind"]), "note": note, "reviewer": reviewer,
            "run_id": run["run_id"], "output_sha256": run["output_sha256"],
            "pipeline": _pipeline_brief(pipeline_version()),
        })
        return {"entry": entry}

    def audit(self) -> dict:
        return {"entries": self.ws.audit_entries(), "path": display_path(self.ws.audit_path)}

    # -- exports ---------------------------------------------------------------------------

    def export_case(self, case_id: str) -> dict:
        detail = self.case(case_id)
        if detail.get("invalid"):
            raise BadRequest(f"{case_id} cannot be loaded, so no report was written: {detail['invalid']}")
        name = f"{case_id}-report-{self.ws.new_run_id()}.html"
        self.ws.export_path(name).write_text(_report_html(detail, self.ws.audit_entries()), encoding="utf-8")
        return {"file": display_path(self.ws.export_path(name)), "url": f"/exports/{name}"}

    def export_csv(self) -> dict:
        decisions = F.latest_decisions(self.ws.audit_entries())
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["case_id", "run_id", "run_time", "pipeline_tag", "pipeline_tag_commit", "frozen_files_match",
                         "finding_id", "tier", "field", "category", "finding", "record_value", "documented_value",
                         "detail", "evidence", "decision", "note", "reviewer", "decision_time"])
        for case_id in self.ws.case_ids():
            run = self.ws.latest_run(case_id)
            if run is None:
                writer.writerow([case_id, "", "", "", "", "", "", "", "", "", "not verified"] + [""] * 8)
                continue
            p = run["pipeline"]
            items = F.with_decisions(case_id, run, decisions)
            if not items:
                status = "error" if F.status(run, items) == "error" else "no findings"
                writer.writerow([case_id, run["run_id"], run["started_at"], p["tag"], p["tag_commit"],
                                 p["frozen_files_match"], "", "", "", "", status] + [""] * 8)
            for i in items:
                d = i["decision"] or {}
                writer.writerow([
                    case_id, run["run_id"], run["started_at"], p["tag"], p["tag_commit"], p["frozen_files_match"],
                    i["finding_id"], F.TIER_NAMES[i["tier"]], i["field"] or "", i["category"] or "", i["label"],
                    _plain(i.get("record_value")), _plain(i.get("documented_value")), i.get("detail") or "",
                    " | ".join(f'{e.get("document_id")} v{e.get("version")} {e.get("start")}-{e.get("end")} "{e.get("quote")}"'
                               for e in i["evidence"]),
                    d.get("label", "open"), d.get("note", ""), d.get("reviewer", ""), d.get("time", ""),
                ])
        name = f"findings-{self.ws.new_run_id()}.csv"
        self.ws.export_path(name).write_text(out.getvalue(), encoding="utf-8")
        return {"file": display_path(self.ws.export_path(name)), "url": f"/exports/{name}"}


def _plain(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _report_html(d: dict, audit: list[dict]) -> str:
    """A printable, self-contained case report (no scripts, no external files)."""
    e = html.escape
    run = d.get("run")
    rec = d["record"]["versions"][-1]
    rows = []
    for v in d["record"]["versions"]:
        rows.append(f"<tr><td>v{v['version']}</td><td>{e(v['recorded_at'])}</td><td>{'yes' if v['icans_reported'] else 'no'}</td>"
                    f"<td>{e(v['onset_date'] or 'empty')}</td><td>{e(str(v['max_grade']) if v['max_grade'] is not None else 'empty')}</td>"
                    f"<td>{e(v['change_reason'] or '')}</td></tr>")
    body = [f"<h1>Case report {e(d['case_id'])}</h1>",
            f"<p class='notice'>{e(d['fictional_notice'])} Synthetic data only. Results on synthetic data are not clinical validation.</p>",
            f"<p>Age at infusion {d['facts']['age_at_infusion']} · infusion (Day 0) {e(d['facts']['infusion_date'])} · "
            f"{len({x['document_id'] for x in d['documents']})} documents, {len(d['documents'])} versions</p>",
            "<h2>Research record</h2><table><tr><th>Version</th><th>Recorded</th><th>ICANS</th><th>Onset</th><th>Max grade</th><th>Change reason</th></tr>",
            *rows, "</table>"]
    if not run:
        body.append("<h2>Verification</h2><p>Not verified yet.</p>")
    else:
        p = run["pipeline"]
        body.append("<h2>Verification</h2>")
        body.append(f"<p>Run {e(run['run_id'])} at {e(run['started_at'])}. Pipeline {e(p['tag'])} "
                    f"(commit {e((p['tag_commit'] or 'unknown')[:12])}); frozen files match docs/freeze.md: "
                    f"{'yes' if p['frozen_files_match'] else 'NO'}.</p>")
        if run.get("error"):
            body.append(f"<p><strong>The run stopped with an error:</strong> {e(run['error'].get('error', ''))}</p>")
        out = run.get("resauce", {}).get("output")
        if out and not out.get("out_of_scope"):
            body.append("<table><tr><th>Field</th><th>Record</th><th>Documented</th><th>Category</th></tr>")
            for name in F.FIELDS:
                f = out["fields"][name]
                body.append(f"<tr><td>{F.FIELD_NAMES[name]}</td><td>{e(_plain(f['record_value']) or 'empty')}</td>"
                            f"<td>{e(_plain(f['documented_value']))}</td><td>{e(F.category_label(f['category'], f))}</td></tr>")
            body.append("</table>")
        body.append("<h2>Findings and decisions</h2>")
        if not d["findings"]:
            body.append("<p>No findings.</p>")
        for i in d["findings"]:
            dec = i["decision"]
            body.append(f"<section class='finding'><h3>{e(i['label'])}</h3>")
            if i.get("detail"):
                body.append(f"<p>{e(i['detail'])}</p>")
            for ev in i["evidence"]:
                body.append(f"<blockquote><span class='ref'>{e(str(ev.get('document_id')))} v{ev.get('version')} · "
                            f"{ev.get('start')}–{ev.get('end')}{' · ' + e(ev['role']) if ev.get('role') else ''}</span>"
                            f"<q>{e(str(ev.get('quote')))}</q></blockquote>")
            body.append(f"<p class='decision'><strong>Decision:</strong> {e(dec['label'])} by {e(dec['reviewer'])} "
                        f"at {e(dec['time'])}. Note: {e(dec['note'])}</p>" if dec else "<p class='decision'><strong>Decision:</strong> open</p>")
            body.append("</section>")
        history = [a for a in audit if a.get("case_id") == d["case_id"] and a.get("type") == "decision"]
        if history:
            body.append("<h2>Decision history (audit log)</h2><table><tr><th>Time</th><th>Reviewer</th><th>Finding</th><th>Decision</th><th>Note</th><th>Run</th></tr>")
            body += [f"<tr><td>{e(a['time'])}</td><td>{e(a['reviewer'])}</td><td>{e(a['finding'])}</td><td>{e(a['decision_label'])}</td>"
                     f"<td>{e(a['note'])}</td><td>{e(a['run_id'])}</td></tr>" for a in history]
            body.append("</table>")
        body.append("<h2>Pipeline version</h2><table><tr><th>Frozen file</th><th>SHA-256 at this run</th></tr>")
        body += [f"<tr><td>{e(k)}</td><td class='mono'>{e(v or 'missing')}</td></tr>" for k, v in p["frozen_files"].items()]
        body.append("</table>")
    body.append("<p class='foot'>ReSauce is a research proof of concept, not a clinical decision tool. "
                "Each category is a potential discrepancy for human review, never a verdict (clinical-methods §7).</p>")
    style = ("body{font:15px/1.55 system-ui,sans-serif;color:#1d2427;max-width:52rem;margin:2rem auto;padding:0 1rem}"
             "h1{font-size:1.6rem}h2{font-size:1.15rem;margin-top:2rem;border-bottom:1px solid #ccd;padding-bottom:.2rem}"
             "h3{font-size:1rem;margin:.2rem 0}table{border-collapse:collapse;width:100%;font-size:.9rem}"
             "td,th{border:1px solid #ccd;padding:.3rem .5rem;text-align:left;vertical-align:top}"
             ".notice{background:#eef2f2;padding:.5rem .75rem}.finding{border-left:3px solid #1c7c8c;padding:.2rem .8rem;margin:1rem 0}"
             "blockquote{margin:.4rem 0;padding:.3rem .6rem;background:#f5f7f7}.ref,.mono{font-family:ui-monospace,monospace;font-size:.8rem;display:block;color:#55636a}"
             ".foot{margin-top:2rem;color:#55636a;font-size:.85rem}@media print{body{margin:0}}")
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>ReSauce report {e(d['case_id'])}</title>"
            f"<style>{style}</style></head><body>{''.join(body)}</body></html>")
