import os
import threading
import duckdb
from dotenv import load_dotenv

load_dotenv(override=True)

con = duckdb.connect()

con.execute("INSTALL httpfs; LOAD httpfs;")

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket     = os.getenv("R2_BUCKET")

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

con.execute("""
    CREATE OR REPLACE VIEW valid_events AS
    SELECT * FROM events_r2
""")

con.execute("""
    CREATE OR REPLACE VIEW valid_matches AS
    SELECT * FROM matches_r2
""")


_lock = threading.Lock()


def query(sql: str) -> list[dict]:
    with _lock:
        result = con.execute(sql)
        if result is None:
            return []
        df = result.df()
        if df is None:
            return []
        return df.to_dict(orient="records")


def _build_valid_match_ids() -> set[int]:
    print("Building valid match ID index from R2...")
    result = con.execute("""
        SELECT DISTINCT match_id
        FROM events_r2
        WHERE type_name = 'Shot'
    """)
    ids = set(result.df()["match_id"].tolist())
    print(f"Found {len(ids)} matches with shot data.")
    return ids


VALID_MATCH_IDS: set[int] = _build_valid_match_ids()
