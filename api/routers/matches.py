from fastapi import APIRouter
from api.db import query, VALID_MATCH_IDS
from api.cache import cached

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("")
@cached(lambda: "matches:all")
def list_matches():
    rows = query("""
        SELECT
            match_id,
            home_team,
            away_team,
            home_score,
            away_score,
            competition_id,
            competition_name,
            match_date
        FROM matches_r2
        ORDER BY match_id DESC
    """)
    return [r for r in rows if r["match_id"] in VALID_MATCH_IDS]
