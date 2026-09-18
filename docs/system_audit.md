# InfraGuard-AI System Audit

**Audit date:** 2026-09-18
**Scope:** Existing repository inspection before integration changes
**Positioning:** Predictive decision support built on PAIMANA/MoSPI project-monitoring data; not a replacement for PAIMANA.

## Executive Status

| Area | Status | Evidence | Main gap |
|---|---|---|---|
| Frontend | PARTIAL | `frontend/src/App.tsx`, dashboard pages, Axios client | Several authenticated surfaces are incomplete; mock state/map content remains |
| Backend | PARTIAL | `backend/main.py` exposes health, auth, projects, analytics, ML, risk, monthly update, AI routes | Missing admin, reports, alerts, upload, project creation, and complete health routes |
| Database | PARTIAL | SQLAlchemy models and local SQLite fallback in `backend/database.py` | No verified Supabase/PostgreSQL migration or RLS evidence; schema is incomplete for report/source data |
| Authentication | PARTIAL | JWT login and `/api/auth/me` in `backend/main.py`, helpers in `backend/auth.py` | Registration route, logout audit, password-change flow, environment-enforced JWT secret, and first-login state are missing |
| RBAC | FAIL | `check_project_access` exists in `backend/auth.py` | Role names are inconsistent and the final fallback returns `True`, allowing unintended access |
| Project data | PARTIAL | `data/processed/*.csv`, local SQLite, `Project` and `ProjectSnapshot` models | Historical data exists locally but source provenance and database loading are not fully verified |
| Monthly history | PARTIAL | Unique `(project_code, report_month)` snapshot index and monthly update route | History is preserved, but month ordering/date validation and update authorization policy need strengthening |
| Cost ML | PARTIAL | `src/models/cost_model.py`, `models/cost_prediction_model.pkl`, feature JSON | Inference is connected to an endpoint, but model provenance, leakage audit, and persistence/health checks are incomplete |
| Time ML | PARTIAL | `src/models/time_model.py`, classifier/regressor artifacts, feature JSON | Inference is connected, but missing-resource handling and model validation evidence are incomplete |
| Risk engine | PARTIAL | `backend/services/ml_service.py`, `src/risk/risk_engine.py` | Runtime pipeline exists; early-warning module is a TODO and two risk implementations are not clearly centralized |
| Early warnings | FAIL | `src/risk/early_warning.py` contains a TODO only | No API-backed warning persistence or retrieval |
| Groq AI | PARTIAL | `backend/services/ai_service.py`, Groq dependency | Backend service exists but no `/health/groq`, model reachability check, or safe structured failure contract |
| RAG | NOT CONFIGURED | No verified RAG index/retriever/source implementation found in inspected paths | PAIMANA report retrieval and page metadata are not connected |
| API layer | PARTIAL | `frontend/src/services/api.ts` centralizes current calls | Client does not cover admin, reports, alerts, updates, health, or full prediction response types |
| Search | PASS (scoped) | `GET /api/projects/search` queries database fields | Search covers code/name/agency/ministry, but not all requested identifiers and requires auth |
| Dashboard analytics | PARTIAL | `/api/analytics/overview`, ministry, sector, state, agency | Backend aggregation exists; frontend and risk assessment completeness need verification |
| Reports | FAIL | Report schemas exist in `backend/schemas.py`; no report routes found | No real report generation/view/download path |
| Admin | FAIL | No admin route group found in `backend/main.py` | User/role/org/upload/audit/system-health workflows are incomplete |
| Audit logging | PARTIAL | `AuditLog` model and `log_audit_action` helper | Login/monthly update are logged; privileged coverage and safe failure handling are incomplete |
| Security | FAIL | `.gitignore` ignores `.env`; server key is read from env | Hardcoded JWT fallback, source-seeded demo credentials, permissive access fallback, and unverified secret hygiene |
| Frontend build | NOT VERIFIED | `frontend/package.json` has `npm run build` | Baseline build still needs to run |
| Backend startup | NOT VERIFIED | FastAPI app and SQLAlchemy local fallback exist | Import/startup and endpoint smoke checks still need to run |
| End-to-end | NOT CONFIGURED | No tests in `tests/` | No executable end-to-end flow currently exists |

## Frontend Structure

- Entry and routing: `frontend/src/main.tsx`, `frontend/src/App.tsx`.
- Public pages: `frontend/src/pages/LandingPage.tsx`, auth login/register pages.
- Authenticated pages: dashboard, project list/intelligence, ministry, sector, state, new projects, AI assistant.
- Layout/UI: `frontend/src/components/layout`, `frontend/src/components/ui`.
- API/auth: `frontend/src/services/api.ts`, `frontend/src/contexts/AuthContext.tsx`.
- Tailwind v4 is indicated by `@import "tailwindcss"` and `@tailwindcss/postcss`; `tailwind.config.js` is legacy-compatible configuration and needs build verification.

