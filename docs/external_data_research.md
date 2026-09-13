# External Data Research for Predictive Models

To improve the accuracy of our machine learning models for cost overruns and time delays, we can incorporate external datasets. These datasets can provide macro-economic, environmental, and geo-political context that systemic delays and cost escalations often depend on.

## 1. Macro-Economic Indicators (Inflation & Material Costs)

Cost escalations are frequently driven by inflation in raw material prices (steel, cement, fuel, etc.).

### Suggested Datasets:
*   **Wholesale Price Index (WPI)**: Track the WPI for core infrastructure materials.
    *   **Source**: Office of the Economic Adviser (OEA), Ministry of Commerce and Industry, India.
    *   **Frequency**: Monthly
    *   **Application**: Create an `inflation_index` feature from the `approval_date` to the current `report_month`.
*   **Consumer Price Index (CPI)**: Proxy for labor cost inflation.
    *   **Source**: MoSPI
    *   **Application**: Can be used to adjust the baseline `original_cost` to present value to see if the overrun is purely inflationary or due to mismanagement.

## 2. Environmental and Weather Data

Infrastructure projects (especially roads, railways, and water resources) are highly susceptible to weather disruptions (e.g., heavy monsoons).

### Suggested Datasets:
*   **Rainfall / Monsoon Data**:
    *   **Source**: India Meteorological Department (IMD) or OpenWeatherMap API.
    *   **Frequency**: Monthly/Seasonal by State/Sub-division.
    *   **Application**: Create a `weather_disruption_index` for the specific `state` during the project's active duration. High rainfall regions (like North-East or coastal states) might have structural delays.

## 3. Geo-Spatial and Land Acquisition Data

Delays in land acquisition and environmental clearances are the top reasons for project delays in India.

### Suggested Datasets:
*   **Forest Cover & Environmental Zones**:
    *   **Source**: Forest Survey of India (FSI) or Bhuvan (ISRO).
    *   **Application**: If a project passes through a dense forest or eco-sensitive zone, the probability of delay increases.
*   **State-level Ease of Doing Business / Land Acquisition Complexity**:
    *   **Source**: DPIIT (Department for Promotion of Industry and Internal Trade).
    *   **Application**: Provides a categorical risk score for the `state`. Multi-state projects have inherently higher complexity (as seen in our EDA where multi-state projects had up to 966% cost escalation).

## 4. Financial & Budgetary Data

*   **Union Budget Allocations**:
    *   **Source**: Ministry of Finance, India.
    *   **Application**: Track if the specific sector/ministry received adequate budget allocations in the years the project was active. Budget crunches lead to paused projects.

## Action Items for Data Engineering (Member 1)
1. Fetch historical monthly WPI indices for "All Commodities" and map them to the project timeline (`approval_date` to `report_month`).
2. Fetch state-wise average annual rainfall deviations to flag regions with extreme weather during the project tenure.
