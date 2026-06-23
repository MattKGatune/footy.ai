import os
import re
import pathlib
import threading
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv(override=True)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket     = os.getenv("R2_BUCKET")

# Extension directory inside the project — persists between Render build and runtime.
_EXT_DIR = str(pathlib.Path(__file__).parent.parent / ".duckdb_ext")

# Two connections so the slow chat-events view never blocks fast queries.
# _mcon: matches view + per-match event queries (shots/timeline/narrative). Ready fast.
# _ccon: full events view for the /chat free-form SQL endpoint. Ready slow (~90s).
_mcon = None
_ccon = None
_mlock = threading.Lock()
_clock = threading.Lock()

_matches_ready = threading.Event()   # /matches dropdown
_events_ready  = threading.Event()   # shots / timeline / narrative
_chat_ready    = threading.Event()   # /chat

_init_error: str | None = None

# match_id -> s3 path, built from a boto3 listing (DuckDB's own S3 LIST hangs on Render).
_event_file_map: dict[int, str] = {}

# World Cup (competition_id=43) file used as a union anchor — it's the only
# competition with every shot column present. Unioning each match file with it
# makes columns missing from other competitions (shot_open_goal, shot_aerial_won,
# shot_one_on_one) resolve to NULL instead of raising a BinderException.
# DuckDB skips the anchor's row data via row-group stats, so it's nearly free.
_schema_anchor: str | None = None

VALID_MATCH_IDS: set[int] = set()

_R2_SECRET = f"""
    CREATE OR REPLACE SECRET r2_secret (
        TYPE S3,
        KEY_ID '{access_key}',
        SECRET '{secret_key}',
        ENDPOINT '{account_id}.r2.cloudflarestorage.com',
        REGION 'auto',
        URL_STYLE 'path'
    );
"""


def _list_r2_files(prefix: str) -> list[str]:
    """List R2 files via boto3 — avoids DuckDB's S3 LIST which hangs on Render."""
    import boto3
    s3 = boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto',
    )
    files: list[str] = []
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix):
        files += [f"s3://{bucket}/{o['Key']}" for o in page.get('Contents', [])]
    return files


def _file_list_sql(paths: list[str]) -> str:
    return "[" + ", ".join(f"'{p}'" for p in paths) + "]"


def get_event_expr(match_id: int) -> str | None:
    """read_parquet expression for one match's events, unioned with the WC anchor.

    Blocks until the event file map is ready. Returns None if the match has no
    event file (caller should treat as 404 / no data).
    """
    _events_ready.wait(timeout=60)
    path = _event_file_map.get(match_id)
    if not path or not _schema_anchor:
        return None
    fl = _file_list_sql([path, _schema_anchor])
    return f"read_parquet({fl}, hive_partitioning=true, union_by_name=true)"


def _make_con(memory_limit: str):
    import duckdb
    os.makedirs(_EXT_DIR, exist_ok=True)
    con = duckdb.connect(config={"extension_directory": _EXT_DIR})
    con.execute(f"SET memory_limit='{memory_limit}';")
    try:
        con.execute("LOAD httpfs;")
        print("httpfs loaded from cache.")
    except Exception:
        print("httpfs cache miss — installing...")
        con.execute("INSTALL httpfs; LOAD httpfs;")
        print("httpfs installed.")
    con.execute(_R2_SECRET)
    return con


def _init():
    global _mcon, _ccon, _event_file_map, _schema_anchor, _init_error
    try:
        # ── Phase 1: matches (~3–5 s) ──────────────────────────────────────
        print("Listing R2 match files via boto3...")
        match_files = _list_r2_files('matches/')
        print(f"Found {len(match_files)} match files.")

        _mcon = _make_con("200MB")
        _mcon.execute(
            f"CREATE OR REPLACE VIEW matches_r2 AS "
            f"SELECT * FROM read_parquet({_file_list_sql(match_files)}, hive_partitioning=true)"
        )
        _matches_ready.set()
        print("Matches ready.")

        # ── Phase 2: event file map (~5 s total from start) ────────────────
        print("Listing R2 event files via boto3...")
        event_files = _list_r2_files('events/')
        print(f"Found {len(event_files)} event files.")

        file_map: dict[int, str] = {}
        anchor: str | None = None
        for path in event_files:
            m = re.search(r'match_(\d+)', path)
            if m:
                mid = int(m.group(1))
                file_map[mid] = path
                if anchor is None and 'competition_id=43/' in path:
                    anchor = path

        _event_file_map = file_map
        _schema_anchor  = anchor
        _events_ready.set()
        print(f"Events map ready. {len(file_map)} matches. Anchor: {anchor}")

        # ── Phase 3: chat connection + full events view (~90 s locally) ────
        # Explicit file list (no R2 LIST) so it doesn't hang on Render. Built on
        # a separate connection so this slow scan never blocks _mcon queries.
        print("Building full events view for chat...")
        _ccon = _make_con("150MB")
        _ccon.execute(
            f"CREATE OR REPLACE VIEW valid_matches AS "
            f"SELECT * FROM read_parquet({_file_list_sql(match_files)}, hive_partitioning=true)"
        )
        _ccon.execute(
            f"CREATE OR REPLACE VIEW valid_events AS "
            f"SELECT * FROM read_parquet({_file_list_sql(event_files)}, "
            f"hive_partitioning=true, union_by_name=true)"
        )
        _chat_ready.set()
        print("Chat ready.")

    except Exception as e:
        _init_error = str(e)
        print(f"DB initialization failed: {e}")
        _matches_ready.set()
        _events_ready.set()
        _chat_ready.set()


threading.Thread(target=_init, daemon=True).start()


def query(sql: str, wait_for_events: bool = False) -> list[dict]:
    """Run a query on the fast connection (_mcon).

    wait_for_events=True is kept for callers that need the event file map ready
    (shots/timeline/narrative build their own read_parquet expr via get_event_expr).
    """
    if wait_for_events:
        if not _events_ready.wait(timeout=60):
            raise HTTPException(503, detail=f"Events not ready. Error: {_init_error}")
    else:
        if not _matches_ready.wait(timeout=120):
            raise HTTPException(503, detail=f"Matches not ready. Error: {_init_error}")

    if _mcon is None:
        raise HTTPException(503, detail=f"DB init failed: {_init_error}")

    with _mlock:
        try:
            result = _mcon.execute(sql)
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    if result is None:
        return []
    df = result.df()
    if df is None:
        return []
    return df.to_dict(orient="records")


def query_chat(sql: str) -> list[dict]:
    """Run free-form SQL for /chat on the full-events connection (_ccon)."""
    if not _chat_ready.wait(timeout=600):
        raise HTTPException(503, detail="Chat is still warming up, please try again shortly.")

    if _ccon is None:
        raise HTTPException(503, detail=f"Chat DB init failed: {_init_error}")

    with _clock:
        try:
            result = _ccon.execute(sql)
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    if result is None:
        return []
    df = result.df()
    if df is None:
        return []
    return df.to_dict(orient="records")
