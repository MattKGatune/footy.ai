import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from api.db import query, VALID_MATCH_IDS
from api.models import xg_model, xg_feature_cols
from api.cache import cached

router = APIRouter(prefix="/matches", tags=["shots"])

BOOL_COLS = [
    "shot_first_time", "shot_aerial_won", "shot_one_on_one",
    "shot_open_goal", "under_pressure"
]
CAT_COLS = ["shot_body_part", "shot_type", "shot_technique"]


def _predict_xg(shots: pd.DataFrame) -> pd.DataFrame:
    df = shots.copy()
    for col in BOOL_COLS:
        df[col] = df[col].fillna(False).astype(int)

    df = pd.get_dummies(df, columns=CAT_COLS)
    df = df.reindex(columns=xg_feature_cols, fill_value=0)

    a = np.array([120 - shots["location_x"], 36 - shots["location_y"]]).T
    b = np.array([120 - shots["location_x"], 44 - shots["location_y"]]).T
    dot   = (a * b).sum(axis=1)
    cross = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]

    df["distance"] = np.sqrt((shots["location_x"] - 120)**2 + (shots["location_y"] - 40)**2)
    df["angle"]    = np.arctan2(np.abs(cross), dot)

    shots["xg_pred"] = xg_model.predict_proba(df[xg_feature_cols])[:, 1]
    return shots


@router.get("/{match_id}/shots")
@cached(lambda match_id: f"shots:{match_id}")
def get_shots(match_id: int):
    if VALID_MATCH_IDS and match_id not in VALID_MATCH_IDS:
        raise HTTPException(status_code=404, detail="Match not found")
    rows = query(f"""
        SELECT
            e.location_x, e.location_y,
            e.shot_body_part, e.shot_type, e.shot_technique,
            e.shot_first_time, e.shot_aerial_won, e.shot_one_on_one,
            e.shot_open_goal, e.under_pressure,
            e.shot_outcome, e.shot_statsbomb_xg,
            e.player_name, e.team_name, e.minute,
            (e.team_id = m.home_team_id) AS is_home
        FROM events_r2 e
        JOIN matches_r2 m ON e.match_id = m.match_id
        WHERE e.type_name = 'Shot'
        AND e.shot_type != 'Penalty'
        AND e.match_id = {match_id}
        AND e.competition_id != 11
    """)

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df = _predict_xg(df)
    return df.to_dict(orient="records")
