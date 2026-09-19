"""Local Python inference server for the dashboard's live model demo.

Architecture decision (docs/DEMO_MODEL_COMPARISON.md Sections 6-8):

    Browser Dashboard (dashboard/realtime_demo.js)
          |
          | HTTP POST /predict  (raw JPEG bytes)
          v
    This local server (127.0.0.1 only)
          |
          +-- shared face detection (up to MAX_DEMO_FACES faces, see inference.py)
                    |
                    +-- per face: Original crop -> HSEmotion
                    +-- per face: Original crop -> ArcFace + Logistic Regression
                    +-- per face: CLAHE(crop)   -> HSEmotion
                    +-- per face: CLAHE(crop)   -> ArcFace + Logistic Regression

    (CLAHE preprocessing per EXP-006, see clahe_preprocessing.py;
    ArcFace = demo-only fit-once artifact, see build_demo_classifier.py.
    See inference.py for the full multi-face, 4-path pipeline and the
    /predict response schema, which returns a "faces" array.)

A separate, optional lifecycle controller (tools/realtime_demo/launcher.py,
127.0.0.1:8766) can start/stop THIS server on request from the dashboard
-- it is a distinct process from this one and does not change anything
in this file. See launcher.py's module docstring for that design.

Option chosen: HTTP frame requests (Option B), not WebSocket (Option A).
Reasoning, per the plan's explicit instruction to justify before adding
any new dependency: this repository has no WebSocket library installed
(no `websockets`, no `fastapi`, no `flask`), and the demo's throttled,
~1.5 FPS polling rate does not need a persistent socket connection. A
plain `http.server.ThreadingHTTPServer` (Python standard library, zero
new dependencies) is sufficient, simpler to reason about, and easier to
debug for a one-off conference demo than adding a new web framework
dependency would be. Only one of the two options is implemented, per
instruction.

Privacy (docs/DEMO_MODEL_COMPARISON.md Section 26): this server binds to
127.0.0.1 only (not 0.0.0.0), so it is not reachable from outside the
local machine. It does not write received frames to disk anywhere, does
not forward them to any external service, and holds each frame only in
memory for the duration of one /predict request.

Run with: uv run python tools/realtime_demo/server.py
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inference import DemoInferenceEngine, decode_jpeg_bytes  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765

engine: DemoInferenceEngine | None = None


class DemoRequestHandler(BaseHTTPRequestHandler):
    def _cors_headers(self) -> None:
        # The dashboard may be opened as a local file:// page (origin "null")
        # or served from a dev server; allow either to reach this
        # localhost-only server for the demo.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # CORS preflight
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "face_detection_available": engine.face_app is not None,
                    "hsemotion_available": engine.hsemotion_model is not None,
                    "arcface_available": engine.arcface_classifier is not None,
                    "load_errors": engine.load_errors,
                },
            )
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/predict":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            self._send_json(400, {"error": "empty request body"})
            return

        raw = self.rfile.read(length)
        frame = decode_jpeg_bytes(raw)
        if frame is None:
            self._send_json(400, {"error": "could not decode image"})
            return

        try:
            result = engine.process_frame(frame)
        except Exception as exc:  # noqa: BLE001 -- report, don't crash the server process
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(200, result)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 -- quiet default logging
        pass


def main() -> None:
    global engine
    print("Loading models (this can take a few seconds)...")
    engine = DemoInferenceEngine()

    if engine.load_errors:
        print("WARNING: some models failed to load:")
        for name, err in engine.load_errors.items():
            print(f"  - {name}: {err}")
        print("The server will still start; unavailable models will report 'unavailable' per request.")
    else:
        print("All models loaded successfully.")

    server = ThreadingHTTPServer((HOST, PORT), DemoRequestHandler)
    print(f"Demo inference server listening on http://{HOST}:{PORT} (localhost only)")
    print("Open dashboard/index.html in a browser, then use 'Live Model Demo' > 'Start Camera'.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
