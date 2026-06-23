import os

import anthropic
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.cache import cached
from api.db import VALID_MATCH_IDS, query
from api.routers.shots import _predict_xg

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

router = APIRouter(prefix="/matches", tags=["narrative"])


class MatchNarrative(BaseModel):
    summary: str
    key_moments: list[str]
    tactical_note: str


@router.get("/{match_id}/narrative")
@cached(lambda match_id: f"narrative:{match_id}")
def get_narrative(match_id: int):
    if match_id not in VALID_MATCH_IDS:
        raise HTTPException(status_code=404, detail="Match not found")

    rows = query(f"""
        SELECT
            e.location_x, e.location_y,
            e.shot_body_part, e.shot_type, e.shot_technique,
            e.shot_first_time, e.shot_aerial_won, e.shot_one_on_one,
            e.shot_open_goal, e.under_pressure,
            e.shot_outcome, e.player_name, e.minute,
            (e.team_id = m.home_team_id) AS is_home,
            m.home_team, m.away_team,
            m.home_score, m.away_score,
            m.competition_name, m.match_date
        FROM events_r2 e
        JOIN matches_r2 m ON e.match_id = m.match_id
        WHERE e.type_name = 'Shot'
        AND e.shot_type != 'Penalty'
        AND e.match_id = {match_id}
        AND e.competition_id != 11
        ORDER BY e.minute
    """, wait_for_events=True)

    if not rows:
        raise HTTPException(status_code=404, detail="No shot data for this match")

    df = pd.DataFrame(rows)
    df = _predict_xg(df)

    meta = rows[0]
    home_team = meta["home_team"]
    away_team = meta["away_team"]
    home_score = int(meta["home_score"])
    away_score = int(meta["away_score"])
    competition = meta["competition_name"]
    match_date = str(meta["match_date"])

    home = df[df["is_home"]]
    away = df[~df["is_home"]]

    home_shots = len(home)
    away_shots = len(away)
    home_on_target = int((home["shot_outcome"].isin(["Goal", "Saved"])).sum())
    away_on_target = int((away["shot_outcome"].isin(["Goal", "Saved"])).sum())
    home_xg = round(float(home["xg_pred"].sum()), 2)
    away_xg = round(float(away["xg_pred"].sum()), 2)

    goals = df[df["shot_outcome"] == "Goal"][
        ["minute", "player_name", "xg_pred", "is_home"]
    ].to_dict(orient="records")

    big_chances = df[(df["xg_pred"] > 0.30) & (df["shot_outcome"] != "Goal")][
        ["minute", "player_name", "xg_pred", "is_home"]
    ].to_dict(orient="records")

    goals_text = "\n".join(
        f"  - min {g['minute']}: {g['player_name']} ({'home' if g['is_home'] else 'away'})"
        f" xG={g['xg_pred']:.2f} — GOAL"
        for g in goals
    ) or "  (no open-play goals)"

    missed_text = "\n".join(
        f"  - min {b['minute']}: {b['player_name']} ({'home' if b['is_home'] else 'away'})"
        f" xG={b['xg_pred']:.2f} — missed"
        for b in big_chances
    ) or "  (no big open-play chances missed)"

    prompt = f"""You are a football analyst writing a concise post-match report.

Match: {home_team} {home_score}–{away_score} {away_team}
Competition: {competition}
Date: {match_date}

Open-play shot statistics (penalties excluded):
  {home_team}: {home_shots} shots, {home_on_target} on target, xG {home_xg}
  {away_team}: {away_shots} shots, {away_on_target} on target, xG {away_xg}

Goals:
{goals_text}

High-xG chances that didn't score (xG > 0.30):
{missed_text}

Write a match analysis with:
- summary: 2–3 sentences on the result and whether the xG line reflects what happened
- key_moments: 4–6 bullet strings covering goals and notable misses in chronological order
- tactical_note: 1–2 sentences on which team dominated and how

Use actual stats and player names. Keep the tone analytical, not sensationalist."""

    response = client.messages.parse(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
        output_format=MatchNarrative,
    )

    narrative: MatchNarrative = response.parsed_output

    return {
        "match": {
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "competition": competition,
            "date": match_date,
        },
        "stats": {
            "home_shots": home_shots,
            "away_shots": away_shots,
            "home_on_target": home_on_target,
            "away_on_target": away_on_target,
            "home_xg": home_xg,
            "away_xg": away_xg,
        },
        "narrative": narrative.model_dump(),
    }
