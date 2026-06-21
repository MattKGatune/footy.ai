import joblib
from pathlib import Path

ROOT = Path(__file__).parent.parent

xg_model       = joblib.load(ROOT / "xg_model.pkl")
xg_feature_cols = joblib.load(ROOT / "xg_feature_cols.pkl")
wp_model       = joblib.load(ROOT / "wp_model.pkl")
