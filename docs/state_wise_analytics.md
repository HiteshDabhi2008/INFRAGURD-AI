# InfraGuard-AI — State-Wise Project Intelligence & Geospatial Analytics

## 1. Overview & Architecture

The **State-Wise Infrastructure Intelligence Page** (`/dashboard/state`) provides interactive geospatial intelligence for monitoring central sector projects across all 36 States and Union Territories of India.

It is powered by a high-performance backend aggregation endpoint and renders an interactive choropleth map using a locally bundled GeoJSON boundary dataset (`/india.json`), completely eliminating external network dependencies.

---

## 2. Five Visualization Modes

Users can toggle dynamically between five analytical modes using the mode bar:

1. **Project Distribution**:
   - Total count of active infrastructure projects per state.
   - Choropleth Color Scale: Graduated Blue (`#eff6ff` to `#1d4ed8`).
2. **High Risk Projects**:
   - Number of projects flagged with High or Critical risk in each state.
   - Choropleth Color Scale: Warm Orange/Red (`#ffedd5` to `#9a3412`).
3. **Critical Projects**:
   - Number of projects in the severe risk tier ($\text{Score} \ge 75$ or `CRITICAL`).
   - Choropleth Color Scale: Deep Red/Burgundy (`#fee2e2` to `#7f1d1d`).
4. **Delayed Projects**:
   - Count of projects experiencing schedule delay ($\text{Time Overrun Months} > 0$).
   - Choropleth Color Scale: Amber/Gold (`#fef3c7` to `#78350f`).
5. **Average Physical Progress (%)**:
   - Average civil execution completion rate across all projects in the state.
   - Choropleth Color Scale: Emerald/Green (`#ecfdf5` to `#047857`).

---

## 3. Interactive Features & State Projects Drawer

- **Live Hover Tooltip**:
  - Displays State Name, Selected Mode Value, Total Projects, High/Critical Risk Count, Delayed Projects Count, Sanctioned Capital, and Average Progress %.
- **Click-to-Inspect Drawer**:
  - Clicking any state opens a sliding right-hand drawer displaying that state's full project portfolio.
  - State Project Table displays: Project Code, Name, Agency, Sector, Sanctioned Cost, Progress %, Time Delay, and Risk Badge.
  - Action Buttons:
    - `[ View ]`: Navigates to `/dashboard/projects/{code}`.
    - `[ Risk ]`: Navigates directly to the deep risk assessment page `/dashboard/projects/{code}/risk`.

---

## 4. Analytical Charts (Recharts)

1. **Delay Analysis by State**: Bar chart comparing delayed project counts across top delayed states.
2. **Risk Category Distribution by State**: Stacked bar chart showing the composition of `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL` projects for top states.
3. **Top States by Project Volume**: Horizontal bar chart ranking states by central project density.
4. **Average Physical Execution Progress (%)**: Bar chart comparing completion percentage across leading states.
5. **State Capital Allocation vs Cumulative Expenditure**: Comparative bar chart of total sanctioned cost versus cumulative capital spent (in ₹ Crore).

---

## 5. API Endpoints

- `GET /api/analytics/state/map`: Aggregates national KPI metrics, per-state statistics, and top-10 chart datasets in a single optimized query.
- `GET /api/analytics/state/{state_name}/projects`: Returns all projects belonging to the specified state (including multi-state projects).

