"""A small local HTTP server: the JSON API, streamed pipeline runs and the built page (web/dist).

It listens on 127.0.0.1 only and makes no network calls. Requests that change the
workspace must be JSON from this app's own page: a JSON content type cannot be sent
cross-site without a CORS preflight (which this server never approves), and the Origin and
Host headers must name this computer.
"""

from __future__ import annotations

import json
import mimetypes
import re
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from app.api import Api
from app.pipeline import LINES
from app.sources import ROOT
from app.workstation import BadRequest, NotFound, Workstation

STATIC_DIR = ROOT / "web" / "dist"
CASE_PATH = re.compile(r"/api/cases/(SYN-[0-9]{4})")
VERIFY_PATH = re.compile(r"/api/cases/(SYN-[0-9]{4})/verify")
EXPORT_CASE_PATH = re.compile(r"/api/export/case/(SYN-[0-9]{4})")
EXPORT_FILE = re.compile(r"/exports/((?:SYN-[0-9]{4}-report|findings)-[0-9T-]+\.(html|csv))")
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
MAX_BODY = 5 * 1024 * 1024  # bytes; a new case with long notes is well under this

MISSING_BUILD = """<!doctype html><meta charset="utf-8"><title>ReSauce</title>
<body style="font:16px/1.5 system-ui;max-width:40rem;margin:4rem auto;padding:0 1rem">
<h1>The web page has not been built yet</h1>
<p>The API is running, but <code>web/dist/</code> is missing.</p>
<p>Build it once with: <code>cd web &amp;&amp; npm install &amp;&amp; npm run build</code>, then reload.</p>
</body>"""

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


def _host_of(value: str | None) -> str | None:
    if not value:
        return None
    netloc = urlsplit(value).netloc if "//" in value else value
    return netloc.rsplit(":", 1)[0].strip("[]") if netloc else None


