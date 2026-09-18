"""
train_cost_model.py - Member 3
============================================================
Trains ML models to predict total project cost using historical PAIMANA data.
Models evaluated: Baseline (Linear Regression), Random Forest, XGBoost.
"""

import os
import pandas as pd
import numpy as np
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "cost_ml_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "member3")

def evaluate_model(name, y_true, y_pred, baseline_cost=None):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    # Relative error: (y_pred - y_true) / y_true
    # Filter zeros to avoid division by zero
    valid_mask = y_true > 0
    rel_error = np.mean(np.abs(y_pred[valid_mask] - y_true[valid_mask]) / y_true[valid_mask]) * 100
    
    metrics = {
        'Model': name,
        'MAE (Cr)': round(mae, 2),
        'RMSE (Cr)': round(rmse, 2),
        'R2': round(r2, 4),
        'MAPE (%)': round(rel_error, 2)
    }
    return metrics

def train_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found. Run cost_features.py first.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    
    # Drop rows where target is missing or original cost is missing
    df = df.dropna(subset=['target_total_cost', 'original_cost'])
    
    # Define features
    num_features = ['original_cost', 'physical_progress', 'cumulative_expenditure', 
                    'progress_change_1m', 'expenditure_change_1m', 'expenditure_per_progress']
    cat_features = ['state', 'agency', 'project_size_category']
    
    # Save feature names for inference
    with open(os.path.join(MODEL_DIR, "cost_feature_columns.json"), "w") as f:
        json.dump({'num_features': num_features, 'cat_features': cat_features}, f)
        
    X = df[num_features + cat_features].copy()
    y = df['target_total_cost']
    
    # Fill any remaining NaNs in features
    for col in num_features:
        X[col] = X[col].fillna(0)
    for col in cat_features:
        X[col] = X[col].fillna('Unknown')
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features)
        ])
    
    # 1. Baseline: Ridge Regression
    lr = Pipeline(steps=[('preprocessor', preprocessor), ('regressor', Ridge(alpha=1.0))])
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    
    # 2. Random Forest Regressor
    rf = Pipeline(steps=[('preprocessor', preprocessor), ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))])
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    
    # 3. XGBoost
    xgb_pred = None
    if XGBRegressor is not None:
        xgb = Pipeline(steps=[('preprocessor', preprocessor), ('regressor', XGBRegressor(n_estimators=100, random_state=42, learning_rate=0.1))])
        xgb.fit(X_train, y_train)
        xgb_pred = xgb.predict(X_test)
        
    # Evaluate
    results = []
    results.append(evaluate_model("Ridge Regression", y_test, lr_pred))
    results.append(evaluate_model("Random Forest", y_test, rf_pred))
    
    if xgb_pred is not None:
        results.append(evaluate_model("XGBoost", y_test, xgb_pred))
        
    results_df = pd.DataFrame(results)
    results_df.to_csv(os.path.join(OUTPUT_DIR, "model_comparison.csv"), index=False)
    print("\nModel Evaluation Results:")
    print(results_df.to_string())
    
    # Select best model (Random Forest is usually robust, but if XGBoost is better, use it)
    best_model_name = results_df.sort_values(by="MAE (Cr)").iloc[0]["Model"]
    print(f"\nBest model selected: {best_model_name}")
    
    if best_model_name == "XGBoost":
        best_model = xgb
        final_preds = xgb_pred
    elif best_model_name == "Random Forest":
        best_model = rf
        final_preds = rf_pred
    else:
        best_model = lr
        final_preds = lr_pred
        
    # Save best model
    joblib.dump(best_model, os.path.join(MODEL_DIR, "cost_prediction_model.pkl"))
    
    # Predict for ALL data (for Member 5 and 6)
    all_preds = best_model.predict(X)
    
    # Add predictions back to dataframe
    output_df = df.copy()
    output_df['predicted_total_cost'] = all_preds
    
    # Cap prediction to not be lower than cumulative expenditure (can't cost less than what we spent!)
    output_df['predicted_total_cost'] = np.maximum(output_df['predicted_total_cost'], output_df['cumulative_expenditure'])
    
    # Calculate predicted cost overrun
    # Baseline for overrun is original_cost
    output_df['cost_overrun_percent'] = np.where(
        output_df['original_cost'] > 0,
        ((output_df['predicted_total_cost'] - output_df['original_cost']) / output_df['original_cost']) * 100,
        0
    )
    
    # Save final predictions
    output_cols = [
        'project_code', 'report_month', 'agency', 'state', 
        'physical_progress', 'cumulative_expenditure', 
        'original_cost', 'target_total_cost', 
        'predicted_total_cost', 'cost_overrun_percent'
    ]
    output_df[output_cols].to_csv(os.path.join(OUTPUT_DIR, "cost_predictions.csv"), index=False)
    print(f"\nSaved final predictions to {os.path.join(OUTPUT_DIR, 'cost_predictions.csv')}")
    
    # Generate Plots
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, final_preds, alpha=0.5)
    plt.plot([0, max(y_test)], [0, max(y_test)], 'r--')
    plt.xlabel('Actual Total Cost (Cr)')
    plt.ylabel('Predicted Total Cost (Cr)')
    plt.title(f'{best_model_name}: Predicted vs Actual Cost')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "predicted_vs_actual_cost.png"))
    plt.close()
    
    # Residuals
    residuals = y_test - final_preds
    plt.figure(figsize=(10, 6))
    plt.scatter(final_preds, residuals, alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('Predicted Total Cost (Cr)')
    plt.ylabel('Residual (Actual - Predicted)')
    plt.title('Residual Plot')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "residual_plot.png"))
    plt.close()
    
    # Feature Importance (if tree-based)
    if hasattr(best_model.named_steps['regressor'], 'feature_importances_'):
        importances = best_model.named_steps['regressor'].feature_importances_
        # Get feature names after OneHotEncoding
        ohe = best_model.named_steps['preprocessor'].named_transformers_['cat']
        cat_feature_names = ohe.get_feature_names_out(cat_features)
        all_feature_names = num_features + list(cat_feature_names)
        
        # Sort and take top 20
        indices = np.argsort(importances)[::-1][:20]
        
        plt.figure(figsize=(12, 8))
        plt.title("Feature Importances")
        plt.bar(range(20), importances[indices], align="center")
        plt.xticks(range(20), [all_feature_names[i] for i in indices], rotation=90)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "feature_importance.png"))
        plt.close()

if __name__ == "__main__":
    train_models()
