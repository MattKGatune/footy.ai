"""Unit tests for the xG prediction math (api.routers.shots._predict_xg).

Uses the real trained model (loaded from local .pkl, no network) on synthetic
shots so we assert invariants rather than brittle exact probabilities.
"""
import numpy as np
import pandas as pd
import pytest

from api.routers.shots import _predict_xg, BOOL_COLS, CAT_COLS


def _synthetic_shots(n=3):
    """A minimal shots frame with every column _predict_xg reads."""
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "location_x": rng.uniform(80, 120, n),
        "location_y": rng.uniform(20, 60, n),
        "shot_body_part": ["Right Foot", "Left Foot", "Head"][:n] or ["Right Foot"],
        "shot_type": ["Open Play"] * n,
        "shot_technique": ["Normal"] * n,
        "shot_first_time": [True, False, True][:n] or [False],
        "shot_aerial_won": [False] * n,
        "shot_one_on_one": [False] * n,
        "shot_open_goal": [False] * n,
        "under_pressure": [True, False, False][:n] or [False],
    })
    return df


def test_predict_xg_adds_probability_column():
    df = _predict_xg(_synthetic_shots())
    assert "xg_pred" in df.columns
    assert len(df) == 3


def test_predict_xg_values_are_valid_probabilities():
    df = _predict_xg(_synthetic_shots())
    assert df["xg_pred"].between(0.0, 1.0).all()


def test_predict_xg_handles_missing_bool_columns_as_nan():
    # This is the schema-inconsistency case that caused the original prod bugs:
    # competitions missing shot_open_goal / shot_one_on_one come back as NaN
    # via the union anchor. _predict_xg must treat NaN bools as False, not crash.
    df = _synthetic_shots()
    df["shot_open_goal"] = np.nan
    df["shot_one_on_one"] = np.nan
    out = _predict_xg(df)
    assert out["xg_pred"].between(0.0, 1.0).all()


def test_predict_xg_closer_shot_has_higher_xg():
    # A shot from the penalty spot should out-rank one from distance.
    df = _synthetic_shots(n=1).copy()
    df.loc[0, ["location_x", "location_y"]] = [108, 40]   # ~12y, central
    near = _predict_xg(df.copy())["xg_pred"].iloc[0]

    df.loc[0, ["location_x", "location_y"]] = [85, 20]    # far + wide
    far = _predict_xg(df.copy())["xg_pred"].iloc[0]

    assert near > far
