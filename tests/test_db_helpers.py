"""Unit tests for the pure helpers in api.db (no network)."""
import api.db as db


def test_file_list_sql_quotes_and_joins():
    assert db._file_list_sql(["a.parquet"]) == "['a.parquet']"
    assert db._file_list_sql(["a", "b"]) == "['a', 'b']"


def test_file_list_sql_empty():
    assert db._file_list_sql([]) == "[]"


def test_parse_event_keys_maps_match_id_to_key():
    keys = [
        "events/competition_id=2/match_111.parquet",
        "events/competition_id=7/match_222.parquet",
    ]
    key_map, anchor = db._parse_event_keys(keys)
    assert key_map == {
        111: "events/competition_id=2/match_111.parquet",
        222: "events/competition_id=7/match_222.parquet",
    }
    # No World Cup (competition_id=43) file present -> no anchor.
    assert anchor is None


def test_parse_event_keys_picks_first_world_cup_anchor():
    keys = [
        "events/competition_id=2/match_111.parquet",
        "events/competition_id=43/match_999.parquet",   # first WC -> anchor
        "events/competition_id=43/match_1000.parquet",  # later WC ignored
    ]
    key_map, anchor = db._parse_event_keys(keys)
    assert anchor == "events/competition_id=43/match_999.parquet"
    assert key_map[999] == "events/competition_id=43/match_999.parquet"


def test_parse_event_keys_skips_keys_without_match_id():
    keys = ["events/competition_id=2/_SUCCESS", "events/random.txt"]
    key_map, anchor = db._parse_event_keys(keys)
    assert key_map == {}
    assert anchor is None


def test_get_event_expr_unions_match_with_anchor(monkeypatch):
    # Arrange the module state as if init had completed, with no real download.
    db._event_key_map = {111: "events/competition_id=2/match_111.parquet"}
    db._schema_anchor = "/local/anchor.parquet"
    db._events_ready.set()
    monkeypatch.setattr(db, "_download_key", lambda key: "/local/match_111.parquet")

    expr = db.get_event_expr(111)

    assert expr is not None
    assert "/local/match_111.parquet" in expr
    assert "/local/anchor.parquet" in expr
    assert "union_by_name=true" in expr
    assert "hive_partitioning=true" in expr


def test_get_event_expr_unknown_match_returns_none(monkeypatch):
    db._event_key_map = {}
    db._schema_anchor = "/local/anchor.parquet"
    db._events_ready.set()
    assert db.get_event_expr(424242) is None
