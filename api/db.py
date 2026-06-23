import os
import time
import threading
from dotenv import load_dotenv

load_dotenv(override=True)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket     = os.getenv("R2_BUCKET")

_con = None
_lock = threading.Lock()
_ready = threading.Event()
VALID_MATCH_IDS: set[int] = set()


def _init():
    global _con
    try:
        import duckdb
        _con = duckdb.connect()
        _con.execute("LOAD httpfs;")
        _con.execute(f"""
            CREATE OR REPLACE SECRET r2_secret (
                TYPE S3,
                KEY_ID '{access_key}',
                SECRET '{secret_key}',
                ENDPOINT '{account_id}.r2.cloudflarestorage.com',
                REGION 'auto',
                URL_STYLE 'path'
            );
        """)

        for attempt in range(5):
            try:
                _con.execute(f"""
                    CREATE OR REPLACE VIEW events_r2 AS
                    SELECT * FROM read_parquet('s3://{bucket}/events/**/*.parquet',
                        hive_partitioning=true, union_by_name=true)
                """)
                _con.execute(f"""
                    CREATE OR REPLACE VIEW matches_r2 AS
                    SELECT * FROM read_parquet('s3://{bucket}/matches/**/*.parquet',
                        hive_partitioning=true, union_by_name=true)
                """)
                break
            except Exception as e:
                print(f"View creation attempt {attempt + 1} failed: {e}")
                if attempt < 4:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise

        _con.execute("CREATE OR REPLACE VIEW valid_events AS SELECT * FROM events_r2")
        _con.execute("CREATE OR REPLACE VIEW valid_matches AS SELECT * FROM matches_r2")

        _ready.set()
        print("DB initialized.")

        with _lock:
            result = _con.execute(
                "SELECT DISTINCT match_id FROM events_r2 WHERE type_name = 'Shot'"
            )
            VALID_MATCH_IDS.update(set(result.df()["match_id"].tolist()))
        print(f"Found {len(VALID_MATCH_IDS)} matches with shot data.")

    except Exception as e:
        print(f"DB initialization failed: {e}")
        _ready.set()


threading.Thread(target=_init, daemon=True).start()


def query(sql: str) -> list[dict]:
    _ready.wait(timeout=180)
    with _lock:
        result = _con.execute(sql)
        if result is None:
            return []
        df = result.df()
        if df is None:
            return []
        return df.to_dict(orient="records")
