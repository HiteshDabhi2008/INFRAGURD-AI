import json
from cost_model import predict_cost_risk

def test_prediction():
    # A dummy project with features representing a typical ongoing project
    dummy_project = {
        'original_cost': 1500.0,
        'project_age_days': 1200,
        'physical_progress': 45.0,
        'cumulative_expenditure': 800.0,
        'safe_expenditure_percent': (800.0 / 1500.0) * 100,  # ~53.3%
        'safe_progress_gap': ((800.0 / 1500.0) * 100) - 45.0, # ~8.3%
        'original_duration_days': 1000,
        'state': 'Maharashtra',
        'agency': 'NHAI',
        'sector': 'Roads & Highways',
        'project_size_category': 'Medium'
    }

    print("Testing cost prediction on dummy project...")
    print(json.dumps(dummy_project, indent=2))
    
    result = predict_cost_risk(dummy_project)
    
    print("\n--- Prediction Result ---")
    print(json.dumps(result, indent=2))
    
    assert "risk_level" in result
    assert "overrun_probability" in result
    assert "expected_overrun_percent" in result
    
    print("\nTest passed successfully!")

if __name__ == "__main__":
    test_prediction()
