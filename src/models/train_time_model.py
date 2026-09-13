"""
Member 4: Time Overrun Prediction — Training Pipeline
=====================================================
Trains classification (time_overrun_flag) and regression (time_overrun_months)
models using leakage-safe features from the PAIMANA July 2026 snapshot.

Usage:
    python src/models/train_time_model.py
"""

import os
import json
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
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
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    mean_absolute_error, mean_squared_error, r2_score
)

warnings.filterwarnings('ignore', category=FutureWarning)

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("XGBoost not available; continuing with scikit-learn models only.")

# ── directories ──────────────────────────────────────────────────────────────
OUTPUT_DIR = "outputs/member4"
MODELS_DIR = "models"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ── feature definitions ─────────────────────────────────────────────────────
NUM_FEATURES = [
    'original_cost',
    'project_age_days',
    'physical_progress',
    'cumulative_expenditure',
    'safe_expenditure_percent',
    'safe_progress_gap',
    'original_duration_days',
]

CAT_FEATURES = [
    'state',
    'agency',
    'sector',
    'project_size_category',
]


# ── helper: infer sector (reused from Member 2/3) ───────────────────────────
def _infer_sector(row):
    agency = str(row.get('agency', '')).lower()
    name = str(row.get('project_name', '')).lower()
    if 'rail' in agency or 'rail' in name or 'rly' in agency:
        return 'Railways'
    if any(k in agency for k in ('road', 'highway', 'nhai', 'nhidcl')) or 'road' in name:
        return 'Roads & Highways'
    if any(k in agency for k in ('power', 'ntpc', 'pgcil', 'hydro')) or 'power' in name:
        return 'Power'
    if 'coal' in agency or 'mine' in agency or 'mining' in name or 'coal' in name:
        return 'Coal & Mining'
    if any(k in agency for k in ('petroleum', 'oil', 'gas', 'ongc')) or 'refinery' in name:
        return 'Petroleum & Natural Gas'
    if 'water' in agency or 'irrigation' in name:
        return 'Water Resources'
    if 'urban' in agency or 'metro' in name or 'housing' in agency:
        return 'Urban Development'
    if 'telecom' in agency or 'bsnl' in agency or 'telecom' in name:
        return 'Telecommunications'
    if any(k in agency for k in ('airport', 'aviation', 'aai')) or 'airport' in name:
        return 'Civil Aviation'
    if 'port' in agency or 'shipping' in agency or 'port' in name:
        return 'Ports & Shipping'
    return 'Other'


# ── data loading & target creation ───────────────────────────────────────────
def load_data():
    master = pd.read_csv("data/processed/master_projects.csv")
    features = pd.read_csv("data/processed/project_features.csv")

    df = pd.merge(master, features, on=['project_code', 'report_month'], how='left')

    # Parse dates
    for col in ('approval_date', 'original_completion_date', 'revised_completion_date'):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Require valid original_completion_date and approval_date
    df = df.dropna(subset=['original_completion_date', 'approval_date'])

    # ── Targets ──────────────────────────────────────────────────────────────
    # Fill missing revised dates with original (assume on-time if no revision)
    revised_filled = df['revised_completion_date'].fillna(df['original_completion_date'])
    df['time_overrun_months'] = (revised_filled - df['original_completion_date']).dt.days / 30.44
    df['time_overrun_flag'] = (df['time_overrun_months'] > 0).astype(int)

    # ── Derived safe features ────────────────────────────────────────────────
    df = df[df['original_cost'] > 0].copy()

    if 'safe_expenditure_percent' not in df.columns:
        df['safe_expenditure_percent'] = (
            df['cumulative_expenditure'] / df['original_cost']
        ) * 100

    if 'safe_progress_gap' not in df.columns:
        df['safe_progress_gap'] = df['safe_expenditure_percent'] - df['physical_progress']

    df['sector'] = df.apply(_infer_sector, axis=1)

    # ── Save feature schema ──────────────────────────────────────────────────
    schema = {
        "numeric_features": NUM_FEATURES,
        "categorical_features": CAT_FEATURES,
    }
    schema_path = os.path.join(MODELS_DIR, "time_feature_columns.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=4)
    print(f"Saved feature schema -> {schema_path}")

    X = df[NUM_FEATURES + CAT_FEATURES]
    y_cls = df['time_overrun_flag']
    y_reg = df['time_overrun_months']

    return X, y_cls, y_reg, df


# ── preprocessing ────────────────────────────────────────────────────────────
def build_preprocessor():
    num_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])
    return ColumnTransformer([
        ('num', num_pipe, NUM_FEATURES),
        ('cat', cat_pipe, CAT_FEATURES),
    ])