def make_handler(validation: Api, station: Workstation, static_dir: Path = STATIC_DIR):
    static_root = static_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "ReSauce"

        def log_request(self, code="-", size="-"):  # one short line per request
            print(f"  {self.command} {self.path} -> {code}")

        def log_message(self, fmt, *args):
            print("  " + fmt % args)

        def _send(self, status: int, body: bytes, content_type: str, cache: str = "no-store", extra=None):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, payload: dict):
            self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _api(self, call):
            try:
                self._json(HTTPStatus.OK, call())
            except NotFound as exc:
                self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            except BadRequest as exc:
                self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc), "problems": exc.problems})
            except Exception as exc:
                traceback.print_exc()
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"{type(exc).__name__}: {exc}"})

        def _stream(self, events):
            """Send one JSON object per line as each is produced (a live run, never buffered)."""
            try:
                first = next(events)
            except NotFound as exc:
                return self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            gone = False
            try:
                for event in _chain(first, events):
                    if gone:
                        continue  # the page went away: finish the run so it is still stored and logged
                    try:
                        self.wfile.write((json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        gone = True
            except Exception as exc:
                traceback.print_exc()
                if not gone:
                    self.wfile.write((json.dumps({"event": "failed", "error": f"{type(exc).__name__}: {exc}"}) + "\n").encode())

        def _body(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                raise BadRequest("The request size is not a number.") from None
            if length < 0 or length > MAX_BODY:
                raise BadRequest("The request is too large.")
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise BadRequest("The request was not valid JSON.") from None
            if not isinstance(data, dict):
                raise BadRequest("The request must be a JSON object.")
            return data

        def _local_page(self) -> bool:
            if _host_of(self.headers.get("Host")) not in LOCAL_HOSTS:
                return False
            origin = self.headers.get("Origin")
            if origin and _host_of(origin) not in LOCAL_HOSTS:
                return False
            return (self.headers.get("Content-Type") or "").split(";")[0].strip() == "application/json"

        def do_GET(self):
            if _host_of(self.headers.get("Host")) not in LOCAL_HOSTS:
                return self._send(HTTPStatus.FORBIDDEN, b"forbidden", "text/plain")
            path = unquote(urlsplit(self.path).path)
            routes = {"/api/summary": validation.summary, "/api/workspace": station.info,
                      "/api/cases": station.cases, "/api/queue": station.queue, "/api/audit": station.audit}
            if path in routes:
                return self._api(routes[path])
            match = CASE_PATH.fullmatch(path)
            if match:
                return self._api(lambda: station.case(match.group(1)))
            match = EXPORT_FILE.fullmatch(path)
            if match:
                return self._export_file(match.group(1), match.group(2))
            if path.startswith("/api/"):
                return self._json(HTTPStatus.NOT_FOUND, {"error": f"no endpoint {path}"})
            return self._static(path)

        do_HEAD = do_GET

        def do_POST(self):
            if not self._local_page():
                return self._json(HTTPStatus.FORBIDDEN, {"error": "requests must come from the ReSauce page on this computer"})
            parts = urlsplit(self.path)
            path = unquote(parts.path)
            query = parse_qs(parts.query)
            baseline = query.get("baseline", ["0"])[0] == "1"
            reviewer = query.get("reviewer", [""])[0].strip()[:120] or None
            line = query.get("pipeline", ["v1"])[0]  # "v1" (frozen) or "v2" (development line)
            match = VERIFY_PATH.fullmatch(path)
            if match or path == "/api/verify-all":
                if line not in LINES:
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": f"unknown pipeline {line!r}; use one of {', '.join(LINES)}"})
                if match:
                    return self._stream(station.verify(match.group(1), baseline, reviewer, line))
                return self._stream(station.verify_all(baseline, reviewer, line))
            match = EXPORT_CASE_PATH.fullmatch(path)
            if match:
                return self._api(lambda: station.export_case(match.group(1)))
            routes = {
                "/api/workspace/examples": lambda: station.load_examples(),
                "/api/workspace/import": lambda: station.import_folder(self._body()),
                "/api/cases": lambda: station.create_case(self._body()),
                "/api/decisions": lambda: station.decide(self._body()),
                "/api/export/csv": lambda: station.export_csv(),
            }
            if path in routes:
                return self._api(routes[path])
            self._json(HTTPStatus.NOT_FOUND, {"error": f"no endpoint POST {path}"})

        def _export_file(self, name: str, kind: str):
            target = station.ws.export_path(name)
            if not target.is_file():
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            if kind == "csv":
                return self._send(HTTPStatus.OK, target.read_bytes(), "text/csv; charset=utf-8",
                                  extra={"Content-Disposition": f'attachment; filename="{name}"'})
            return self._send(HTTPStatus.OK, target.read_bytes(), "text/html; charset=utf-8",
                              extra={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})

        def _static(self, path: str):
            index = static_root / "index.html"
            if not index.is_file():
                return self._send(HTTPStatus.OK, MISSING_BUILD.encode("utf-8"), "text/html; charset=utf-8")
            target = (static_root / path.lstrip("/")).resolve()
            if not target.is_relative_to(static_root):
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            if target.is_file():
                kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                if kind.startswith("text/") or kind.endswith("javascript"):
                    kind += "; charset=utf-8"
                # Files in assets/ have a content hash in their name, so they can be cached.
                cache = "public, max-age=31536000, immutable" if "/assets/" in path else "no-cache"
                return self._send(HTTPStatus.OK, target.read_bytes(), kind, cache)
            if Path(path).suffix:  # a missing file, not a page
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            return self._send(HTTPStatus.OK, index.read_bytes(), "text/html; charset=utf-8", "no-cache")

    return Handler


def _chain(first, rest):
    yield first
    yield from rest


def serve(validation: Api, station: Workstation, port: int) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(validation, station))
    print(f"ReSauce running at http://localhost:{port}  (this computer only; press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
