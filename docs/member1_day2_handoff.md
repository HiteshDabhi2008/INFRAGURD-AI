# Data Engineer Day 2 Handoff (Member 1)

## Overview
The Day 2 Data Engineering pipeline is complete. The raw PAIMANA dataset has been successfully transformed into a clean, ML-ready dataset with derived features. A local SQLite database and an optional FastAPI layer have been established to allow immediate consumption by the rest of the team.

## Outputs & Artifacts

### 1. Validated Master Dataset
- **Location**: `data/processed/master_projects.csv`
- **Description**: Contains cleaned and validated raw features from the original PDF extraction. All negative costs have been removed, missing constraints handled, and duplicates stripped. 
- **Quality Report**: Available at `docs/data_quality_report.md`.

### 2. Base Feature Dataset
- **Location**: `data/processed/project_features.csv`
- **Description**: Contains reusable derived features such as `project_age_days`, `progress_gap`, `cost_change_percent`, etc.

### 3. Database
- **Location**: `data/processed/database.sqlite`
- **Structure**:
  - `projects`: Core static project details (Code, Name, Agency, State)
  - `project_snapshots`: Temporal data (Costs, Dates, Expenditure, Progress) specific to the report month.
  - `project_features`: The ML features corresponding to the snapshots.
  - `data_sources`: Source tracking (e.g., July 2026 PAIMANA Flash Report).

### 4. Data Repository API (Python)
- **Location**: `src/data/repository.py`
- **Description**: A wrapper for SQLite to abstract data access.

### 5. Optional FastAPI Layer
- **Location**: `src/data/api.py`
- **Description**: Provides REST endpoints for querying data. Run with `python -m uvicorn src.data.api:app --reload`.

## Instructions for Team Members

### How M3 (Cost Prediction) Can Load the Data
You can either read the CSVs directly:
```python
import pandas as pd
master = pd.read_csv("data/processed/master_projects.csv")
features = pd.read_csv("data/processed/project_features.csv")
df = master.merge(features, on=["project_code", "report_month"])
```
Or use the repository for a cleaner interface:
```python
from src.data.repository import get_all_projects
df = get_all_projects()
```
*Note: Ensure you drop `revised_cost`, `cost_change`, and `cost_change_percent` when creating your input features, as these leak the target.*

### How M4 (Time Prediction) Can Load the Data
Follow the same loading approach as M3.
*Note: Ensure you drop `revised_completion_date`, `revised_duration_days`, and `time_overrun_months` when creating your input features, as these leak the target.*

### How M5 (Risk Engine) Can Load the Data
You can load the master dataset combined with features. Your input should primarily use `progress_gap`, `expenditure_percent`, and `project_size_category`, in combination with the models produced by M3 and M4. The API layer (`src/data/api.py`) is recommended if you plan on deploying the engine as a service.

### How M6 (AI/RAG Dashboard) Can Retrieve Project Information
You can leverage the database through the `src/data/repository.py` functions directly inside your dashboard/RAG application:
```python
from src.data.repository import get_project, get_projects_by_state

# Fetch project for AI prompt context
project_context = get_project("612786")

# Fetch stats for dashboard map
ap_projects = get_projects_by_state("Andhra Pradesh")
```
Alternatively, integrate with the FastAPI server using HTTP requests if you need separation of concerns.

## Next Steps / Notes
- The data dictionary `docs/data_dictionary.md` has been fully updated.
- Please review `docs/data_leakage.md` (or the warnings in the dictionary) before feeding features into your models.
