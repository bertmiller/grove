"""Background HTTP server for the dashboard."""

from __future__ import annotations

import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grove.state import RunState

_state_ref: RunState | None = None
_dashboard_html: str | None = None


def _load_dashboard_html() -> str:
    global _dashboard_html
    if _dashboard_html is None:
        html_path = Path(__file__).parent / "dashboard.html"
        _dashboard_html = html_path.read_text()
    return _dashboard_html


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            html = _load_dashboard_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/state":
            data = _state_ref.to_dict() if _state_ref else {}
            body = json.dumps(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path == "/transcripts":
            # List available transcript files
            names = []
            if _state_ref:
                tdir = _state_ref.run_dir / "transcripts"
                if tdir.exists():
                    for child in sorted(tdir.iterdir()):
                        jsonl = child / "transcript.jsonl"
                        if jsonl.exists():
                            names.append(child.name)
            body = json.dumps(names)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path.startswith("/transcripts/"):
            # Serve a specific transcript JSONL
            name = self.path[len("/transcripts/"):]
            # Sanitise: only allow alphanumeric, underscore, dash
            if not all(c.isalnum() or c in ("_", "-") for c in name) or not name:
                self.send_error(400)
                return
            if not _state_ref:
                self.send_error(404)
                return
            jsonl = _state_ref.run_dir / "transcripts" / name / "transcript.jsonl"
            if not jsonl.exists():
                self.send_error(404)
                return
            data = jsonl.read_text()
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data.encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress request logging


def _find_open_port(start: int = 8150, attempts: int = 20) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No open port found in range {start}-{start + attempts}")


def start_dashboard_server(state: RunState) -> int:
    """Start the dashboard HTTP server in a background thread. Returns the port."""
    global _state_ref
    _state_ref = state

    port = _find_open_port()
    server = HTTPServer(("", port), DashboardHandler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return port
