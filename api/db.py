import os
import re
import pathlib
import tempfile
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

# Local cache for parquet files downloaded from R2 via boto3.
#
# Why download instead of letting DuckDB read s3:// directly: DuckDB's httpfs
# extension is unreliable on Render's network. Its S3 LIST hangs (~114s), and
# its range-read pattern for large event files also hangs indefinitely — a hung
# read holds _mlock and exhausts the threadpool, poisoning the whole worker.
# boto3, by contrast, lists and GETs reliably on Render. So we use boto3 for ALL
# network I/O and point DuckDB only at local files (no httpfs in the hot path).
# Files are stored mirroring their S3 key so hive_partitioning still recovers
# competition_id from the competition_id=XX/ path segment.
_CACHE_DIR = pathlib.Path(tempfile.gettempdir()) / "footy_cache"

_mcon = None
_mlock = threading.Lock()
_dl_lock = threading.Lock()          # serializes on-demand downloads

_matches_ready = threading.Event()   # /matches dropdown
_events_ready  = threading.Event()   # shots / timeline / narrative (file map + anchor ready)

_init_error: str | None = None

# match_id -> S3 key (e.g. "events/competition_id=43/match_123.parquet")
_event_key_map: dict[int, str] = {}

# Local path to the World Cup (competition_id=43) anchor file. It's the only
# competition with every shot column present. Unioning each match's events with
# it makes columns missing from other competitions (shot_open_goal,
# shot_aerial_won, shot_one_on_one) resolve to NULL instead of raising a
# BinderException. DuckDB skips the anchor's row data via row-group stats.
_schema_anchor: str | None = None

VALID_MATCH_IDS: set[int] = set()


def _s3_client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto',
        # Bounded timeouts so a slow/failed transfer raises instead of hanging
        # the worker (the failure mode that poisoned the threadpool before).
        config=Config(connect_timeout=10, read_timeout=60,
                      retries={'max_attempts': 3, 'mode': 'standard'}),
    )


def _list_keys(prefix: str) -> list[str]:
    """List object keys under a prefix via boto3 (reliable on Render)."""
    s3 = _s3_client()
    keys: list[str] = []
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix):
        keys += [o['Key'] for o in page.get('Contents', [])]
    return keys


def _download_key(key: str) -> str:
    """Download an R2 object to the local cache (mirroring its key) and return
    the local path. No-op if already cached. Atomic via temp file + rename."""
    dest = _CACHE_DIR / key
    if dest.exists():
        return str(dest)
    with _dl_lock:
        if dest.exists():                       # re-check inside the lock
            return str(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        _s3_client().download_file(bucket, key, str(tmp))
        os.replace(tmp, dest)
    return str(dest)


def _file_list_sql(paths: list[str]) -> str:
    return "[" + ", ".join(f"'{p}'" for p in paths) + "]"


def _parse_event_keys(keys: list[str]) -> tuple[dict[int, str], str | None]:
    """Map match_id -> S3 key and pick the first competition_id=43 key as the
    schema anchor. Pure (no I/O) so it can be unit-tested."""
    key_map: dict[int, str] = {}
    anchor_key: str | None = None
    for key in keys:
        m = re.search(r'match_(\d+)', key)
        if m:
            key_map[int(m.group(1))] = key
            if anchor_key is None and 'competition_id=43/' in key:
                anchor_key = key
    return key_map, anchor_key


def get_event_expr(match_id: int) -> str | None:
    """read_parquet expression over LOCAL files for one match's events, unioned
    with the WC anchor. Downloads the match's event file on demand.

    Blocks until the event map/anchor are ready. Returns None if the match has
    no event file (caller should treat as 404 / no data).
    """
    _events_ready.wait(timeout=60)
    key = _event_key_map.get(match_id)
    if not key or not _schema_anchor:
        return None
    try:
        local_match = _download_key(key)
    except Exception as e:
        raise HTTPException(503, detail=f"Failed to fetch event data: {e}")
    fl = _file_list_sql([local_match, _schema_anchor])
    return f"read_parquet({fl}, hive_partitioning=true, union_by_name=true)"


def _make_con(memory_limit: str):
    import duckdb
    os.makedirs(_EXT_DIR, exist_ok=True)
    con = duckdb.connect(config={"extension_directory": _EXT_DIR})
    con.execute(f"SET memory_limit='{memory_limit}';")
    return con


def _init():
    global _mcon, _event_key_map, _schema_anchor, _init_error
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # ── Phase 1: matches ───────────────────────────────────────────────
        print("Listing R2 match files via boto3...")
        match_keys = _list_keys('matches/')
        print(f"Found {len(match_keys)} match files. Downloading...")
        local_match_paths = [_download_key(k) for k in match_keys]

        _mcon = _make_con("250MB")
        _mcon.execute(
            f"CREATE OR REPLACE VIEW matches_r2 AS "
            f"SELECT * FROM read_parquet({_file_list_sql(local_match_paths)}, hive_partitioning=true)"
        )
        _matches_ready.set()
        print("Matches ready.")

        # ── Phase 2: event key map + anchor ────────────────────────────────
        print("Listing R2 event files via boto3...")
        event_keys = _list_keys('events/')
        print(f"Found {len(event_keys)} event files.")

        key_map, anchor_key = _parse_event_keys(event_keys)

        _event_key_map = key_map
        if anchor_key:
            _schema_anchor = _download_key(anchor_key)   # fetch anchor once, up front
        _events_ready.set()
        print(f"Events map ready. {len(key_map)} matches. Anchor: {_schema_anchor}")

    except Exception as e:
        _init_error = str(e)
        print(f"DB initialization failed: {e}")
        _matches_ready.set()
        _events_ready.set()


# Skip the background network init when running unit tests (FOOTY_SKIP_INIT=1).
if os.getenv("FOOTY_SKIP_INIT") != "1":
    threading.Thread(target=_init, daemon=True).start()


def query(sql: str, wait_for_events: bool = False) -> list[dict]:
    """Run a query on the connection (_mcon).

    wait_for_events=True is for callers that build their own read_parquet expr
    via get_event_expr (shots/timeline/narrative); it waits for the event map.
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
    """Free-form SQL for /chat.

    Disabled on this deployment: chat needs every event file at once, which would
    mean DuckDB reading 2651 files over httpfs (hangs on Render) or downloading
    the entire dataset to disk. Returns 503 rather than hanging the worker.
    Tracked for a follow-up (e.g. a prebuilt aggregate table).
    """
    raise HTTPException(
        503,
        detail="The chat feature is temporarily unavailable on this deployment.",
    )
