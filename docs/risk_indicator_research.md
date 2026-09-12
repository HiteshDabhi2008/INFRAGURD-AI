# Risk Indicator Research (Exploratory)

This document identifies potential exploratory risk indicators for PAIMANA projects based on the current data snapshot.

> **Note**: These are *potential indicators* for exploration, not confirmed predictive rules. They should be validated by domain experts and tested for statistical significance.

## 1. Financial Risk Indicators

### Abnormal Expenditure-Progress Relationship
- **Indicator**: High expenditure compared to physical progress.
- **Example**: `(cumulative_expenditure / original_cost) * 100 > physical_progress + 20%`
- **Why it's a risk**: If a project has spent 80% of its budget but is only 30% physically complete, a severe cost overrun is almost mathematically guaranteed.

### Large Cost Increase (Exploratory)
- **Indicator**: `cost_overrun_percent > 50%`
- **Why it's a risk**: Extreme overruns often indicate systemic issues (e.g., major scope changes, severe delays causing material inflation, or land acquisition failures) rather than minor estimation errors.

## 2. Schedule & Execution Risk Indicators

### Stagnation Near Completion
- **Indicator**: `physical_progress >= 90%` AND project is past its `original_completion_date`.
- **Why it's a risk**: Projects often stall at the 90-99% mark due to final regulatory clearances (e.g., environmental, safety certifications for railways/airports), testing failures, or contractor disputes.

### Delayed Start
- **Indicator**: Time between `approval_date` and `start_date` > 12 months.
- **Why it's a risk**: Prolonged delays before breaking ground often point to intractable land acquisition, funding, or initial clearance issues, setting a precedent for poor execution.

### Large Schedule Difference
- **Indicator**: `time_overrun_months > original_duration_months`
- **Why it's a risk**: If a project takes more than double its originally planned time, the initial feasibility study was likely flawed, or external macro factors have severely impacted it.

## 3. Structural Risk Indicators

### Multi-State Complexity
- **Indicator**: `state` contains "Multi-State" or lists more than 2 states.
- **Why it's a risk**: Cross-border infrastructure (like long railway lines or pipelines) requires coordination across multiple state governments, multiplying land acquisition and regulatory friction.

### Agency Concentration Risk
- **Indicator**: An agency has > 50% of its portfolio in delay/overrun.
- **Why it's a risk**: Indicates institutional bottlenecks (lack of funds, poor project management capacity) rather than project-specific bad luck.
