"""Local lifecycle controller for the demo inference server.

Solves the "start the demo without a terminal" requirement from
docs/DEMO_MODEL_COMPARISON.md's server-control enhancement, within the
hard browser-security constraint that a static HTML/JS page cannot
spawn processes or run shell commands. Per that constraint (and the
plan's explicit permission for "a tiny local launcher with the simplest
possible UX" as the fallback when a browser page alone cannot do it):

    uv run python tools/realtime_demo/launcher.py

is the ONE command a user runs manually. Everything after that --
starting the actual inference server (server.py), stopping it, checking
whether it's already running -- is then controllable from the
dashboard's "Start Demo" / "Stop Demo" buttons, via this controller's
small, fixed HTTP API.

Architecture:

    Dashboard (dashboard/realtime_demo.js)
          |
          | POST /start | POST /stop | GET /status   (127.0.0.1:8766)
          v
    This controller (launcher.py)
          |
          | controlled subprocess spawn -- ALWAYS the exact same fixed
          | command, never anything derived from request input
          v
    uv run python tools/realtime_demo/server.py  ->  127.0.0.1:8765

Security boundaries (all deliberate, see docs/DEMO_MODEL_COMPARISON.md's
"Security Requirements" section):
  - Binds to 127.0.0.1 only -- never reachable from another machine.
  - Exposes exactly three fixed operations: /status, /start, /stop.
  - /start always spawns the SAME hardcoded command
    (["uv", "run", "python", "<absolute path to server.py>"]) --
    the request body is never read for /start or /stop, so there is no
    way for a browser request to inject a different executable, path,
    or shell string. This is not a generic "run a command" endpoint.
  - /stop only ever terminates a subprocess THIS controller itself
    spawned (tracked via a Popen handle). If an inference server is
    already running but was started manually in a separate terminal
    (not by this controller), /stop reports that plainly and does NOT
    attempt to find or kill an arbitrary process bound to port 8765 --
    killing a process by port lookup would be exactly the kind of
    unsafe, overly-broad action this design avoids.
  - /start first checks (via a real HTTP probe of :8765/health, not
    just "did I spawn something") whether an inference server is
    already responding, and if so does NOT spawn a second, duplicate
    one -- it simply reports that the existing server was found.

Run with: uv run python tools/realtime_demo/launcher.py
Then open dashboard/index.html and use the "Demo Server" controls.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONTROLLER_HOST = "127.0.0.1"
CONTROLLER_PORT = 8766

INFERENCE_HOST = "127.0.0.1"
INFERENCE_PORT = 8765
INFERENCE_HEALTH_URL = f"http://{INFERENCE_HOST}:{INFERENCE_PORT}/health"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = Path(__file__).resolve().parent / "server.py"
DASHBOARD_INDEX = PROJECT_ROOT / "dashboard" / "index.html"

# Fixed, never derived from any request: this is the ONLY command this
# controller will ever spawn.
if shutil.which("uv"):
    SERVER_COMMAND = ["uv", "run", "python", str(SERVER_SCRIPT)]
else:
    # Fallback if `uv` is not on PATH: reuse the already-active
    # interpreter (assumes it has the project's dependencies installed,
    # e.g. this launcher itself was started with `uv run python ...`).
    SERVER_COMMAND = [sys.executable, str(SERVER_SCRIPT)]

STARTUP_TIMEOUT_SECONDS = 25
STARTUP_POLL_INTERVAL_SECONDS = 0.5

_managed_process: subprocess.Popen | None = None


def _probe_inference_server() -> bool:
    try:
        with urllib.request.urlopen(INFERENCE_HEALTH_URL, timeout=1.5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


def _start_inference_server() -> dict:
    global _managed_process

    if _probe_inference_server():
        return {"status": "already_running", "managed_by_this_controller": _managed_process is not None}

    if _managed_process is not None and _managed_process.poll() is None:
        # We already have a live handle but health probe failed -- still starting up.
        pass
    else:
        _managed_process = subprocess.Popen(
            SERVER_COMMAND,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    import time

    waited = 0.0
    while waited < STARTUP_TIMEOUT_SECONDS:
        if _probe_inference_server():
            return {"status": "started", "managed_by_this_controller": True}
        if _managed_process is not None and _managed_process.poll() is not None:
            return {
                "status": "failed",
                "error": f"server process exited early (code {_managed_process.returncode})",
            }
        time.sleep(STARTUP_POLL_INTERVAL_SECONDS)
        waited += STARTUP_POLL_INTERVAL_SECONDS

    return {"status": "timeout", "error": f"server did not become ready within {STARTUP_TIMEOUT_SECONDS}s"}


def _stop_inference_server() -> dict:
    global _managed_process

    if _managed_process is None or _managed_process.poll() is not None:
        if _probe_inference_server():
            return {
                "status": "not_managed",
                "message": "A demo server is running but was not started by this controller "
                "(e.g. started manually in a terminal). Stop it there directly -- this "
                "controller only stops servers it started itself.",
            }
        return {"status": "already_stopped"}

    _managed_process.terminate()
    try:
        _managed_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _managed_process.kill()
        _managed_process.wait(timeout=5)
    _managed_process = None
    return {"status": "stopped"}


class ControllerRequestHandler(BaseHTTPRequestHandler):
    def _cors_headers(self) -> None:
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

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/status":
            running = _probe_inference_server()
            self._send_json(
                200,
                {
                    "controller": "ok",
                    "inference_server_running": running,
                    "managed_by_this_controller": _managed_process is not None
                    and _managed_process.poll() is None,
                },
            )
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        # Deliberately ignores any request body -- /start and /stop take
        # no parameters, so there is nothing in the request that could
        # influence what command runs.
        if self.path == "/start":
            self._send_json(200, _start_inference_server())
            return
        if self.path == "/stop":
            self._send_json(200, _stop_inference_server())
            return
        self._send_json(404, {"error": "not found"})

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass


def main() -> None:
    server = ThreadingHTTPServer((CONTROLLER_HOST, CONTROLLER_PORT), ControllerRequestHandler)
    print(f"Demo lifecycle controller listening on http://{CONTROLLER_HOST}:{CONTROLLER_PORT} (localhost only)")
    print(f"It can start/stop the inference server ({' '.join(SERVER_COMMAND)}) on request.")

    if DASHBOARD_INDEX.exists():
        try:
            webbrowser.open(DASHBOARD_INDEX.as_uri())
            print(f"Opened {DASHBOARD_INDEX} in your default browser.")
        except Exception:  # noqa: BLE001 -- opening a browser is a convenience, not required
            print(f"Open {DASHBOARD_INDEX} in a browser manually.")

    print("In the dashboard, use 'Live Model Demo' > Demo Server: [Start Demo].")
    print("Press Ctrl+C here to stop the controller (and any server it started).")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down controller...")
        _stop_inference_server()
        server.shutdown()


if __name__ == "__main__":
    main()
