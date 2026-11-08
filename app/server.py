"""A small local HTTP server: the JSON API plus the built web page (web/dist)."""

from __future__ import annotations

import json
import mimetypes
import re
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.api import Api, NotFound
from app.sources import ROOT

STATIC_DIR = ROOT / "web" / "dist"
CASE_PATH = re.compile(r"/api/cases/([^/]+)")
RUN_PATH = re.compile(r"/api/cases/([^/]+)/run")

MISSING_BUILD = """<!doctype html><meta charset="utf-8"><title>ReSauce</title>
<body style="font:16px/1.5 system-ui;max-width:40rem;margin:4rem auto;padding:0 1rem">
<h1>The web page has not been built yet</h1>
<p>The API is running (try <a href="/api/summary">/api/summary</a>), but <code>web/dist/</code> is missing.</p>
<p>Build it once with: <code>cd web &amp;&amp; npm install &amp;&amp; npm run build</code>, then reload.</p>
</body>"""

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


def make_handler(api: Api, static_dir: Path = STATIC_DIR):
    static_root = static_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "ReSauceDemo"

        def log_request(self, code="-", size="-"):  # one short line per request
            print(f"  {self.command} {self.path} -> {code}")

        def log_message(self, fmt, *args):  # errors and anything else the base class logs
            print("  " + fmt % args)

        def _send(self, status: int, body: bytes, content_type: str, cache: str = "no-store"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8")

        def _api(self, call):
            try:
                self._json(HTTPStatus.OK, call())
            except NotFound as exc:
                self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            except Exception as exc:
                traceback.print_exc()
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"{type(exc).__name__}: {exc}"})

        def do_GET(self):
            path = unquote(urlsplit(self.path).path)
            if path == "/api/summary":
                return self._api(api.summary)
            if path == "/api/cases":
                return self._api(api.cases)
            match = CASE_PATH.fullmatch(path)
            if match:
                return self._api(lambda: api.case(match.group(1)))
            if path.startswith("/api/"):
                return self._json(HTTPStatus.NOT_FOUND, {"error": f"no endpoint {path}"})
            return self._static(path)

        do_HEAD = do_GET

        def do_POST(self):
            path = unquote(urlsplit(self.path).path)
            match = RUN_PATH.fullmatch(path)
            if match:
                return self._api(lambda: api.run(match.group(1)))
            self._json(HTTPStatus.NOT_FOUND, {"error": f"no endpoint POST {path}"})

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


def serve(api: Api, host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(api))
    shown = "localhost" if host in ("127.0.0.1", "localhost") else host
    print(f"ReSauce demo app running at http://{shown}:{port}  (press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
