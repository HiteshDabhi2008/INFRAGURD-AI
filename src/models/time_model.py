"""
Member 4: Time Overrun Prediction — Reusable Inference Module
=============================================================
Provides ``predict_time_risk(project_data)`` for use by Member 5
(Risk Engine) and Member 6 (Dashboard).

Usage:
    from src.models.time_model import predict_time_risk
    result = predict_time_risk({...})
"""

import os
import json
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

CLASSIFIER_PATH = os.path.join(MODELS_DIR, "time_classifier.pkl")
REGRESSOR_PATH = os.path.join(MODELS_DIR, "time_regressor.pkl")
SCHEMA_PATH = os.path.join(MODELS_DIR, "time_feature_columns.json")

# Module-level caches (loaded once)
_classifier = None
_regressor = None
_schema = None


def _load_resources():
    global _classifier, _regressor, _schema
    if _classifier is None and os.path.exists(CLASSIFIER_PATH):
        _classifier = joblib.load(CLASSIFIER_PATH)
    if _regressor is None and os.path.exists(REGRESSOR_PATH):
        _regressor = joblib.load(REGRESSOR_PATH)
    if _schema is None and os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r") as f:
            _schema = json.load(f)


def predict_time_risk(project_data: dict) -> dict:
    """
    Predict time-overrun risk for a single project.

    Args:
        project_data: dict with at least the keys listed in
            ``models/time_feature_columns.json``.

    Returns:
        dict with keys:
            risk_level           : "HIGH" | "MEDIUM" | "LOW"
            overrun_probability  : float  (0-1)
            expected_overrun_months : float
            is_time_overrun      : bool

    Risk thresholds (internal convention, NOT official MoSPI thresholds):
        > 0.70  ->  HIGH
        0.40-0.70  ->  MEDIUM
        < 0.40  ->  LOW
    """
    _load_resources()

    if not _classifier or not _schema:
        raise RuntimeError(
            "Time models or schema not found. Run train_time_model.py first."
        )

    all_features = _schema["numeric_features"] + _schema["categorical_features"]

    df = pd.DataFrame([project_data])
    for col in all_features:
        if col not in df.columns:
            df[col] = None
    df = df[all_features]

    # Classification
    overrun_prob = float(_classifier.predict_proba(df)[0, 1])
    is_overrun = bool(_classifier.predict(df)[0])

    # Regression (optional — may not exist if only classification was trained)
    if _regressor is not None:
        expected_months = float(_regressor.predict(df)[0])
    else:
        expected_months = None

    # Risk level
    if overrun_prob > 0.70:
        risk_level = "HIGH"
    elif overrun_prob > 0.40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "overrun_probability": round(overrun_prob, 3),
        "expected_overrun_months": round(expected_months, 1) if expected_months is not None else None,
        "is_time_overrun": is_overrun,
    }
