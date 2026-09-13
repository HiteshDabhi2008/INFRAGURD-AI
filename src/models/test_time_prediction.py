"""
Member 4: Test script for time_model.predict_time_risk()
========================================================
Validates that the saved model loads, accepts a project dictionary,
and returns a well-formed risk assessment.
"""

import json
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.models.time_model import predict_time_risk


def test_typical_project():
    """A mid-stage roads project in Maharashtra."""
    project = {
        'original_cost': 2500.0,
        'project_age_days': 1800,
        'physical_progress': 55.0,
        'cumulative_expenditure': 1400.0,
        'safe_expenditure_percent': (1400.0 / 2500.0) * 100,  # 56%
        'safe_progress_gap': ((1400.0 / 2500.0) * 100) - 55.0,  # 1%
        'original_duration_days': 1460,  # ~4 years
        'state': 'Maharashtra',
        'agency': 'NHAI',
        'sector': 'Roads & Highways',
        'project_size_category': 'Medium',
    }

    print("Test 1: Typical mid-stage roads project")
    print(json.dumps(project, indent=2))
    result = predict_time_risk(project)
    print("Result:", json.dumps(result, indent=2))
    assert 'risk_level' in result
    assert 'overrun_probability' in result
    assert 'expected_overrun_months' in result
    assert 'is_time_overrun' in result
    assert result['risk_level'] in ('HIGH', 'MEDIUM', 'LOW')
    print("  PASSED\n")
    return result


def test_early_stage_project():
    """A newly approved large power project — minimal progress."""
    project = {
        'original_cost': 8000.0,
        'project_age_days': 180,
        'physical_progress': 2.0,
        'cumulative_expenditure': 100.0,
        'safe_expenditure_percent': (100.0 / 8000.0) * 100,
        'safe_progress_gap': ((100.0 / 8000.0) * 100) - 2.0,
        'original_duration_days': 2190,  # ~6 years
        'state': 'Jharkhand',
        'agency': 'National Thermal Power Corporation [NTPC]',
        'sector': 'Power',
        'project_size_category': 'Large',
    }

    print("Test 2: Early-stage large power project")
    print(json.dumps(project, indent=2))
    result = predict_time_risk(project)
    print("Result:", json.dumps(result, indent=2))
    assert result['risk_level'] in ('HIGH', 'MEDIUM', 'LOW')
    print("  PASSED\n")
    return result


def test_missing_features():
    """Ensure model handles missing optional features gracefully."""
    project = {
        'original_cost': 500.0,
        'project_age_days': 600,
        'physical_progress': 30.0,
        # cumulative_expenditure intentionally missing
        # safe_expenditure_percent intentionally missing
        'original_duration_days': 730,
        'state': 'Unknown State',
        'agency': 'Unknown Agency',
        'sector': 'Other',
        'project_size_category': 'Small',
    }

    print("Test 3: Missing features (should still work via imputation)")
    result = predict_time_risk(project)
    print("Result:", json.dumps(result, indent=2))
    assert result['risk_level'] in ('HIGH', 'MEDIUM', 'LOW')
    print("  PASSED\n")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Time Model Prediction Tests")
    print("=" * 60 + "\n")

    r1 = test_typical_project()
    r2 = test_early_stage_project()
    r3 = test_missing_features()

    print("=" * 60)
    print("All tests PASSED.")
    print("=" * 60)
