# Proposed Risk Framework (Member 5)

This document outlines the proposed Risk Framework for the InfraGuard-AI project, serving as the analytical engine to flag vulnerable projects.

## Overall Concept

The risk of a project is a multidimensional vector. An infrastructure project may be entirely on schedule but massively over budget, or entirely on budget but completely stalled. Therefore, the Overall Project Risk must be a composite score.

```text
Cost Risk + Schedule Risk + Progress Risk + Macro Risk = Overall Project Risk
```

## 1. Cost Risk
- **Definition**: The probability or magnitude of a project exceeding its `original_cost`.
- **Inputs**: ML predictions from Member 3 (using features like `original_cost`, `agency`, `state`).
- **Retrospective Validation**: `cost_overrun_percent`.

## 2. Schedule Risk
- **Definition**: The probability or magnitude of a project missing its `original_completion_date`.
- **Inputs**: ML predictions from Member 4 (using features like `original_duration_months`, `state`, `agency`).
- **Retrospective Validation**: `time_overrun_percent`.

## 3. Progress Risk (Implementation Health)
- **Definition**: Financial and physical progress dissonance.
- **Inputs**: The `progress_gap` (`safe_expenditure_percent` minus `physical_progress`). If a project has spent 80% of its budget but only completed 10% of physical work, it faces an existential completion threat, regardless of ML forecasts.

## 4. Macro & Exogenous Risk (Future)
- **Definition**: External factors outside the immediate control of the agency.
- **Inputs**: Inflation indices, state-level land acquisition delays, weather anomalies.

## Prototype Outputs

The composite numerical score (0 to 9 in the prototype) is binned into four actionable categories:
- **LOW**: Project is proceeding largely according to plan.
- **MEDIUM**: Early signs of friction (e.g., minor delays, slight cost escalation).
- **HIGH**: Significant deviations in at least one major dimension (cost, time, or progress gap).
- **CRITICAL**: Systemic failure across multiple dimensions (e.g., severely over budget, severely delayed, AND physically stalled).

*Note: These thresholds are analytical prototypes and do NOT represent official MoSPI thresholds.*

## Temporal Limitation

**WARNING**: The current evaluation is based on a **single static snapshot** (July 2026).
- Currently, we can only evaluate the *accumulated* risk state of a project.
- To create a true **Predictive Early Warning System**, we require historical, longitudinal PAIMANA/OCMS monthly reports. This would allow us to calculate *velocity* (e.g., progress stalling over 3 consecutive months) and forecast future states before the delays manifest in the official "revised" numbers.
