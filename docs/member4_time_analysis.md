# Schedule / Time Analysis (Member 4)

This document details the exploratory data analysis (EDA) performed strictly on the schedule and time metrics of the PAIMANA July 2026 dataset.

## High-Level Schedule Statistics

Out of **1,775** ongoing projects:
- **Projects with a Schedule Extension (Delayed)**: 1,110 (62.5%)
- **Projects Strictly on Time**: 665 (37.5%)

*Observation: Time overruns are significantly more common than cost overruns (62.5% delayed vs 27.2% over-budget). This suggests that agencies prefer to extend timelines rather than authorize additional funds.*

## Time Overrun Magnitude

For the 1,110 projects experiencing a schedule extension (`time_overrun_months > 0`):
- **Mean Time Overrun**: 30.23 Months
- **Median Time Overrun**: 22.96 Months
- **Maximum Time Overrun**: 299.96 Months (~25 years)
- **Minimum Time Overrun**: 0.92 Months

The distribution has a heavy right tail, meaning while the typical project is delayed by 1 to 3 years, a subset of projects is stalled indefinitely, heavily skewing the average.

*(See `outputs/member4_time_overrun_distribution.png`)*

## Original Duration vs Physical Progress

Analyzing `original_duration_months` against `physical_progress`:
- A clear separation emerges. Projects with short original durations (12-36 months) often have high physical progress, even if they are slightly delayed.
- Massive infrastructure projects (planned for 60-120 months) often stall at low physical progress (< 30%) and accumulate severe delays.
- There are multiple projects completely stalled at 0% physical progress but with massive time overruns. These are likely stuck in the pre-construction phase (land acquisition, clearances).

*(See `outputs/member4_duration_vs_progress.png`)*

## State and Agency Impact

### By State
Schedule delays vary massively across states. 
States with dense urban environments (complex utility shifting/land acquisition) or difficult terrain (Himalayas, North East) display significantly wider IQR (Interquartile Ranges) and higher median delays.
*(See `outputs/member4_time_overrun_by_state.png`)*

### By Agency
As with cost overruns, the executing agency is highly correlated with schedule delays. Agencies managing complex linear infrastructure (like Railways or National Highways) face much higher median delays than agencies building localized assets (like hospitals or specific campus buildings).
*(See `outputs/member4_time_overrun_by_agency.png`)*

## Temporal Limitation Warning

**CRITICAL LIMITATION**: The July 2026 dataset is a **single monthly snapshot**. 

Because we only have data from July 2026, we see the *current* state of delays. We do not have the timeline of *when* the delay was officially recognized.
- For a true "Predictive Early Warning System," we need to train a model on historical sequences (e.g., watching a project go from 10% progress in Jan 2025, to 12% in June 2025, and predicting the delay).
- Without time-series data, our model will perform **Retrospective Pattern Recognition**. It will learn that "Projects in State X by Agency Y with Original Cost Z tend to be delayed," but it cannot track velocity-based stalling.

We strongly recommend aggregating past monthly MoSPI/OCMS reports (e.g., 2020 through 2025) to create a panel dataset for robust future-oriented predictions.
