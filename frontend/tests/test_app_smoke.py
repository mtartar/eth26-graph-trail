"""Headless smoke test for the Streamlit frontend, using Streamlit's official AppTest.

Runs the real FastAPI backend against fixture data (no LLM involved) as a
subprocess, so this exercises real HTTP calls end to end rather than mocks —
without needing ANTHROPIC_API_KEY or spending real API credit.
"""

import os
import subprocess
import sys
import time

import httpx
import pytest
from streamlit.testing.v1 import AppTest

_TEST_PORT = 8811
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


@pytest.fixture(scope="module")
def backend_url():
    """Start the real FastAPI backend against fixture data on a dedicated test port."""
    env = {**os.environ, "DATA_SOURCE": "fixture"}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(_TEST_PORT)],
        cwd=_REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{_TEST_PORT}"
    try:
        for _ in range(50):
            try:
                if httpx.get(f"{url}/health", timeout=0.5).status_code == 200:
                    break
            except httpx.ConnectError:
                pass
            time.sleep(0.2)
        else:
            proc.terminate()
            pytest.fail("Backend did not start in time")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_app_loads_and_shows_default_transfers(backend_url):
    """The app loads without exceptions and shows the default fixture-backed table."""
    os.environ["BACKEND_URL"] = backend_url
    at = AppTest.from_file(_APP_PATH)
    at.run(timeout=15)

    assert not at.exception
    assert any("Graph Trail" in md.value for md in at.markdown)
    assert len(at.dataframe) > 0
