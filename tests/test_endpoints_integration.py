"""Layer 2: integration / contract tests.

These exercise the real FastAPI endpoints against the real R2 data (the path
that broke in production), with the Anthropic LLM mocked so /narrative and /chat
are deterministic and free. Marked `integration` so the fast loop can skip them:

    pytest -m "not integration"

They skip automatically if R2 credentials aren't configured.
"""
import os
import types

import pytest

pytestmark = pytest.mark.integration

# Known historical matches (facts that don't change) used as golden signals.
COPA = 3943077        # Argentina 1-0 Colombia (Copa America)
PL   = 3754351        # Liverpool 1-2 Crystal Palace (Premier League)
BOGUS = 1             # no such match


def _have_creds() -> bool:
    return all(os.getenv(k) for k in
               ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"))


@pytest.fixture(scope="session")
def client():
    if not _have_creds():
        pytest.skip("R2 credentials not configured")
    import api.db as db
    db._init()                       # synchronous; the background thread is guarded off
    if db._init_error:
        pytest.skip(f"R2 init failed: {db._init_error}")
    from starlette.testclient import TestClient
    from api.main import app
    with TestClient(app) as c:
        yield c


# ── health / debug ──────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_debug_initialised_cleanly(client):
    body = client.get("/debug").json()
    assert body["init_error"] is None
    assert body["mcon_ready"] is True
    assert body["events_event_set"] is True
    assert body["event_file_count"] > 0


# ── /matches ────────────────────────────────────────────────────────────────

def test_matches_returns_rows_with_contract(client):
    rows = client.get("/matches").json()
    assert isinstance(rows, list) and len(rows) > 0
    required = {"match_id", "home_team", "away_team", "home_score",
                "away_score", "competition_id", "competition_name", "match_date"}
    assert required <= set(rows[0])


def test_matches_contains_known_match(client):
    rows = client.get("/matches").json()
    by_id = {m["match_id"]: m for m in rows}
    assert COPA in by_id
    m = by_id[COPA]
    assert m["home_team"] == "Argentina"
    assert m["away_team"] == "Colombia"
    assert (m["home_score"], m["away_score"]) == (1, 0)


# ── /shots (the endpoint that hung prod; exercises the union-anchor path) ─────

@pytest.mark.parametrize("match_id", [COPA, PL])
def test_shots_contract(client, match_id):
    r = client.get(f"/matches/{match_id}/shots")
    assert r.status_code == 200
    shots = r.json()
    assert len(shots) > 0
    required = {"location_x", "location_y", "shot_outcome", "player_name",
                "team_name", "is_home", "xg_pred"}
    assert required <= set(shots[0])
    assert all(0.0 <= s["xg_pred"] <= 1.0 for s in shots)
    assert all(isinstance(s["is_home"], bool) for s in shots)


def test_shots_bogus_match_is_404(client):
    assert client.get(f"/matches/{BOGUS}/shots").status_code == 404


# ── /timeline ───────────────────────────────────────────────────────────────

def test_timeline_probabilities_sum_to_one(client):
    r = client.get(f"/matches/{COPA}/timeline")
    assert r.status_code == 200
    pts = r.json()
    assert len(pts) > 0
    for p in pts:
        total = p["p_home_win"] + p["p_draw"] + p["p_away_win"]
        assert total == pytest.approx(1.0, abs=1e-6)


# ── /narrative (LLM mocked) ─────────────────────────────────────────────────

def test_narrative_contract(client, monkeypatch):
    import api.routers.narrative as narr
    fake = types.SimpleNamespace(parsed_output=narr.MatchNarrative(
        summary="s", key_moments=["a", "b"], tactical_note="t"))
    monkeypatch.setattr(narr.client.messages, "parse", lambda **kw: fake)

    r = client.get(f"/matches/{COPA}/narrative")
    assert r.status_code == 200
    body = r.json()
    assert {"match", "stats", "narrative"} <= set(body)
    assert body["match"]["home_team"] == "Argentina"
    assert body["stats"]["home_xg"] >= 0
    assert body["narrative"]["summary"] == "s"


# ── /chat (LLM mocked; currently a graceful 503 in-body) ─────────────────────

def test_chat_degrades_gracefully(client, monkeypatch):
    import api.routers.chat as chatmod
    fake = types.SimpleNamespace(parsed_output=chatmod.SQLResult(
        sql="SELECT 1", explanation="x"))
    monkeypatch.setattr(chatmod.client.messages, "parse", lambda **kw: fake)

    r = client.post("/chat", json={"question": "anything"})
    assert r.status_code == 200
    assert "unavailable" in (r.json().get("error") or "")
