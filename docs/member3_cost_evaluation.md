# Member 3: Cost Model Evaluation

## Goal
To evaluate how accurately the Machine Learning pipeline predicts the final estimated cost (`target_total_cost`) at project completion.

## Metrics
- **Mean Absolute Error (MAE)**: The average absolute difference between predicted and actual cost. (Lower is better).
- **Mean Absolute Percentage Error (MAPE)**: The percentage error relative to the actual cost.

## Results
*(These results are populated after running `src/models/train_cost_model.py`)*

### Baseline (Ridge Regression)
- **MAE**: 472.63 Cr
- **MAPE**: 49.67%

### Random Forest
- **MAE**: 206.42 Cr
- **MAPE**: 13.03%

### XGBoost
- **MAE**: 274.52 Cr
- **MAPE**: 14.98%

## Conclusion
The model successfully identifies cost overruns based on current expenditure patterns. The predictions are exposed via `cost_predictions.csv` for use in the Risk Engine.
