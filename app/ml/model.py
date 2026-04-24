import os

import joblib
import pandas as pd

from app.config import ML_MODEL

_model = None


def load_model():
    global _model
    if not os.path.exists(ML_MODEL):
        raise FileNotFoundError(
            f"Model file not found at '{ML_MODEL}'. "
            "Drop the joblib file there and restart the server."
        )
    _model = joblib.load(ML_MODEL)


def is_loaded() -> bool:
    return (_model is not None)


def predict(features: dict) -> str:
    if _model is None:
        raise RuntimeError("Model is not loaded.")
    df = pd.DataFrame([features])
    try:
        result = _model.predict(df)
    except ValueError as e:
        raise RuntimeError(
            f"Feature mismatch between extract_features() and the trained model: {e}"
        ) from e
    return str(result[0])
