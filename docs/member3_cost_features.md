# Member 3: Cost Feature Engineering

## Objective
To generate highly predictive, temporal features that capture the "velocity" of a project's physical and financial progress, while strictly avoiding data leakage.

## Input Data
The features are engineered from the `paimana_historical.csv` dataset, which contains monthly snapshots from April to July 2026.

## Engineered Features

### Temporal Features (Velocity)
1. **`progress_change_1m`**: 
   - Calculation: `physical_progress (Current Month) - physical_progress (Previous Month)`
   - Meaning: The speed at which the project physically progressed over the last 30 days.
2. **`expenditure_change_1m`**:
   - Calculation: `cumulative_expenditure (Current Month) - cumulative_expenditure (Previous Month)`
   - Meaning: The financial burn rate over the last 30 days.

### Derived Ratios
1. **`expenditure_per_progress`**:
   - Calculation: `cumulative_expenditure / physical_progress`
   - Meaning: The amount of money spent to achieve 1% of physical progress. This is a critical indicator of cost efficiency. If this number is increasing rapidly, a cost overrun is highly likely.

### Categorical Features
1. **`project_size_category`**:
   - Calculation: Binning `original_cost` into 'Small' (<1000 Cr), 'Medium' (1000-5000 Cr), and 'Large' (>5000 Cr).
   - Meaning: Mega-projects often have different risk profiles than smaller projects.

## Output
The engineered features are saved to `data/processed/cost_ml_dataset.csv` and fed directly into the model training pipeline.
