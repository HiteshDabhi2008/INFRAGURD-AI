# Cost Analysis (Member 3)

This document details the exploratory data analysis (EDA) performed strictly on the cost metrics of the PAIMANA July 2026 dataset.

## High-Level Cost Statistics

Out of **1,775** ongoing projects:
- **Projects with a cost overrun**: 482 (27.2%)
- **Projects strictly on original budget**: 977 (55.0%)
- **Projects with a cost decrease**: 316 (17.8%)

*Note: Cost decreases usually occur due to descoping of a project or savings in final contract awards.*

## Cost Overrun Magnitude

For the 482 projects experiencing a cost overrun (where `revised_cost > original_cost`), the distribution is highly skewed:
- **Mean Overrun %**: 50.68%
- **Median Overrun %**: 23.47%
- **Maximum Overrun %**: 1921.01%
- **Absolute Mean Overrun**: ₹191.83 Crore per project across the entire portfolio.

The enormous difference between the mean (50.6%) and the median (23.5%) confirms that a small number of extreme outlier projects are heavily skewing the dataset. 

*(See `outputs/member3_cost_overrun_distribution.png`)*

## Original vs Revised Cost Relationship

Plotting `original_cost` against `revised_cost` reveals:
- Most projects tightly hug the $x=y$ line (meaning revised cost = original cost).
- The outliers that deviate above the line represent the cost overruns.
- Notably, mega-projects (original cost > ₹10,000 Crore) tend to have smaller *percentage* overruns but massive *absolute* monetary overruns. Smaller projects are more susceptible to extreme percentage overruns (e.g., a ₹100 Cr project jumping to ₹400 Cr).

*(See `outputs/member3_original_vs_revised_cost.png`)*

## State and Agency Analysis

### By State
Cost overruns are not evenly distributed geographically.
Certain states exhibit a much higher propensity for cost overruns. This could be due to systemic issues like:
- Difficult terrain (e.g., Himalayan states).
- Complex land acquisition laws or local resistance.
- State-level administrative bottlenecks.

*(See `outputs/member3_cost_overrun_by_state.png`)*

### By Agency
Agencies manage wildly different portfolios. An agency building small rural roads will have a different risk profile than an agency building nuclear power plants or metro rails. 
The analysis shows that specific agencies have more than 50% of their projects experiencing cost overruns. This makes `agency` a critically important feature for the ML model.

*(See `outputs/member3_cost_overrun_by_agency.png`)*

## Temporal Limitation Warning

**CRITICAL LIMITATION**: The July 2026 dataset represents a **single static snapshot**. 
- We can see that a project is 80% complete and 20% over budget *today*.
- We **cannot** see *when* that budget increase occurred (e.g., did it happen at 10% progress or 75% progress?).

For a true "Early Warning System" that predicts future failures, a model needs historical time-series data (e.g., training on Jan 2025 data to predict July 2026 outcomes). 

With single-snapshot data, our Day-2 ML model will essentially be performing **retrospective pattern recognition** (finding the characteristics of projects that have *already* failed) rather than true future forecasting. To build a true predictive engine, MoSPI historical reports must be aggregated to form a longitudinal dataset.
