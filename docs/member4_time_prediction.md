# Member 4 - Time Prediction ML Engine

## Objective
To predict the total duration or expected completion date for a given PAIMANA project based on its physical progress, expenditure, and historical velocity.

## Methodology

### 1. Data Preparation (`src/features/time_features.py`)
- We engineered temporal features such as:
  - `project_age_months`: The number of months since the start date.
  - `target_duration_months`: The planned duration based on the revised (or original) completion date.
  - `progress_velocity_1m`: The rate of physical progress over the last month.

### 2. Modeling (`src/models/train_time_model.py`)
- **Algorithms Evaluated:** Ridge Regression, Random Forest Regressor, XGBoost.
- **Target Variable:** The `target_total_duration` derived from historical longitudinal snapshots.
- **Constraints Applied:** We enforced that the predicted total duration must be *at least* the current `project_age_months`, preventing physically impossible completion dates in the past.

### 3. Execution
- Run `python src/features/time_features.py` to prepare the dataset.
- Run `python src/models/train_time_model.py` to train the models and output final predictions.

## Outputs
- `models/time_prediction_model.pkl`: Best performing ML model.
- `outputs/member4/time_predictions.csv`: Final predictions containing `predicted_duration_months` and `time_overrun_percent`.
- Evaluation plots including actual vs predicted, and feature importance.
