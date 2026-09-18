"""
cost_model.py - Member 3
============================================================
Inference script for the Cost Prediction ML Model.
Provides reusable functions for Member 5 and Member 6.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "cost_prediction_model.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "cost_feature_columns.json")

_model = None
_feature_info = None

def load_model():
    global _model, _feature_info
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)
        
        with open(FEATURES_PATH, "r") as f:
            _feature_info = json.load(f)

def predict_total_cost(project_data: dict) -> float:
    """
    Predicts the total expected cost at 100% completion for a given project.
    
    Args:
        project_data (dict): Dictionary containing all required features.
            Expected keys: 'original_cost', 'physical_progress', 'cumulative_expenditure', 
                           'progress_change_1m', 'expenditure_change_1m', 'expenditure_per_progress',
                           'state', 'agency', 'project_size_category'
                           
    Returns:
        float: Predicted total cost in Rs. Crore.
    """
    load_model()
    
    # Convert dict to DataFrame
    df = pd.DataFrame([project_data])
    
    # Ensure all expected columns are present
    all_features = _feature_info['num_features'] + _feature_info['cat_features']
    for col in all_features:
        if col not in df.columns:
            # Provide sensible defaults for missing features
            if col in _feature_info['num_features']:
                df[col] = 0.0
            else:
                df[col] = 'Unknown'
                
    # Reorder columns to match training
    df = df[all_features]
    
    # Predict
    pred = _model.predict(df)[0]
    
    # Cap prediction at cumulative_expenditure (cannot cost less than what we spent)
    if 'cumulative_expenditure' in project_data:
        pred = max(pred, project_data['cumulative_expenditure'])
        
    return pred

def predict_project_cost_risk(project_data: dict) -> dict:
    """
    Returns the predicted total cost and the predicted cost overrun percentage.
    Useful for Member 5 (Risk Engine) and Member 6 (Dashboard).
    """
    predicted_cost = predict_total_cost(project_data)
    
    original_cost = project_data.get('original_cost', 0)
    
    if original_cost > 0:
        overrun_percent = ((predicted_cost - original_cost) / original_cost) * 100
    else:
        overrun_percent = 0.0
        
    return {
        "predicted_total_cost": predicted_cost,
        "cost_overrun_percent": overrun_percent
    }
