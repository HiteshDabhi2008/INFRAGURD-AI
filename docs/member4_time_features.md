# Schedule Feature & Leakage Research (Member 4)

This document catalogs the available features in `paimana_master_v1.csv` and evaluates their suitability as inputs for the Time Prediction Model, operating under the "Implementation-time Early Warning" prediction point.

## 1. Safe Inputs (Confirmed in Dataset)

### `original_duration_months`
- **Source**: Calculated: `original_completion_date` - `approval_date`
- **Meaning**: The baseline planned duration of the project.
- **Usefulness**: Very High. Projects with a baseline duration of 5+ years inherently face more exogenous risks (election cycles, macro-economic shifts, prolonged land acquisition) than 1-year projects.
- **Classification**: **SAFE INPUT**

### `original_cost`
- **Source**: PDF Column 6
- **Meaning**: The initial project budget, acting as a proxy for physical scale and complexity.
- **Usefulness**: High. Mega-projects generally take longer to coordinate and clear regulatory hurdles.
- **Classification**: **SAFE INPUT**

### `state`
- **Source**: PDF Column 3
- **Meaning**: Project location.
- **Usefulness**: High. Environmental clearances (e.g., forest laws) and land acquisition speed vary drastically by state jurisdiction. 
- **Classification**: **SAFE INPUT**

### `agency`
- **Source**: PDF Column 2
- **Meaning**: The executing body.
- **Usefulness**: High. Reflects organizational efficiency and contractor management capability.
- **Classification**: **SAFE INPUT**

## 2. Snapshot/Implementation Inputs

### `physical_progress`
- **Source**: PDF Column 8
- **Meaning**: Percentage of physical completion at the time of the snapshot (July 2026).
- **Usefulness**: High, *but only when paired with project age*. A project at 10% progress after 3 years is heavily delayed; a project at 10% progress after 1 month is on track.
- **Classification**: **POTENTIAL INPUT** (Valid for Implementation-time prediction).

### `cumulative_expenditure`
- **Source**: PDF Column 7
- **Meaning**: Total funds spent to date.
- **Usefulness**: Medium. Often correlated with physical progress, but financial bottlenecks (funds exhausted before progress is complete) heavily predict future schedule stalling.
- **Classification**: **POTENTIAL INPUT** (Valid for Implementation-time prediction).

## 3. High Leakage Risk Variables (DO NOT USE AS INPUTS)

### `revised_completion_date`
- **Why it leaks**: Directly defines the Target. Knowing the revised date mathematically gives you the time overrun.
- **Classification**: **TARGET / OUTCOME (LEAKAGE)**

### `time_overrun_months` & `time_overrun_flag`
- **Why it leaks**: They ARE the targets.
- **Classification**: **TARGET / OUTCOME (LEAKAGE)**

## 4. Missing but Highly Desirable Features (Requires Joins)

To improve future iterations of the model, we strongly recommend integrating:
- **`sector` & `ministry`**: Not currently at the project level in the master dataset, but highly predictive of delays (e.g., Railways vs. Urban Development).

## 5. External Variables Research (For Future Integration)

These external factors are known primary drivers of schedule delays in Indian infrastructure:
1. **Land Acquisition Status**: (Source: State Land Records / PARIVESH). Delay in land handover is the #1 cause of project stalling.
2. **Forest/Environmental Clearances**: (Source: PARIVESH portal). Projects in eco-sensitive zones face structural delays.
3. **Monsoon/Weather Data**: (Source: IMD API). Heavy rainfall completely halts civil construction for 2-3 months a year in certain states.
4. **Utility Shifting**: Delays in shifting electricity/water lines handled by municipal bodies.
