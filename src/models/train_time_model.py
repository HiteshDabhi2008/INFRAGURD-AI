"""
train_time_model.py - Member 4
============================================================
Trains ML models to predict target duration (months) of projects.
Evaluates Ridge, Random Forest, and XGBoost regressors.
Selects the best model based on MAE and saves it.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "time_ml_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "member4")
MODEL_PATH = os.path.join(MODELS_DIR, "time_prediction_model.pkl")
FEATURES_PATH = os.path.join(MODELS_DIR, "time_feature_columns.json")
PREDICTIONS_PATH = os.path.join(OUTPUT_DIR, "time_predictions.csv")

def train_and_evaluate():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # We want to predict target_duration_months
    # Features cannot include target_duration_months, original_completion_date, revised_completion_date
    
    num_features = [
        'physical_progress', 'project_age_months', 'original_duration_months',
        'remaining_original_duration_months', 'progress_change_1m'
    ]
    
    cat_features = ['agency', 'state']
    
    target = 'target_duration_months'
    
    X = df[num_features + cat_features]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
        ])
    
    models = {
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42)
    }
    
    if XGB_AVAILABLE:
        models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
        
    results = []
    best_model = None
    best_mae = float('inf')
    best_model_name = ""
    best_pipeline = None
    
    for name, model in models.items():
        pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('regressor', model)])
        
        # Train
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred = pipeline.predict(X_test)
        
        # Ensure predictions aren't lower than the project age
        # A project cannot be finished faster than the time already spent
        test_age = X_test['project_age_months'].values
        y_pred = np.maximum(y_pred, test_age)
        
        # Evaluate
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        results.append({
            "Model": name,
            "MAE (Months)": round(mae, 2),
            "RMSE (Months)": round(rmse, 2),
            "R2": round(r2, 4)
        })
        
        if mae < best_mae:
            best_mae = mae
            best_model_name = name
            best_pipeline = pipeline
            
    results_df = pd.DataFrame(results)
    print("\nModel Evaluation Results:")
    print(results_df.to_string())
    
    print(f"\nBest model selected: {best_model_name}")
    
    # Save the best model
    joblib.dump(best_pipeline, MODEL_PATH)
    
    # Save feature metadata
    with open(FEATURES_PATH, 'w') as f:
        json.dump({
            "num_features": num_features,
            "cat_features": cat_features
        }, f)
        
    # Generate predictions for the whole dataset for Member 5
    print("\nGenerating final predictions...")
    all_preds = best_pipeline.predict(X)
    
    # Constraints: Duration >= Project Age
    all_preds = np.maximum(all_preds, df['project_age_months'])
    
    out_df = df[['project_code', 'report_date', 'original_duration_months', 'target_duration_months', 'project_age_months']].copy()
    out_df['predicted_duration_months'] = all_preds
    
    # Calculate time overrun
    out_df['time_overrun_months'] = out_df['predicted_duration_months'] - out_df['original_duration_months']
    out_df['time_overrun_percent'] = (out_df['time_overrun_months'] / out_df['original_duration_months']) * 100
    
    # Cap lower bound of overrun at 0 for simplicity if predicted duration is less than original
    out_df['time_overrun_months'] = out_df['time_overrun_months'].clip(lower=0)
    out_df['time_overrun_percent'] = out_df['time_overrun_percent'].clip(lower=0)
    
    out_df.to_csv(PREDICTIONS_PATH, index=False)
    print(f"Saved final predictions to {PREDICTIONS_PATH}")

if __name__ == "__main__":
    train_and_evaluate()
