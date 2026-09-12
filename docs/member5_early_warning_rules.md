# Early-Warning Rule Ideas (Member 5)

This document outlines prototype logic rules for the InfraGuard-AI Early Warning System. These rules are designed to flag projects *before* they officially declare massive overruns, relying on implementation-time snapshot data.

*Disclaimer: These are analytical prototype rules, not official MoSPI heuristics.*

## Proposed Prototype Rules

### 1. High Expenditure with Low Physical Progress
- **Logic**: `safe_expenditure_percent > 30%` AND `physical_progress < 5%`
- **Rationale**: If a third of the budget is spent but physical progress has barely started, the project is likely hemorrhaging funds on administration, land disputes, or mobilization advances without yielding physical assets.

### 2. Significant Cost Escalation
- **Logic**: `cost_overrun_percent > 20%`
- **Rationale**: Any project exceeding 20% of its original budget has likely encountered systemic estimation failures or major scope changes and requires immediate audit.

### 3. Approaching Planned Completion with Insufficient Progress
- **Logic**: `Project Age / Original Duration > 80%` AND `physical_progress < 50%`
- **Rationale**: If a project has consumed 80% of its allowed time but is less than half finished, a severe schedule extension is mathematically inevitable.

### 4. Severe Stalling (Velocity Warning)
- **Logic**: *(Requires time-series data)* `physical_progress_change_over_3_months == 0%`
- **Rationale**: A project that reports the exact same physical progress for three consecutive months is effectively stalled on the ground, likely due to legal stays, contractor bankruptcy, or extreme weather.

### 5. Multi-dimensional Failure (The "Red Flag" Rule)
- **Logic**: `cost_risk_score >= 2` AND `time_risk_score >= 2` AND `progress_risk_score >= 2`
- **Rationale**: Projects that trigger multiple risk indicators simultaneously are the highest priority for intervention. They are over budget, delayed, AND structurally misaligned in their expenditure/progress ratio.
