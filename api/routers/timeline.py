import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from api.db import query, VALID_MATCH_IDS
from api.models import xg_model, xg_feature_cols, wp_model
from api.cache import cached
from api.routers.shots import BOOL_COLS, CAT_COLS, _predict_xg

router = APIRouter(prefix="/matches", tags=["timeline"])

WP_FEATURES = [
    "home_goals", "away_goals", "goal_diff",
    "home_xg", "away_xg", "xg_diff",
    "minute", "minutes_remaining", "period"
]


@router.get("/{match_id}/timeline")
@cached(lambda match_id: f"timeline:{match_id}")
def get_timeline(match_id: int):
    if VALID_MATCH_IDS and match_id not in VALID_MATCH_IDS:
        raise HTTPException(status_code=404, detail="Match not found")
    rows = query(f"""
        SELECT
            e.location_x, e.location_y,
            e.shot_body_part, e.shot_type, e.shot_technique,
            e.shot_first_time, e.shot_aerial_won, e.shot_one_on_one,
            e.shot_open_goal, e.under_pressure,
            e.shot_outcome, e.team_id,
            e.minute, e.second, e.period,
            m.home_team, m.away_team,
            m.home_team_id, m.away_team_id,
            m.home_score, m.away_score
        FROM events_r2 e
        JOIN matches_r2 m ON e.match_id = m.match_id
        WHERE e.type_name = 'Shot'
        AND e.match_id = {match_id}
        AND e.competition_id != 11
        ORDER BY e.period, e.minute, e.second
    """)

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df = _predict_xg(df)

    df["is_home"] = df["team_id"] == df["home_team_id"]

    df["home_xg"]   = df["xg_pred"].where(df["is_home"], 0).cumsum()
    df["away_xg"]   = df["xg_pred"].where(~df["is_home"], 0).cumsum()
    df["home_goals"] = (df["is_home"] & (df["shot_outcome"] == "Goal")).cumsum()
    df["away_goals"] = (~df["is_home"] & (df["shot_outcome"] == "Goal")).cumsum()

    df["goal_diff"]        = df["home_goals"] - df["away_goals"]
    df["xg_diff"]          = df["home_xg"] - df["away_xg"]
    df["minutes_remaining"] = (90 - df["minute"]).clip(lower=0)

    wp_preds = wp_model.predict_proba(df[WP_FEATURES])
    df["p_away_win"] = wp_preds[:, 0]
    df["p_draw"]     = wp_preds[:, 1]
    df["p_home_win"] = wp_preds[:, 2]

    return df[[
        "minute", "home_goals", "away_goals",
        "home_xg", "away_xg",
        "p_home_win", "p_draw", "p_away_win",
        "home_team", "away_team", "shot_outcome", "is_home"
    ]].to_dict(orient="records")
