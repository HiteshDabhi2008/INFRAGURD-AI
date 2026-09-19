# InfraGuard-AI — Monthly Project Updates System

## 1. Overview & Architecture

The **Monthly Project Data Entry & Snapshot System** enables authorized government officers (MoSPI/IPMD Administrators, Ministry Authorities, Department Authorities, and Agency Authorities) to record monthly progress reports for infrastructure projects in a non-destructive manner.

Each entry generates a month-indexed snapshot, recalculates project features, triggers real-time re-evaluation of Machine Learning models (M3 Cost Overrun & M4 Time Delay), runs the M5 Multi-Factor Risk Engine, upserts persistent risk assessments and predictions, and logs a tamper-evident audit trail.

---

## 2. User Flow & Key Capabilities

1. **Autocomplete Search**:
   - Authorized users search by Project ID, MoSPI Code, Project Name, or Implementing Agency.
   - Selecting a project auto-populates sanctioned cost, original cost, approval date, sector, state, and ministry.

2. **Data Entry Fields**:
   - **Reporting Month**: Month identifier (e.g., `August 2026`, `September 2026`).
   - **Physical Progress**: Execution progress percentage ($0.0\% - 100.0\%$) with live progress-bar preview.
   - **Cumulative Expenditure**: Total capital spent up to the reporting month ($\ge 0$, in ₹ Crore) with dynamic sanction utilization ratio calculation.
   - **Project Status**: Status selection (`On Schedule`, `Delayed`, `Critical`, `Ahead of Schedule`, `Under Review`, `Completed`).
   - **Revised Cost (Optional)**: Sanctioned revised cost (₹ Cr).
   - **Revised Completion Date (Optional)**: Revised target commissioning date.
   - **Official Remarks**: Field-level notes on land acquisition, environmental clearances, contractor performance, and site milestones.

3. **Duplicate Detection & Non-Destructive Update**:
   - If a snapshot for the selected project and month already exists, the system flags a **409 Conflict** with an informative banner.
   - Users can choose:
     - **[ View Existing Data ]**: Review what is currently stored in the database.
     - **[ Edit Existing Data ]**: In-place edit with `allow_edit: true`, preserving history without overwriting prior months.

4. **Real-Time ML Re-Evaluation**:
   - Automatically recalculates `ProjectFeature` (cost change %, progress gap, expenditure ratio).
   - Evaluates:
     - **M3 (Cost Model)**: Expected cost overrun percentage and risk tier.
     - **M4 (Time Model)**: Overrun probability and predicted delay months.
     - **M5 (Risk Engine)**: Aggregates risk score ($0-100$), overall risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and early warning detection.
   - Persists results to `risk_assessments` and `ml_predictions` tables.

---

## 3. Security & Role-Based Access Control (RBAC)

| Role | Permissions |
| :--- | :--- |
| **Super Admin** | Full access to all projects, can add and edit monthly data. |
| **MoSPI / IPMD Admin** | National oversight, can add and edit monthly data across all sectors. |
| **Ministry Authority** | Scoped to projects belonging to their specific ministry. |
| **Department Authority** | Scoped to projects belonging to their department. |
| **Agency Authority** | Scoped to projects implemented by their agency (e.g., NHAI, RVNL, AAI). |
| **Viewer / Auditor** | **Read-Only**: Can view snapshots and predictions; submission is strictly restricted with HTTP 403. |

---

## 4. API Specification

### `POST /api/projects/{project_code}/monthly-update`
**Request Payload:**
```json
{
  "report_month": "August 2026",
  "physical_progress": 85.5,
  "cumulative_expenditure": 195.0,
  "project_status": "Ongoing",
  "revised_cost": 265.91,
  "revised_completion_date": "2026-12-31",
  "remarks": "Terminal structural glass installed. Runway electrical work underway.",
  "allow_edit": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Monthly update for August 2026 successfully saved.",
  "snapshot": {
    "id": 7101,
    "project_code": "612786",
    "report_month": "August 2026",
    "physical_progress": 85.5,
    "cumulative_expenditure": 195.0,
    "project_status": "Ongoing",
    "created_by": "admin@infraguard.local",
    "created_at": "2026-09-18T13:36:14.830261"
  },
  "risk_assessment": {
    "risk_score": 30,
    "overall_risk": "MEDIUM",
    "warnings": ["High Time Overrun Predicted"]
  },
  "predictions": {
    "cost_risk_level": "LOW",
    "predicted_cost_overrun": 0.9,
    "time_risk_level": "HIGH",
    "predicted_time_months": 0.0
  }
}
```

