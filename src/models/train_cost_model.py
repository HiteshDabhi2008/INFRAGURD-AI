import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

# Ensure output directories exist
os.makedirs("outputs/member3", exist_ok=True)
os.makedirs("models", exist_ok=True)

def load_data():
    master = pd.read_csv("data/processed/master_projects.csv")
    features = pd.read_csv("data/processed/project_features.csv")
    
    # Merge
    df = pd.merge(master, features, on=['project_code', 'report_month'], how='left')
    
    # We only use rows with valid original_cost and revised_cost
    df = df.dropna(subset=['original_cost', 'revised_cost'])
    
    # Filter out tiny projects or extreme outliers if necessary, but we keep mostly all for now
    df = df[df['original_cost'] > 0]
    
    # 1. Define Targets
    df['cost_overrun_flag'] = (df['revised_cost'] > df['original_cost']).astype(int)
    df['cost_overrun_percent'] = ((df['revised_cost'] - df['original_cost']) / df['original_cost']) * 100
    
    # 2. Select Safe Input Features
    # Numeric
    num_features = [
        'original_cost', 
        'project_age_days', 
        'physical_progress', 
        'cumulative_expenditure', 
        'safe_expenditure_percent', 
        'safe_progress_gap', 
        'original_duration_days'
    ]
    
    # Categorical
    # Infer sector for those missing (reusing member 2 logic briefly)
    def infer_sector(row):
        agency = str(row['agency']).lower()
        name = str(row['project_name']).lower()
        if 'rail' in agency or 'rail' in name or 'rly' in agency: return 'Railways'
        if 'road' in agency or 'highway' in agency or 'nhai' in agency or 'nhidcl' in agency or 'road' in name: return 'Roads & Highways'
        if 'power' in agency or 'ntpc' in agency or 'pgcil' in agency or 'hydro' in agency or 'power' in name: return 'Power'
        if 'coal' in agency or 'mine' in agency or 'mining' in name or 'coal' in name: return 'Coal & Mining'
        if 'petroleum' in agency or 'oil' in agency or 'gas' in agency or 'refinery' in name or 'ongc' in agency: return 'Petroleum & Natural Gas'
        if 'water' in agency or 'irrigation' in name: return 'Water Resources'
        if 'urban' in agency or 'metro' in name or 'housing' in agency: return 'Urban Development'
        if 'telecom' in agency or 'bsnl' in agency or 'telecom' in name: return 'Telecommunications'
        if 'airport' in agency or 'aviation' in agency or 'airport' in name or 'aai' in agency: return 'Civil Aviation'
        if 'port' in agency or 'shipping' in agency or 'port' in name: return 'Ports & Shipping'
        return 'Other'

    df['sector'] = df.apply(infer_sector, axis=1)
    
    cat_features = ['state', 'agency', 'sector', 'project_size_category']
    
    # Fill safe_ features if missing to allow pipeline to handle cleanly or compute them if not present
    if 'safe_expenditure_percent' not in df.columns:
        df['safe_expenditure_percent'] = (df['cumulative_expenditure'] / df['original_cost']) * 100
    if 'safe_progress_gap' not in df.columns:
        df['safe_progress_gap'] = df['safe_expenditure_percent'] - df['physical_progress']

    # Keep only needed columns
    features_df = df[num_features + cat_features]
    target_class = df['cost_overrun_flag']
    target_reg = df['cost_overrun_percent']
    
    # Save the feature schema
    feature_schema = {
        "numeric_features": num_features,
        "categorical_features": cat_features
    }
    with open("models/cost_feature_columns.json", "w") as f:
        json.dump(feature_schema, f, indent=4)
        
    return features_df, target_class, target_reg, num_features, cat_features

def build_preprocessor(num_features, cat_features):
    num_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(transformers=[
        ('num', num_transformer, num_features),
        ('cat', cat_transformer, cat_features)
    ])
    
    return preprocessor

