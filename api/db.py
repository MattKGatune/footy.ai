import os
import time
import threading
import duckdb
from dotenv import load_dotenv

load_dotenv(override=True)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket     = os.getenv("R2_BUCKET")

con = duckdb.connect()
_lock = threading.Lock()
_ready = threading.Event()
VALID_MATCH_IDS: set[int] = set()


def _init():
    try:
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"""
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
                con.execute(f"""
                    CREATE OR REPLACE VIEW events_r2 AS
                    SELECT * FROM read_parquet('s3://{bucket}/events/**/*.parquet',
                        hive_partitioning=true, union_by_name=true)
                """)
                con.execute(f"""
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

        con.execute("CREATE OR REPLACE VIEW valid_events AS SELECT * FROM events_r2")
        con.execute("CREATE OR REPLACE VIEW valid_matches AS SELECT * FROM matches_r2")

        _ready.set()
        print("DB initialized.")

        with _lock:
            result = con.execute("""
                SELECT DISTINCT match_id FROM events_r2 WHERE type_name = 'Shot'
            """)
            VALID_MATCH_IDS.update(set(result.df()["match_id"].tolist()))
        print(f"Found {len(VALID_MATCH_IDS)} matches with shot data.")

    except Exception as e:
        print(f"DB initialization failed: {e}")
        _ready.set()  # unblock queries so they fail with a clear error rather than hanging


threading.Thread(target=_init, daemon=True).start()


def query(sql: str) -> list[dict]:
    _ready.wait(timeout=180)
    with _lock:
        result = con.execute(sql)
        if result is None:
            return []
        df = result.df()
        if df is None:
            return []
        return df.to_dict(orient="records")
