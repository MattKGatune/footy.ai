"""Layer 3: production smoke tests.

These run against the LIVE deployment to catch the class of failure that only
appears in production (e.g. the DuckDB httpfs hang that local tests can't see).
They make real HTTP calls to the public URL — no app import, no R2 creds.

Opt-in only, so a bare `pytest` never hits production:

    RUN_SMOKE=1 pytest -m smoke

Configure the target with FOOTY_PROD_URL (defaults to the known deployment).
The generous timeouts both tolerate Render free-tier cold starts and still fail
fast on a true hang (the old bug ran >180s).
"""
import os

import httpx
import pytest

PROD_URL = os.getenv("FOOTY_PROD_URL", "https://footy-ai-u99r.onrender.com").rstrip("/")
KNOWN_MATCH = 3943077   # Argentina 1-0 Colombia (Copa America)

_RUN = os.getenv("RUN_SMOKE") == "1"
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(not _RUN, reason="set RUN_SMOKE=1 to run production smoke tests"),
]


@pytest.fixture(scope="session")
def warm():
    """Wake the instance (cold starts can take ~60s) before timing other calls."""
    r = httpx.get(f"{PROD_URL}/health", timeout=90)
    assert r.status_code == 200, f"/health returned {r.status_code}"
    return PROD_URL


def test_health(warm):
    assert httpx.get(f"{warm}/health", timeout=30).json()["status"] == "ok"


def test_debug_healthy(warm):
    body = httpx.get(f"{warm}/debug", timeout=30).json()
    assert body["init_error"] is None
    assert body["mcon_ready"] is True
    assert body["events_event_set"] is True


def test_matches(warm):
    r = httpx.get(f"{warm}/matches", timeout=30)
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_shots_does_not_hang(warm):
    # The exact endpoint that hung the worker in prod. 30s timeout = a hang fails
    # fast rather than blocking for minutes.
    r = httpx.get(f"{warm}/matches/{KNOWN_MATCH}/shots", timeout=30)
    assert r.status_code == 200
    shots = r.json()
    assert len(shots) > 0
    assert all(0.0 <= s["xg_pred"] <= 1.0 for s in shots)


def test_timeline_does_not_hang(warm):
    r = httpx.get(f"{warm}/matches/{KNOWN_MATCH}/timeline", timeout=30)
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_worker_alive_after_load(warm):
    # If a prior request had hung the worker, this lightweight call would time out.
    assert httpx.get(f"{warm}/debug", timeout=30).json()["init_error"] is None
