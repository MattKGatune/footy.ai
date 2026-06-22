import os

import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.db import query

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

router = APIRouter(tags=["chat"])

SYSTEM_PROMPT = """You are a football analytics assistant. Translate the user's question into a single DuckDB SQL SELECT query and return a one-sentence explanation of what the query does.

Available views:

valid_events — one row per in-game event
  match_id, competition_id, period (1/2), minute, second
  type_name: 'Shot', 'Pass', 'Dribble', 'Carry', 'Foul Committed', 'Pressure', etc.
  player_name, player_id, team_name, team_id, position_name
  location_x (0–120), location_y (0–80)
  under_pressure (bool)

  Shot fields (type_name = 'Shot'):
    shot_outcome: 'Goal' | 'Saved' | 'Off T' | 'Blocked' | 'Wayward' | 'Post'
    shot_statsbomb_xg  — StatsBomb xG (0–1)
    shot_body_part: 'Right Foot' | 'Left Foot' | 'Head'
    shot_type: 'Open Play' | 'Free Kick' | 'Corner'
    shot_first_time, shot_one_on_one, shot_open_goal  — bool

  Pass fields (type_name = 'Pass'):
    pass_length, pass_angle, pass_outcome (null = complete, else 'Incomplete' etc.)
    pass_cross, pass_goal_assist, pass_shot_assist  — bool
    pass_recipient, pass_type ('Corner' | 'Free Kick' | 'Goal Kick' | 'Throw-in')

valid_matches — one row per match
  match_id, competition_id, competition_name, competition_stage
  match_date, match_week, season (e.g. '2015/16'), season_id
  home_team_id, home_team, away_team_id, away_team
  home_score, away_score
  stadium, referee
  home_manager_name, away_manager_name

IMPORTANT — competitions with event data in valid_events:
  Premier League, Ligue 1, Serie A, UEFA Europa League,
  Major League Soccer, UEFA Euro, Liga Profesional,
  La Liga, 1. Bundesliga, Champions League, FIFA World Cup,
  Copa America, Copa del Rey, African Cup of Nations,
  Indian Super League, FIFA U20 World Cup, North American League

Rules:
- Query ONLY valid_events and valid_matches. Never reference events_r2 or matches_r2.
- Output only a SELECT statement. Never use INSERT, UPDATE, DELETE, DROP, CREATE, or ALTER.
- Always end with LIMIT 200 unless the user asks for a COUNT/aggregate only.
- When a competition is specified, join valid_events e with valid_matches m ON e.match_id = m.match_id and filter with m.competition_name ILIKE '%...%'. Never rely on competition_id alone.
- ROUND all decimal columns to 2 decimal places using ROUND(col, 2).
- Use ILIKE with % wildcards for name searches. Truncate surnames to avoid accent mismatches (e.g. '%Mbapp%' not '%Mbappe%').
- Join on match_id when combining the two views."""


class ChatRequest(BaseModel):
    question: str


class SQLResult(BaseModel):
    sql: str
    explanation: str


@router.post("/chat")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    response = client.messages.parse(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": req.question}],
        output_format=SQLResult,
    )

    result: SQLResult = response.parsed_output

    sql = result.sql.strip()
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    try:
        rows = query(sql)
    except Exception as e:
        return {
            "sql": sql,
            "explanation": result.explanation,
            "error": str(e),
            "results": [],
            "row_count": 0,
        }

    return {
        "sql": sql,
        "explanation": result.explanation,
        "results": rows,
        "row_count": len(rows),
        "error": None,
    }
