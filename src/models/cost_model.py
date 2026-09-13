import os
import json
import joblib
import pandas as pd

# Load models and schema once at module level to avoid reloading per request
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

CLASSIFIER_PATH = os.path.join(MODELS_DIR, "cost_classifier.pkl")
REGRESSOR_PATH = os.path.join(MODELS_DIR, "cost_regressor.pkl")
SCHEMA_PATH = os.path.join(MODELS_DIR, "cost_feature_columns.json")

classifier = None
regressor = None
feature_schema = None

def _load_resources():
    global classifier, regressor, feature_schema
    if classifier is None and os.path.exists(CLASSIFIER_PATH):
        classifier = joblib.load(CLASSIFIER_PATH)
    if regressor is None and os.path.exists(REGRESSOR_PATH):
        regressor = joblib.load(REGRESSOR_PATH)
    if feature_schema is None and os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r") as f:
            feature_schema = json.load(f)

def predict_cost_risk(project_data: dict) -> dict:
    """
    Predicts the cost overrun risk and magnitude for a given project.
    
    Args:
        project_data (dict): A dictionary containing project features. 
            Must include at least the keys defined in the feature schema.
            
    Returns:
        dict: A dictionary containing risk assessment:
            {
                "risk_level": "HIGH" | "MEDIUM" | "LOW",
                "overrun_probability": float,
                "expected_overrun_percent": float,
                "is_cost_overrun": bool
            }
    """
    _load_resources()
    
    if not classifier or not regressor or not feature_schema:
        raise RuntimeError("Models or schema not found. Please train the model first.")
        
    # Convert input to DataFrame
    df = pd.DataFrame([project_data])
    
    # Ensure all expected columns are present, fill with None/NaN if missing
    all_features = feature_schema["numeric_features"] + feature_schema["categorical_features"]
    for col in all_features:
        if col not in df.columns:
            df[col] = None
            
    # Keep only the features in the exact order the pipeline expects, though the 
    # ColumnTransformer handles order based on column names.
    df = df[all_features]
    
    # Inference
    # 1. Classification (Probability of overrun)
    overrun_prob = classifier.predict_proba(df)[0, 1]
    is_overrun = bool(classifier.predict(df)[0])
    
    # 2. Regression (Expected overrun percentage)
    expected_overrun_pct = float(regressor.predict(df)[0])
    
    # Determine Risk Level based on probability
    if overrun_prob > 0.70:
        risk_level = "HIGH"
    elif overrun_prob > 0.40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
        
    return {
        "risk_level": risk_level,
        "overrun_probability": round(overrun_prob, 3),
        "expected_overrun_percent": round(expected_overrun_pct, 2),
        "is_cost_overrun": is_overrun
    }
