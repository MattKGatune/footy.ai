from fastapi import APIRouter
from api.db import query
from api.cache import cached

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("")
@cached(lambda: "matches:all")
def list_matches():
    return query("""
        SELECT
            match_id,
            home_team,
            away_team,
            home_score,
            away_score,
            competition_id
        FROM matches_r2
        ORDER BY match_id DESC
    """)
