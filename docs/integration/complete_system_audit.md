# InfraGuard-AI Complete System Audit

Audit date: 2026-09-16

This audit records the repository state before integration work. Claims below are based on source inspection and artifact inventory; a component is marked unverified until an executable check succeeds.

## Executive Findings

- The frontend is a React/Vite application with dashboard routes, but the dashboard, project directory, project intelligence page, and AI panel use hard-coded demo values and arrays.
- The frontend API client only configures Axios. It does not expose project, analytics, ML, reports, or AI methods.
- The FastAPI application has login, current-user, projects, history, dashboard stats, and AI routes under `/api`. It does not yet expose the requested analytics, search, mutation, ML, risk, report, or monthly-update contracts.
- Two separate local database paths are present: SQLAlchemy defaults to `data/processed/infraguard.db`, while `src/data/repository.py` reads `data/processed/database.sqlite`. This can make the API read a different dataset from the database used for writes.
- The repository's project list joins every snapshot and feature row without selecting the latest snapshot, so list values can be duplicated or stale.
- Cost and time model artifacts are present. Model loading and real inference have not yet been verified through the FastAPI API.
- The AI service can fall back to deterministic generated text when Groq is missing or errors. That violates the integration requirement that failed Groq calls must be surfaced as errors rather than presented as AI output.
- The Tailwind 4/PostCSS configuration is internally aligned (`@tailwindcss/postcss` plus `@import "tailwindcss"`), but the current build could not be executed in this environment because PowerShell blocked the npm command.

## Existing Components

### Frontend

- Routes: landing, login, registration, dashboard, ministry, sector, state, projects, project intelligence, new projects, and AI assistant.
- Shared layout: sidebar, header, auth context, Axios client.
- Charts: Recharts components in dashboard and project intelligence.
- Existing styling: Tailwind 4 utilities with government color extensions.

### Backend

- FastAPI application in `backend/main.py`.
- SQLAlchemy models for users, roles, projects, snapshots, features, predictions, risk assessments, audit logs, and uploaded files.
- JWT authentication and role/scope helpers in `backend/auth.py`.
- Local SQLite fallback in `backend/database.py`.
- AI, ingestion, and ML service modules.

### Data and Models

- Local data includes `master_projects.csv`, cleaned and historical PAIMANA CSVs, ML datasets, project features, `database.sqlite`, and `infraguard.db`.
- Model artifacts include cost classifier/regressor/prediction model and time classifier/regressor/prediction model, plus feature schema JSON files.
- Risk engine modules exist under `src/risk/`; the API does not yet expose a dedicated risk endpoint.

## Disconnected or Hard-Coded Surfaces

| Surface | Current state | Required integration |
|---|---|---|
| Dashboard KPIs | Hard-coded values in `MainDashboard.tsx` | Backend aggregate endpoint |
| Risk chart | Hard-coded distribution | Persisted/calculated risk assessments |
| Expenditure chart | Hard-coded monthly array | Snapshot aggregation endpoint |
| Priority projects | Two hard-coded demo rows | Authorized project/risk query |
| Project directory | Six hard-coded projects, decorative filters/export | Paginated query, search, filters, export action |
| Project intelligence | Hard-coded project, history, predictions, warnings, chat | Project detail, history, ML, risk, AI APIs |
| Header search | Input has no handler | Backend-powered project search |
| AI suggestions | Buttons have no handler | POST `/api/ai/chat` with project context |
| Reports and analytics navigation | Routes are referenced but not implemented | Implement route or disable until available |

## API Inventory

Existing routes:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/ai/chat`
- `GET /api/projects`
- `GET /api/projects/{project_code}`
- `GET /api/projects/{project_code}/history`
- `GET /api/dashboard/stats`

Missing or incomplete contracts:

- Health endpoint
- Backend-powered search and combined project filters
- Overview/ministry/sector/state/agency analytics
- Project creation and monthly update mutations
- Cost prediction, time prediction, and risk prediction endpoints
- Reports/export endpoints
- Explicit authorization on project reads and AI context retrieval
- Error responses for unavailable ML/Groq services

## Model and AI Status

- Cost model code loads `models/cost_prediction_model.pkl` and `cost_feature_columns.json`.
- Time model code loads classifier/regressor artifacts and `time_feature_columns.json`.
- The ML service assembles model inputs but currently includes a placeholder cost overrun probability (`0.5`) and catches model errors into a fabricated low-risk result.
- Groq is initialized from `GROQ_API_KEY`, but the model name is hard-coded and exceptions return fallback prose instead of an error response.
- No successful end-to-end model or Groq request has been recorded in this pre-change audit.

## Database and Monthly Data Status

- SQLAlchemy schema supports monthly snapshots with a unique `(project_code, report_month)` index.
- The file-backed repository references a `data_sources` table in history queries, but that table is not represented in the SQLAlchemy models and may not exist in the active database.
- Monthly PAIMANA CSVs are present; a formal report inventory and source-document linkage are not yet implemented.
- No evidence was found that the React pages consume monthly history from the backend.

## Security Findings

- `.env.example` contained a credential-like Groq value and must contain placeholders only.
- `.env` is ignored by Git, but secret scanning and key rotation should still be performed outside this change.
- JWT has a development fallback secret in source; deployments must provide `JWT_SECRET_KEY`.
- CORS includes `*` alongside credentialed origins and should be restricted for deployment.

## Validation Constraints

- The initial frontend build command was attempted, but the workspace PowerShell environment denied execution before npm produced build diagnostics. This is a validation failure, not a build success.
- Python import, database connectivity, endpoint, model inference, browser, and Groq checks remain to be run after the integration edits.
