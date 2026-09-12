# Cost Target Definition (Member 3)

This document evaluates potential Machine Learning targets for the InfraGuard-AI Cost Prediction model based on the PAIMANA July 2026 dataset.

## Target Options Investigated

### 1. Classification: `cost_overrun_flag` (Binary)
- **Definition**: `1` if `revised_cost > original_cost`, else `0`.
- **Current Data Split**: ~27% of projects (482) experienced a cost overrun, while ~73% (1293) did not.
- **Pros**:
  - Extremely clear operational meaning (Over budget vs On budget).
  - Handles the extreme outliers well (a 2000% overrun is simply classified as `1`, preventing severe model skew).
  - Easier to achieve high accuracy/ROC-AUC in early models.
  - Good for early warning ("Will this project go over budget?").
- **Cons**:
  - Loses severity information (a ₹10,000 Cr overrun is treated the same as a ₹10 Cr overrun).

### 2. Regression: `cost_overrun_percent` (Continuous)
- **Definition**: `(revised_cost - original_cost) / original_cost * 100`.
- **Distribution**: Highly skewed. The median overrun (for projects with >0% overrun) is roughly 25-30%, but extreme outliers reach up to 1,921%.
- **Pros**:
  - Provides the magnitude of the financial risk.
  - More useful for budget allocation and portfolio management.
- **Cons**:
  - Very hard to predict accurately due to extreme right-tail outliers.
  - Requires complex outlier handling (capping, log transformations, or robust loss functions like Huber Loss).

### 3. Regression: Absolute `cost_change` (Continuous, ₹ Crore)
- **Definition**: `revised_cost - original_cost`.
- **Pros**: Directly maps to monetary loss.
- **Cons**: Heavily biased by the `original_cost` of the project. A 1% overrun on a ₹10,000 Cr project dwarfs a 100% overrun on a ₹10 Cr project. This makes model training unstable.

---

## Final Target Recommendation

For the **Day-2 initial model**, the recommended target is:
**Binary Classification: `cost_overrun_flag`**

**Reasoning**: 
In the context of an early-warning system (Problem Statement 26103), identifying *which* projects are at risk of breaking their budget is the primary goal. The binary target is robust against the extreme outliers present in the PAIMANA dataset and allows us to establish a strong baseline model quickly using classifiers like Random Forest or XGBoost.

Once the classification model achieves satisfactory performance, a secondary **Regression Model** predicting `cost_overrun_percent` can be developed exclusively for the projects flagged as high-risk, effectively creating a two-stage hurdle model.
