"""Regression tests for application startup via main.py.

Reproduces the launch path of start_converter.bat:
`venv_converter\\Scripts\\python.exe main.py`.

Bug (fixed): main.py called asyncio.run(create_app()), which only *builds*
the web.Application object and returns immediately, so the process printed
the banner and exited without ever serving http://localhost:8080.
"""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
HOST = "localhost"
PORT = 8080
BASE_URL = f"http://{HOST}:{PORT}"
STARTUP_TIMEOUT = 30  # seconds


def _server_responds(timeout: float = 1.0) -> bool:
    """Check if the server answers GET /api/status with 200."""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


@pytest.mark.integration
def test_main_py_starts_and_serves_http():
    """main.py must start the web server and keep running until terminated."""
    proc = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "main.py")],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        # Wait until the server responds, asserting the process stays alive.
        # Before the fix the process exited right after printing the banner.
        deadline = time.time() + STARTUP_TIMEOUT
        while time.time() < deadline:
            if _server_responds():
                break
            assert proc.poll() is None, (
                f"main.py exited prematurely with code {proc.returncode}"
            )
            time.sleep(0.5)
        else:
            output = proc.communicate()[0].decode(errors="replace")
            pytest.fail(
                f"Server did not respond within {STARTUP_TIMEOUT}s.\nOutput:\n{output}"
            )

        # Process must still be alive while serving.
        assert proc.poll() is None

        # /api/status must return valid JSON with expected structure.
        with urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
        assert data["status"] == "ok"
        assert data["conversions_max"] >= 1
        assert "uploads" in data["temp_dirs"]

        # Main page must be served as well.
        with urllib.request.urlopen(f"{BASE_URL}/", timeout=5) as resp:
            assert resp.status == 200
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


@pytest.mark.integration
def test_main_module_wires_up_server_entrypoint():
    """main.py must invoke the server entry point (web_converter.app.main),
    not the bare app factory (create_app) which does not run the server."""
    import ast

    source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "web_converter.app":
            imported_names.update(alias.name for alias in node.names)

    assert "main" in imported_names, (
        "main.py should import the server entry point 'main' "
        "from web_converter.app, got: %s" % sorted(imported_names)
    )
    assert "create_app" not in imported_names
