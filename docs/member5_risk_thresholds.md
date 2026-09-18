# Prototype / Proposed Risk Thresholds (Member 5)

> **IMPORTANT**: The thresholds and categorizations defined in this document are **Prototype / Proposed Risk Thresholds** developed for the InfraGuard-AI proof-of-concept. They should **NOT** be presented as official MoSPI/IPMD thresholds unless explicitly confirmed by official sources.

## Methodology

The Overall Risk Score is calculated using a point-based system that integrates the predictive outputs from Member 3 (Cost Risk) and Member 4 (Time Risk) with deterministic project progression metrics (Financial & Physical).

### Point Allocation System

1. **Cost Predictive Risk (from Member 3 Model)**
   - `HIGH` probability (>70%) = **+2 Points**
   - `MEDIUM` probability (40% - 70%) = **+1 Point**
   - `LOW` probability (<40%) = **0 Points**

2. **Time Predictive Risk (from Member 4 Model)**
   - `HIGH` probability (>70%) = **+2 Points**
   - `MEDIUM` probability (40% - 70%) = **+1 Point**
   - `LOW` probability (<40%) = **0 Points**

3. **Progress Mismatch / Financial Gap (Deterministic)**
   - Gap (`safe_expenditure_percent` - `physical_progress`) > 30% = **+2 Points**
   - Gap (`safe_expenditure_percent` - `physical_progress`) > 15% = **+1 Point**
   - Otherwise = **0 Points**

## Overall Risk Categories

Based on the total points accumulated, projects are classified into the following four categories:

| Category | Points | Definition | Action Required |
|----------|--------|------------|-----------------|
| **LOW** | 0 - 1 | The project is tracking well according to schedule and budget, with no significant warnings triggered by predictive models. | Routine monitoring. |
| **MEDIUM** | 2 | Moderate indicators of potential overrun. Often triggered by an isolated issue (e.g., a medium time risk or a slight progress mismatch). | Proactive review of scheduling or finances. |
| **HIGH** | 3 - 4 | Strong indicators of either severe cost/time overruns or a confluence of moderate risks. | Urgent management review and mitigation planning. |
| **CRITICAL** | 5+ | Severe multi-dimensional risks detected. High likelihood of simultaneous extreme cost and time overruns accompanied by heavy financial-physical mismatch. | Immediate executive intervention required. |

## Early Warning Triggers

In addition to the overall risk category, specific Early Warning Messages are generated when exact conditions are met:
* **COST_RISK_HIGH**: Member 3's model estimates >70% chance of cost overrun.
* **TIME_RISK_HIGH**: Member 4's model estimates >70% chance of schedule delay.
* **EXPENDITURE_MISMATCH**: Expenditure percentage exceeds physical progress by more than 20 percentage points.
* **STAGNATION_NEAR_DEADLINE**: More than 80% of original planned duration has elapsed, but physical progress is below 50%.
* **MULTIPLE_INDICATORS**: 3 or more independent warnings are triggered simultaneously.