# ── main training loop ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Member 4 — Time Overrun Prediction Pipeline")
    print("=" * 60)

    X, y_cls, y_reg, full_df = load_data()
    print(f"\nDataset: {len(X)} projects")
    print(f"Time overrun prevalence: {y_cls.mean()*100:.1f}%")

    # ── train / test split (shared for both tasks) ───────────────────────────
    X_train, X_test, yc_train, yc_test, yr_train, yr_test = train_test_split(
        X, y_cls, y_reg, test_size=0.2, random_state=42, stratify=y_cls,
    )
    print(f"Train: {len(X_train)}  |  Test: {len(X_test)}")

    preprocessor = build_preprocessor()
    results = []

    # ═══════════════════════════════════════════════════════════════════════
    # CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    print("\n-- Classification Models " + "-" * 34)

    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight='balanced',
        ),
    }
    if XGB_AVAILABLE:
        # Compute scale_pos_weight for class imbalance
        neg, pos = (yc_train == 0).sum(), (yc_train == 1).sum()
        spw = neg / pos if pos > 0 else 1
        classifiers["XGBoost"] = XGBClassifier(
            n_estimators=200, random_state=42,
            scale_pos_weight=spw,
            eval_metric='logloss',
        )

    best_clf_pipeline = None
    best_clf_f1 = -1
    best_clf_name = ""

    for name, clf in classifiers.items():
        pipe = Pipeline([('pre', preprocessor), ('model', clf)])
        pipe.fit(X_train, yc_train)

        y_pred = pipe.predict(X_test)
        y_prob = (
            pipe.predict_proba(X_test)[:, 1]
            if hasattr(pipe.named_steps['model'], 'predict_proba')
            else y_pred.astype(float)
        )

        acc = accuracy_score(yc_test, y_pred)
        prec = precision_score(yc_test, y_pred, zero_division=0)
        rec = recall_score(yc_test, y_pred, zero_division=0)
        f1 = f1_score(yc_test, y_pred, zero_division=0)
        auc = roc_auc_score(yc_test, y_prob)

        results.append({
            "Task": "Classification",
            "Model": name,
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1": round(f1, 4),
            "ROC-AUC": round(auc, 4),
        })

        print(f"  {name:25s}  Acc={acc:.3f}  P={prec:.3f}  R={rec:.3f}  "
              f"F1={f1:.3f}  AUC={auc:.3f}")

        if f1 > best_clf_f1:
            best_clf_f1 = f1
            best_clf_pipeline = pipe
            best_clf_name = name

    # Save best classifier
    clf_path = os.path.join(MODELS_DIR, "time_classifier.pkl")
    joblib.dump(best_clf_pipeline, clf_path)
    print(f"\n  [OK] Best classifier: {best_clf_name} (F1={best_clf_f1:.3f}) -> {clf_path}")

    # Confusion matrix for best classifier
    y_pred_best = best_clf_pipeline.predict(X_test)
    cm = confusion_matrix(yc_test, y_pred_best)
    print(f"\n  Confusion Matrix ({best_clf_name}):")
    print(f"    TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"    FN={cm[1,0]}  TP={cm[1,1]}")
    print(f"\n  Classification Report:\n{classification_report(yc_test, y_pred_best, zero_division=0)}")

    # ═══════════════════════════════════════════════════════════════════════
    # REGRESSION
    # ═══════════════════════════════════════════════════════════════════════
    print("\n-- Regression Models " + "-" * 38)

    regressors = {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=200, random_state=42,
        ),
    }
    if XGB_AVAILABLE:
        regressors["XGBoost Regressor"] = XGBRegressor(
            n_estimators=200, random_state=42,
        )

    best_reg_pipeline = None
    best_reg_r2 = -float('inf')
    best_reg_name = ""

    for name, reg in regressors.items():
        pipe = Pipeline([('pre', preprocessor), ('model', reg)])
        pipe.fit(X_train, yr_train)

        y_pred = pipe.predict(X_test)
        mae = mean_absolute_error(yr_test, y_pred)
        rmse = np.sqrt(mean_squared_error(yr_test, y_pred))
        r2 = r2_score(yr_test, y_pred)

        results.append({
            "Task": "Regression",
            "Model": name,
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "R2": round(r2, 4),
        })
        print(f"  {name:25s}  MAE={mae:.2f}  RMSE={rmse:.2f}  R2={r2:.3f}")

        if r2 > best_reg_r2:
            best_reg_r2 = r2
            best_reg_pipeline = pipe
            best_reg_name = name

    # Save best regressor
    reg_path = os.path.join(MODELS_DIR, "time_regressor.pkl")
    joblib.dump(best_reg_pipeline, reg_path)
    print(f"\n  [OK] Best regressor: {best_reg_name} (R2={best_reg_r2:.3f}) -> {reg_path}")

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL COMPARISON TABLE
    # ═══════════════════════════════════════════════════════════════════════
    results_df = pd.DataFrame(results)
    comp_path = os.path.join(OUTPUT_DIR, "model_comparison.csv")
    results_df.to_csv(comp_path, index=False)
    print(f"\n  [OK] Model comparison -> {comp_path}")
    print(results_df.to_string(index=False))

    # ═══════════════════════════════════════════════════════════════════════
    # FEATURE IMPORTANCE
    # ═══════════════════════════════════════════════════════════════════════
    print("\n-- Feature Importance " + "-" * 37)
    model_step = best_clf_pipeline.named_steps['model']

    # Get feature names from the fitted preprocessor
    cat_encoder = best_clf_pipeline.named_steps['pre'].transformers_[1][1].named_steps['onehot']
    cat_names = list(cat_encoder.get_feature_names_out(CAT_FEATURES))
    all_names = NUM_FEATURES + cat_names

    if hasattr(model_step, 'feature_importances_'):
        importances = model_step.feature_importances_
        imp_source = best_clf_name
    elif hasattr(model_step, 'coef_'):
        # For linear models use absolute coefficient magnitudes
        importances = np.abs(model_step.coef_[0])
        imp_source = f"{best_clf_name} (|coefficients|)"
    else:
        # Train a separate RF just for importance
        rf_pipe = Pipeline([('pre', preprocessor), ('model', RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight='balanced'))])
        rf_pipe.fit(X_train, yc_train)
        importances = rf_pipe.named_steps['model'].feature_importances_
        imp_source = "Random Forest (auxiliary)"

    imp_df = pd.DataFrame({
        'Feature': all_names,
        'Importance': importances,
    }).sort_values('Importance', ascending=False)

    plt.figure(figsize=(10, 8))
    top = imp_df.head(20)
    sns.barplot(data=top, x='Importance', y='Feature', hue='Feature',
                palette='viridis', dodge=False, legend=False)
    plt.title(f"Top 20 Feature Importances - Time Classifier ({imp_source})")
    plt.tight_layout()
    fi_path = os.path.join(OUTPUT_DIR, "time_feature_importance.png")
    plt.savefig(fi_path, dpi=150)
    plt.close()
    print(f"  [OK] Feature importance plot -> {fi_path}")
    print(f"\n  Top 10 features ({imp_source}):")
    for _, r in imp_df.head(10).iterrows():
        print(f"    {r['Feature']:40s} {r['Importance']:.4f}")

    # ═══════════════════════════════════════════════════════════════════════
    # PROJECT-LEVEL PREDICTIONS (Team Output)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n-- Generating project-level predictions " + "-" * 19)
    X_all = full_df[NUM_FEATURES + CAT_FEATURES]
    probs = best_clf_pipeline.predict_proba(X_all)[:, 1]
    preds = best_clf_pipeline.predict(X_all)
    reg_preds = best_reg_pipeline.predict(X_all)

    pred_df = pd.DataFrame({
        'project_code': full_df['project_code'].values,
        'project_name': full_df['project_name'].values,
        'time_risk_probability': np.round(probs, 3),
        'time_overrun_predicted': preds,
        'time_overrun_months_predicted': np.round(reg_preds, 1),
        'time_risk': pd.cut(
            probs, bins=[0, 0.40, 0.70, 1.01],
            labels=['LOW', 'MEDIUM', 'HIGH'], right=False,
        ),
    })
    pred_path = os.path.join(OUTPUT_DIR, "time_prediction_results.csv")
    pred_df.to_csv(pred_path, index=False)
    print(f"  [OK] Predictions for {len(pred_df)} projects -> {pred_path}")

    risk_counts = pred_df['time_risk'].value_counts()
    for level in ['HIGH', 'MEDIUM', 'LOW']:
        cnt = risk_counts.get(level, 0)
        print(f"    {level:8s}: {cnt}")

    print("\n" + "=" * 60)
    print("Time overrun pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
