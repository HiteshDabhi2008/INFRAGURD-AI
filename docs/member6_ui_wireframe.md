# UI Wireframe (Member 6)

This document provides a text-based layout representation of the InfraGuard-AI Dashboard for Day 2 implementation.

## Layout Structure: Main Dashboard

```text
====================================================================================================
[LOGO] InfraGuard-AI                     PAIMANA Snapshot: July 2026                     [PROFILE]
====================================================================================================
[ GLOBAL FILTERS ]
| Ministry: [Dropdown]  | Sector: [Dropdown] | State: [Dropdown] | Agency: [Dropdown] |
| Search Project ID / Name: [Text Box]                                                |
====================================================================================================
[ KPI CARDS ]
+----------------------+ +----------------------+ +----------------------+ +----------------------+
| Total Projects       | | Ongoing            | | HIGH RISK            | | CRITICAL RISK        |
| 1,775                | | 1,775              | | 420                  | | 106                  |
+----------------------+ +----------------------+ +----------------------+ +----------------------+
+----------------------+ +----------------------+ +----------------------+ +----------------------+
| Total Original Cost  | | Total Revised Cost | | Total Expenditure    | | Avg Physical Progress|
| ₹1,500,000 Cr        | | ₹1,800,000 Cr      | | ₹900,000 Cr          | | 45.2%                |
+----------------------+ +----------------------+ +----------------------+ +----------------------+
====================================================================================================
[ MAIN ANALYTICS ]
+------------------------------------------+ +---------------------------------------------------+
| Risk Distribution (Pie Chart)            | | Expenditure vs Progress Gap (Scatter Plot)          |
| 🟢 LOW: 50%   🟡 MED: 20%                | | y: Expenditure %                                  |
| 🟠 HIGH: 24%  🔴 CRIT: 6%                | | x: Physical Progress %                            |
+------------------------------------------+ +---------------------------------------------------+
+------------------------------------------+ +---------------------------------------------------+
| Top High-Risk Agencies (Bar Chart)       | | Cost Overrun vs Original Cost (Scatter Plot)      |
| Agency X | ▀▀▀▀▀▀▀▀▀                     | | Highlights mega-projects with severe overruns     |
| Agency Y | ▀▀▀▀▀                         | |                                                 |
+------------------------------------------+ +---------------------------------------------------+
====================================================================================================
[ CRITICAL PROJECT WATCHLIST ]
| ID     | Project Name            | State  | Agency | Cost Overrun | Time Overrun | Risk Level  |
|--------|-------------------------|--------|--------|--------------|--------------|-------------|
| P1029  | Highway Expansion A     | UP     | NHAI   | 145%         | 48 Months    | 🔴 CRITICAL |
| P9042  | Metro Phase 2           | MH     | MMRDA  | 80%          | 12 Months    | 🔴 CRITICAL |
| P1124  | Thermal Plant B         | MP     | NTPC   | 10%          | 120 Months   | 🟠 HIGH     |
====================================================================================================
[ 🤖 PAIMANA AI ASSISTANT (Chatbot Floating Widget - Bottom Right) ]
```

## Layout Structure: Project Detail Page Modal

```text
====================================================================================================
⬅ Back to Dashboard                          PROJECT PROFILE
====================================================================================================
Project Name: Highway Expansion A (P1029)
State: Uttar Pradesh | Agency: NHAI | Sector: Road Transport
====================================================================================================
[ AI RISK PROFILE ]
Overall Risk: 🔴 CRITICAL
Cost Risk: 🔴 HIGH (Model Probability: 89%)
Time Risk: 🔴 HIGH (Model Probability: 95%)

⚠️ EARLY WARNING TRIGGERS:
- [Triggered] High Expenditure with Low Physical Progress (Gap = 45%)
- [Triggered] Significant Cost Escalation (>20%)
====================================================================================================
[ FINANCIALS ]                             [ SCHEDULE ]
Original Cost: ₹1,000 Cr                 Approval Date: 01-Jan-2020
Revised Cost: ₹2,450 Cr                  Original Completion: 01-Jan-2023
Cumulative Expenditure: ₹800 Cr          Revised Completion: 01-Jan-2027
Cost Overrun: 145%                       Time Overrun: 48 Months
Expenditure % (of Orig): 80%
====================================================================================================
[ EXECUTION ]
Physical Progress: 35%
Progress Gap: 45% (Expenditure % - Physical Progress %)
====================================================================================================
```
