from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from backend import console_service

HOST = "127.0.0.1"
PORT = 8765
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


class ConsoleHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json({"ok": True, "service": "agentflowkit-console"})
            return
        if self.path == "/api/capabilities":
            self._json(console_service.capabilities() | {"provider": console_service.provider_status()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            self._handle_post()
        except Exception as exc:
            self._json({"ok": False, "error": str(exc), "error_type": type(exc).__name__}, 500)

    def _handle_post(self) -> None:
        payload = self._payload()
        if self.path == "/api/workflows/preview":
            self._json({"ok": True} | console_service.preview_workflow(payload))
            return
        if self.path == "/api/workflows/run":
            self._json({"ok": True} | console_service.run_workflow(payload))
            return
        if self.path == "/api/providers/grok/smoke-test":
            self._json({"ok": True, "provider": console_service.grok_smoke_test()})
            return
        self._json({"ok": False, "error": f"Unknown route: {self.path}"}, 404)

    def _payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Request payload must be a JSON object")
        return data

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ConsoleHandler)
    print(f"AgentFlowKit Console: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
