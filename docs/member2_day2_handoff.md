# Member 2 Day 2 Handoff Document

**To:** Member 3 (Cost Modeling), Member 4 (Time Modeling), Member 5 (Risk Engine)
**From:** Member 2 (Research & EDA)
**Date:** July 2026 Snapshot context

## 1. Work Completed

*   **EDA Script:** Created and executed `src/data/eda_member2.py`.
*   **Visualizations:** Generated 9 key plots in `outputs/member2/` mapping costs, progress, sectors, agencies, and states.
*   **Feature Mapping:** Updated `docs/ml_feature_map.md` with safe inputs, identifying severe data leakage risks in `expenditure_percent` and `progress_gap` as previously defined. I added `safe_expenditure_percent` and `safe_progress_gap` as safe alternatives.
*   **External Data:** Documented necessary macro-economic external datasets (Inflation, Weather, Budget) in `docs/external_data_research.md`.
*   **Feature Recommendations:** Compiled ML modeling recommendations in `docs/feature_recommendations.md`.

## 2. Key Insights for Modeling Teams

*   **Systemic Multi-State Risk:** Multi-state projects account for the most severe cost escalations (e.g., MP/Maharashtra at 230%, Gujarat/MP at 966%). A categorical indicator or systemic penalty is highly recommended for these.
*   **Sector Nuances:** Water Resources have average cost escalations of 137%. Conversely, Roads & Highways average only 1.2% cost escalation, despite making up a large volume of the dataset.
*   **Agency Performance:** Be sure to utilize the `agency` feature. Specific agencies like *Medical Education, Ministry of Health* (31.5% escalation) show structural delays, whereas *NHIDCL* is relatively stable.
*   **Data Leakage Warning:** Do not use `revised_cost`, `cost_change`, or `revised_completion_date` as inputs! If you use derived features like `expenditure_percent`, ensure you are dividing by the `original_cost`, otherwise you are leaking the outcome into your predictors.

## 3. Next Steps for Members 3, 4, 5

*   **Member 1:** Please fetch the WPI and Rainfall datasets mentioned in `docs/external_data_research.md`.
*   **Member 3 (Cost) & Member 4 (Time):** Review `docs/feature_recommendations.md` and `docs/ml_feature_map.md` to select safe inputs for your initial model baselines.
*   **Member 5 (Risk Engine):** Begin structuring the Risk Engine to incorporate the Time and Cost model outputs, while synthesizing the KRIs identified in the recommendations document.

All EDA visuals are available in the `outputs/member2/` folder. Use these to communicate data issues or model baselines during our presentations.
