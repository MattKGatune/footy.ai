import os
import time
import threading
from dotenv import load_dotenv

load_dotenv(override=True)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket     = os.getenv("R2_BUCKET")

# Two connections so events init never blocks matches queries.
# _mcon: matches only — ready fast, used by /matches endpoint.
# _con:  matches + events — ready slow, used by shots/timeline/narrative/chat.
_mcon = None
_con  = None
_mlock = threading.Lock()
_lock  = threading.Lock()

_matches_ready = threading.Event()
_events_ready  = threading.Event()

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

_MATCHES_VIEW = f"""
    CREATE OR REPLACE VIEW matches_r2 AS
    SELECT * FROM read_parquet('s3://{bucket}/matches/**/*.parquet',
        hive_partitioning=true)
"""

_EVENTS_VIEW = f"""
    CREATE OR REPLACE VIEW events_r2 AS
    SELECT * FROM read_parquet('s3://{bucket}/events/**/*.parquet',
        hive_partitioning=true, union_by_name=true)
"""


def _init():
    global _mcon, _con
    try:
        import duckdb

        # Phase 1: fast matches-only connection
        _mcon = duckdb.connect()
        _mcon.execute("SET memory_limit='80MB'; SET threads=1;")
        _mcon.execute("INSTALL httpfs; LOAD httpfs;")
        _mcon.execute(_R2_SECRET)
        _mcon.execute(_MATCHES_VIEW)
        _matches_ready.set()
        print("Matches ready.")

        # Phase 2: main connection with both views (events scan is slow)
        _con = duckdb.connect()
        _con.execute("SET memory_limit='200MB'; SET threads=1;")
        _con.execute("LOAD httpfs;")  # already installed above
        _con.execute(_R2_SECRET)
        _con.execute(_MATCHES_VIEW)

        for attempt in range(5):
            try:
                _con.execute(_EVENTS_VIEW)
                _con.execute("CREATE OR REPLACE VIEW valid_events AS SELECT * FROM events_r2")
                _events_ready.set()
                print("Events ready.")
                break
            except Exception as e:
                print(f"Events view attempt {attempt + 1} failed: {e}")
                if attempt < 4:
                    time.sleep(5 * (attempt + 1))

    except Exception as e:
        print(f"DB initialization failed: {e}")
        _matches_ready.set()
        _events_ready.set()


threading.Thread(target=_init, daemon=True).start()


def query(sql: str, wait_for_events: bool = False) -> list[dict]:
    if wait_for_events:
        _events_ready.wait(timeout=300)
        with _lock:
            result = _con.execute(sql)
    else:
        _matches_ready.wait(timeout=60)
        with _mlock:
            result = _mcon.execute(sql)
    if result is None:
        return []
    df = result.df()
    if df is None:
        return []
    return df.to_dict(orient="records")