def main():
    print("Loading data and defining targets...")
    X, y_class, y_reg, num_features, cat_features = load_data()
    
    # Train-test split (use same split for both classification and regression for comparison)
    X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
        X, y_class, y_reg, test_size=0.2, random_state=42
    )
    
    preprocessor = build_preprocessor(num_features, cat_features)
    
    results = []
    
    # --- CLASSIFICATION MODELS ---
    print("\n--- Training Classification Models ---")
    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest Classifier": RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    }
    if XGB_AVAILABLE:
        classifiers["XGBoost Classifier"] = XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')

    best_classifier = None
    best_clf_f1 = -1
    best_clf_name = ""
    
    for name, clf in classifiers.items():
        print(f"Training {name}...")
        pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', clf)])
        pipeline.fit(X_train, y_class_train)
        
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred
        
        acc = accuracy_score(y_class_test, y_pred)
        prec = precision_score(y_class_test, y_pred, zero_division=0)
        rec = recall_score(y_class_test, y_pred, zero_division=0)
        f1 = f1_score(y_class_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_class_test, y_prob)
        
        results.append({
            "Task": "Classification",
            "Model": name,
            "Accuracy/MAE": acc,
            "Precision/RMSE": prec,
            "Recall/R2": rec,
            "F1": f1,
            "ROC-AUC": auc
        })
        print(f"{name} -> Acc: {acc:.3f}, Precision: {prec:.3f}, Recall: {rec:.3f}, F1: {f1:.3f}, AUC: {auc:.3f}")
        
        # Track best classifier by F1 score
        if f1 > best_clf_f1:
            best_clf_f1 = f1
            best_classifier = pipeline
            best_clf_name = name
            
    # Save the best classifier
    print(f"\nSaving best classifier: {best_clf_name} (F1: {best_clf_f1:.3f})")
    joblib.dump(best_classifier, "models/cost_classifier.pkl")
    
    
    # --- REGRESSION MODELS ---
    print("\n--- Training Regression Models ---")
    regressors = {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42)
    }
    if XGB_AVAILABLE:
        regressors["XGBoost Regressor"] = XGBRegressor(random_state=42)

    best_regressor = None
    best_reg_r2 = -float("inf")
    best_reg_name = ""
    
    for name, reg in regressors.items():
        print(f"Training {name}...")
        pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', reg)])
        # For regression, we might want to predict only on those that have an overrun, or all.
        # Predicting on all to estimate total cost overrun
        pipeline.fit(X_train, y_reg_train)
        
        y_pred = pipeline.predict(X_test)
        
        mae = mean_absolute_error(y_reg_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_reg_test, y_pred))
        r2 = r2_score(y_reg_test, y_pred)
        
        results.append({
            "Task": "Regression",
            "Model": name,
            "Accuracy/MAE": mae,
            "Precision/RMSE": rmse,
            "Recall/R2": r2,
            "F1": None,
            "ROC-AUC": None
        })
        print(f"{name} -> MAE: {mae:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}")
        
        if r2 > best_reg_r2:
            best_reg_r2 = r2
            best_regressor = pipeline
            best_reg_name = name

    # Save the best regressor
    print(f"\nSaving best regressor: {best_reg_name} (R2: {best_reg_r2:.3f})")
    joblib.dump(best_regressor, "models/cost_regressor.pkl")
    
    # Save Model Comparison
    results_df = pd.DataFrame(results)
    results_df.to_csv("outputs/member3/model_comparison.csv", index=False)
    print("\nSaved model comparison to outputs/member3/model_comparison.csv")
    
    # --- EXPLAINABILITY (Feature Importance) ---
    print("\n--- Generating Feature Importance ---")
    
    # We will use the best Random Forest or XGBoost Classifier for explainability
    # Extract the feature names from the preprocessor
    # categorical encoder feature names
    cat_encoder = best_classifier.named_steps['preprocessor'].transformers_[1][1].named_steps['onehot']
    cat_feature_names = cat_encoder.get_feature_names_out(cat_features)
    all_feature_names = num_features + list(cat_feature_names)
    
    model_step = best_classifier.named_steps['model']
    
    if hasattr(model_step, 'feature_importances_'):
        importances = model_step.feature_importances_
        
        imp_df = pd.DataFrame({
            'Feature': all_feature_names,
            'Importance': importances
        }).sort_values(by='Importance', ascending=False)
        
        # Plot top 15 features
        plt.figure(figsize=(10, 8))
        sns.barplot(data=imp_df.head(15), x='Importance', y='Feature', palette="viridis")
        plt.title(f"Top 15 Feature Importances ({best_clf_name})")
        plt.tight_layout()
        plt.savefig("outputs/member3/feature_importance.png")
        print("Saved feature importance plot to outputs/member3/feature_importance.png")
    else:
        print(f"Feature importance not supported for {best_clf_name}")

if __name__ == "__main__":
    main()