## Backend Structure

- FastAPI entrypoint: `backend/main.py`.
- Authentication and authorization: `backend/auth.py`.
- SQLAlchemy engine/session: `backend/database.py`.
- ORM entities: `backend/models.py`.
- Pydantic schemas: `backend/schemas.py`.
- Services: `backend/services/ml_service.py`, `ai_service.py`, and `data_ingest.py`.
- Existing routes include health, login/me, projects/search/list/detail/history, analytics, cost/time/risk prediction, and monthly update.

## Data And Database Findings

- Local processed datasets include `master_projects.csv`, `paimana_historical.csv`, `project_features.csv`, cost/time ML datasets, and a local SQLite database.
- The ORM models preserve project identity separately from monthly snapshots and enforce a unique project/month index.
- There is no inspected Supabase client, migration directory, RLS policy, report/source table, organization relationship table, or explicit source-document/page metadata model.
- Data validation logic exists in `backend/services/data_ingest.py`, but it must be reviewed for safe defaults and duplicate/month/date handling before being used as an authoritative ingestion path.

## ML And Risk Findings

- Cost inference loads `models/cost_prediction_model.pkl` and `models/cost_feature_columns.json` through `src/models/cost_model.py`.
- Time inference loads classifier/regressor artifacts and `models/time_feature_columns.json` through `src/models/time_model.py`.
- `backend/services/ml_service.py` assembles model inputs and combines cost/time outputs with expenditure-progress mismatch scoring.
- `src/risk/risk_engine.py` is a batch CSV pipeline, while `backend/services/ml_service.py` is the API-time risk path. These need a documented authoritative boundary.
- `src/risk/early_warning.py` is not implemented.
- No executed model-load/inference or genuine metric validation was found during this audit. Small-data and target-leakage limitations must remain explicit.

## AI/RAG Findings

- `backend/services/ai_service.py` retrieves project/database context and invokes Groq server-side when configured.
- The AI service currently contains project-context retrieval and a high-risk portfolio query path, but its general portfolio query is not fully authorization-scoped through the shared access helper.
- No verified PAIMANA PDF extraction-to-index-to-retriever path or source metadata persistence was found.
- Groq has no dedicated health route and the service error text may expose raw upstream exception details through the API route.

## Hard-Coded, Mock, And Duplicate Findings

- `frontend/src/pages/dashboard/StateView.tsx` contains explicitly marked mock state data.
- `frontend/src/pages/LandingPage.tsx` contains a fake chart row used for presentation.
- `frontend/src/services/api.ts` defaults to `http://localhost:8000` and reads `VITE_API_URL`, while the target contract calls for `VITE_API_BASE_URL`.
- `backend/auth.py` contains a hardcoded fallback JWT secret, which is unsafe for deployment.
- `backend/services/data_ingest.py` contains seeded demo user credential values in source. These must not become a production/default-admin path and must be removed or replaced with environment-driven seeding.
- Risk calculation is duplicated between `src/risk/risk_engine.py` and `backend/services/ml_service.py`; the runtime authority must be made explicit.

## Highest-Priority Integration Problems

1. Enforce a non-default server JWT secret and remove source credentials from runtime seeding.
2. Replace permissive RBAC fallback behavior with canonical roles and explicit deny-by-default authorization.
3. Run frontend build and backend import/startup checks to identify immediate blockers.
4. Add truthful health routes for database, ML, risk, Groq, and RAG configuration.
5. Complete registration/password/admin/report/alerts/project-creation routes only after existing route behavior is covered by focused tests.
6. Implement early-warning retrieval and persistence from the authoritative risk path.
7. Connect frontend loading/error/unavailable states and remove production use of mock arrays.
8. Document or implement Supabase/PostgreSQL/RLS integration; current evidence supports local SQLite fallback only.

## Required Evidence Before PASS

- `npm run build` and `npm run lint` results from `frontend/`.
- Python syntax/import/startup checks and focused API tests.
- Auth/RBAC negative tests for unauthorized project, update, report, ML, risk, and AI access.
- Model artifact load and inference checks with actual feature schemas.
- Groq health and failure-mode checks without exposing secrets.
- Data validation report and source metadata verification.
- End-to-end flow from login through project history, prediction, risk, AI/source display, report, and logout.
