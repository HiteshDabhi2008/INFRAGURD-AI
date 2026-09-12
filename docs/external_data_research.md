# External Data Research

To improve predictions beyond the PAIMANA snapshot, Member 3 and 4 should consider integrating these freely available external data sources. 

> **Important**: Do not claim these variables exist in PAIMANA. They must be joined from external datasets using `state`, `approval_date`, or `agency`.

## 1. Wholesale Price Index (WPI) / Inflation Data
- **Source**: Office of the Economic Adviser (DPIIT) / RBI / data.gov.in
- **Variable**: Construction material inflation indices (Steel, Cement, Bitumen).
- **Why useful**: Severe inflation spikes during a project's execution window directly cause cost overruns.
- **Availability**: Monthly data is freely available.
- **Historical coverage**: Decades.
- **Possible join key**: `approval_date` / current month.
- **API availability**: RBI Data DBIE API / data.gov.in APIs.
- **Free/open status**: Free & Open.

## 2. Weather & Climate Data (Monsoon impact)
- **Source**: Indian Meteorological Department (IMD)
- **Variable**: Rainfall deviation from normal, extreme weather events.
- **Why useful**: Unusually heavy monsoons halt construction (especially earthworks for roads/railways), directly causing time overruns.
- **Availability**: District/State level monthly rainfall data.
- **Historical coverage**: Excellent (100+ years).
- **Possible join key**: `state` + Execution year/months.
- **API availability**: IMD data portal (CSV downloads).
- **Free/open status**: Free.

## 3. Land Acquisition & Forest Clearance Data
- **Source**: PARIVESH Portal (Ministry of Environment, Forest and Climate Change)
- **Variable**: Pending environmental/forest clearance timelines.
- **Why useful**: A massive predictor of time delays. If a project in a specific state/sector is waiting on PARIVESH, it will stall.
- **Availability**: Public dashboard available, might require scraping or manual export.
- **Possible join key**: `project_name` / `agency` / `state`.
- **Free/open status**: Public but no clean API.

## 4. State-level Ease of Doing Business / Infrastructure Index
- **Source**: DPIIT (BRAP - Business Reforms Action Plan)
- **Variable**: State ranking in ease of doing business / land acquisition efficiency.
- **Why useful**: Explains why a highway in State A finishes on time while a similar highway in State B is delayed by 3 years.
- **Availability**: Annual rankings.
- **Possible join key**: `state`.
- **API availability**: CSV/PDF downloads.
- **Free/open status**: Free.
