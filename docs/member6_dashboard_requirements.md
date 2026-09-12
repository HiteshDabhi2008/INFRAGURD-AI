# Dashboard Requirements (Member 6)

This document outlines the requirements and user flow for the InfraGuard-AI integrated project-monitoring platform.

## 1. User Flow

The final application will follow a hierarchical drill-down structure, allowing MoSPI officials to go from a macro portfolio view down to a specific project and its AI-generated risk profile.

`Login`
   → `Dashboard`
      → `Portfolio Overview`
      → `Ministry/Sector/State Filters`
      → `Project List`
         → `Project Details`
            → `Cost & Time Overrun Analytics`
            → `Risk Score & Early Warning`
            → `PAIMANA AI Assistant (Project Context)`

## 2. Portfolio KPIs (Top-Level)

The main dashboard must display the following Key Performance Indicators (KPIs):
- **Total Projects**: (Count of all projects).
- **Ongoing Projects**: (Currently active).
- **High-Risk Projects**: (Projects flagged as HIGH by Member 5's engine).
- **Critical Projects**: (Projects flagged as CRITICAL by Member 5's engine).
- **Total Original Cost**: Sum of original budgets.
- **Total Revised Cost**: Sum of current revised budgets.
- **Total Expenditure**: Total money spent to date.
- **Average Physical Progress**: Median/Mean physical progress across the portfolio.

## 3. Global Filters

To allow slicing of the dataset, the dashboard will include a persistent sidebar or top bar with these filters:
- **Project ID**
- **Project Name** (Search bar)
- **Ministry**
- **Agency**
- **State**
- **Sector**

## 4. Visualizations

The dashboard will contain a central analytics area featuring:
- **Projects by Ministry/Sector/State**: Bar charts.
- **Original vs Revised Cost**: Scatter plot (Member 3 output).
- **Expenditure vs Physical Progress**: Scatter plot showing the "Progress Gap" (Member 5 output).
- **Risk Distribution**: Pie/Donut chart of Risk Categories (LOW, MEDIUM, HIGH, CRITICAL).
- **Top High-Risk Projects**: A sortable data table highlighting the most vulnerable projects.

## 5. Project Detail Page

Clicking a project in the list or table will open its dedicated page, displaying:
### Identity
- Project Name, ID, Ministry, Agency, State, Sector.

### Financial Health
- Original Cost, Revised Cost, Cost Overrun %, Cumulative Expenditure, Expenditure %.

### Schedule Health
- Approval Date, Original Completion Date, Revised Completion Date, Time Overrun.

### Execution Health
- Physical Progress (%), Progress Gap.

### AI Risk Profile
- **Cost Risk Score** (Member 3 & 5)
- **Time Risk Score** (Member 4 & 5)
- **Overall Risk Score** (Member 5)
- **Early Warnings Triggered**: (e.g., "High Expenditure with Low Physical Progress").

## 6. Temporal Limitations

**Critical Note for the UI**: The dashboard must explicitly display a disclaimer indicating that the data is based on the **July 2026 PAIMANA Snapshot**. Because it relies on a single static snapshot, early warning alerts are based on current accumulated deviations, not longitudinal velocity forecasting.
