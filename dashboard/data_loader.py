"""
Data loading and preparation utilities for the InfraGuard-AI Dashboard.
Loads CSV data, merges datasets, and prepares project dictionaries for ML models.
"""

import os
import sys
import pandas as pd
import streamlit as st

# Setup path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

MASTER_PATH = os.path.join(BASE_DIR, "data", "processed", "master_projects.csv")
FEATURES_PATH = os.path.join(BASE_DIR, "data", "processed", "project_features.csv")
EARLY_WARNINGS_PATH = os.path.join(BASE_DIR, "outputs", "member5", "early_warning_results.csv")
RISK_SUMMARY_PATH = os.path.join(BASE_DIR, "outputs", "member5", "risk_summary.csv")


@st.cache_data(ttl=600)
def load_master_data() -> pd.DataFrame:
    """Load master_projects.csv with error handling."""
    if not os.path.exists(MASTER_PATH):
        st.error(f"Master data file not found: {MASTER_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(MASTER_PATH)
    # Ensure numeric columns
    for col in ["original_cost", "revised_cost", "cumulative_expenditure", "physical_progress"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=600)
def load_features_data() -> pd.DataFrame:
    """Load project_features.csv with error handling."""
    if not os.path.exists(FEATURES_PATH):
        st.warning("Features data file not found. Some analytics may be unavailable.")
        return pd.DataFrame()
    df = pd.read_csv(FEATURES_PATH)
    return df


@st.cache_data(ttl=600)
def load_early_warnings() -> pd.DataFrame:
    """Load pre-computed early warning results from Member 5."""
    if not os.path.exists(EARLY_WARNINGS_PATH):
        return pd.DataFrame()
    try:
        df = pd.read_csv(EARLY_WARNINGS_PATH)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_merged_data() -> pd.DataFrame:
    """Merge master and features data on project_code."""
    master = load_master_data()
    features = load_features_data()

    if master.empty:
        return master
    if features.empty:
        return master

    merged = pd.merge(master, features, on="project_code", how="left", suffixes=("", "_feat"))
    # Drop duplicate report_month column if created
    if "report_month_feat" in merged.columns:
        merged.drop(columns=["report_month_feat"], inplace=True)

    # Compute safe_expenditure_percent for models (expenditure / revised_cost * 100)
    if "cumulative_expenditure" in merged.columns and "revised_cost" in merged.columns:
        merged["safe_expenditure_percent"] = merged.apply(
            lambda r: (r["cumulative_expenditure"] / r["revised_cost"] * 100)
            if pd.notna(r.get("revised_cost")) and r.get("revised_cost", 0) > 0
            else r.get("expenditure_percent"),
            axis=1,
        )
    # Compute safe_progress_gap
    if "safe_expenditure_percent" in merged.columns and "physical_progress" in merged.columns:
        merged["safe_progress_gap"] = merged["safe_expenditure_percent"] - merged["physical_progress"]

    # Infer sector from agency if missing
    if "sector" not in merged.columns:
        merged["sector"] = merged["agency"].apply(_infer_sector)

    return merged


def _infer_sector(agency: str) -> str:
    """Simple heuristic to infer sector from agency name."""
    if pd.isna(agency):
        return "Unknown"
    a = str(agency).lower()
    if "rail" in a:
        return "Railways"
    elif "road" in a or "highway" in a or "nhai" in a:
        return "Roads & Highways"
    elif "airport" in a or "aviation" in a or "aai" in a:
        return "Aviation"
    elif "port" in a or "shipping" in a:
        return "Ports & Shipping"
    elif "power" in a or "energy" in a or "ntpc" in a or "nhpc" in a or "coal" in a:
        return "Power & Energy"
    elif "petroleum" in a or "oil" in a or "gas" in a or "ongc" in a:
        return "Petroleum & Gas"
    elif "water" in a or "irrigation" in a or "dam" in a:
        return "Water Resources"
    elif "metro" in a:
        return "Metro Rail"
    elif "steel" in a:
        return "Steel"
    elif "telecom" in a or "bsnl" in a:
        return "Telecom"
    elif "defence" in a or "drdo" in a:
        return "Defence"
    elif "atomic" in a or "nuclear" in a:
        return "Atomic Energy"
    elif "health" in a or "aiims" in a:
        return "Health"
    elif "education" in a or "iit" in a:
        return "Education"
    elif "urban" in a or "smart city" in a or "housing" in a:
        return "Urban Development"
    else:
        return "Other"


def prepare_project_dict(row: pd.Series) -> dict:
    """Convert a merged DataFrame row into a dict suitable for ML model input."""
    d = row.where(pd.notna(row), None).to_dict()
    # Ensure key fields exist for models
    for key in [
        "original_cost", "project_age_days", "physical_progress",
        "safe_expenditure_percent", "original_duration_days",
        "cumulative_expenditure", "safe_progress_gap",
        "state", "agency", "sector", "project_size_category",
        "project_code",
    ]:
        if key not in d:
            d[key] = None
    return d


def get_risk_prediction(project_dict: dict) -> dict:
    """
    Safely call Member 5's risk engine.
    Returns dict with risk results or an error fallback.
    """
    import warnings
    warnings.filterwarnings("ignore")
    try:
        from src.risk.risk_engine import predict_project_risk
        result = predict_project_risk(project_dict)
        return result
    except Exception as e:
        return {
            "project_code": project_dict.get("project_code"),
            "risk_score": None,
            "overall_risk": "UNAVAILABLE",
            "warnings": [],
            "explanation": f"Risk engine error: {str(e)}",
            "cost_model_output": {"risk_level": "UNAVAILABLE", "overrun_probability": None, "expected_overrun_percent": None},
            "time_model_output": {"risk_level": "UNAVAILABLE", "overrun_probability": None, "expected_overrun_months": None},
        }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filters to a DataFrame."""
    filtered = df.copy()
    if filters.get("state") and filters["state"] != "All":
        filtered = filtered[filtered["state"] == filters["state"]]
    if filters.get("agency") and filters["agency"] != "All":
        filtered = filtered[filtered["agency"] == filters["agency"]]
    if filters.get("sector") and filters["sector"] != "All":
        filtered = filtered[filtered["sector"] == filters["sector"]]
    if filters.get("risk_level") and filters["risk_level"] != "All":
        # This requires pre-computed risk; we'll handle it in pages
        pass
    if filters.get("search"):
        search = filters["search"].strip().lower()
        if search:
            mask = (
                filtered["project_code"].astype(str).str.lower().str.contains(search, na=False)
                | filtered["project_name"].astype(str).str.lower().str.contains(search, na=False)
            )
            filtered = filtered[mask]
    return filtered
