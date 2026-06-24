# footy.ai

[![CI](https://github.com/MattKGatune/footy.ai/actions/workflows/ci.yml/badge.svg)](https://github.com/MattKGatune/footy.ai/actions/workflows/ci.yml)
[![Smoke (prod)](https://github.com/MattKGatune/footy.ai/actions/workflows/smoke.yml/badge.svg)](https://github.com/MattKGatune/footy.ai/actions/workflows/smoke.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

Football analytics on StatsBomb open data — an **expected-goals (xG)** model, a
**live win-probability timeline**, and **AI-generated match narratives**.

**Live:** https://footy-ai-u99r.onrender.com

## Features

- **xG shot map** — a trained XGBoost model scores every shot from its location,
  body part, play pattern, and context; rendered on a pitch.
- **Win-probability timeline** — a model converts the running score and cumulative
  xG into live home/draw/away probabilities across the match.
- **Match narratives** — Claude turns the computed shot/xG stats into a concise
  post-match report.
- **Natural-language query** — text-to-SQL chat over the event data *(in progress)*.

## Architecture

| Layer | Tech |
|-------|------|
| API | FastAPI |
| Analytics engine | DuckDB querying Parquet |
| Data store | Cloudflare R2 (S3-compatible), accessed via boto3 |
| Models | XGBoost / scikit-learn (xG, win-probability) |
| LLM | Anthropic Claude |
| Frontend | React |
| Hosting | Render |

Event/match data lives as Parquet in R2. The API fetches the files it needs with
boto3 and queries them locally with DuckDB — deliberately **not** reading `s3://`
through DuckDB's httpfs, which is unreliable on the host network (see the test
suite for the regression that motivated this).

## Testing & CI

A three-layer test suite, wired into GitHub Actions:

| Layer | What it covers | Command |
|-------|----------------|---------|
| **Unit** | pure logic (xG math, data-path helpers); no network | `pytest -m "not integration and not smoke"` |
| **Integration** | real endpoints against real R2, LLM mocked | `pytest -m integration` |
| **Smoke** | the live production deployment | `RUN_SMOKE=1 pytest -m smoke` |

- **CI** runs unit + integration on every push/PR.
- **Smoke** runs on a schedule (and on demand) against production.

```bash
pip install -r requirements-dev.txt
pytest -m "not integration and not smoke"   # fast, offline
```

## Local development

```bash
pip install -r requirements.txt
# .env with R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
# R2_BUCKET, ANTHROPIC_API_KEY
uvicorn api.main:app --reload
```
