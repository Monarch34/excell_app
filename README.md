# Excell App

Mechanical test data analysis app with FastAPI backend and Vue 3 frontend.

## Stack

- Backend: Python, FastAPI, pandas, matplotlib, openpyxl
- Frontend: Vue 3, Pinia, PrimeVue, Plotly

## Run Locally
### Docker (Recommended)

Dev mode (default):

```powershell
docker compose up --build
```

This starts:
- `backend` on `http://localhost:8001` (host access, optional)
- `frontend-dev` on `http://localhost:7173`
- Frontend API calls are proxied to the backend container (`VITE_API_TARGET=http://backend:8000`)

If file watching is unreliable on your machine, you can enable polling temporarily:

```powershell
$env:WATCHFILES_FORCE_POLLING = "true"
$env:CHOKIDAR_USEPOLLING = "true"
$env:VITE_USE_POLLING = "true"
docker compose up --build
```

Prod UI check (Nginx bundle):

```powershell
docker compose --profile prod up --build
```

Test services:

```powershell
docker compose --profile test run --rm backend-test
docker compose --profile test run --rm frontend-test
docker compose --profile test run --rm frontend-typecheck
```

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn src.api.server:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Local frontend dev can use an explicit API URL (recommended):

```powershell
$env:VITE_API_URL = "http://localhost:8001/api/v3"
npm run dev
```

## Quality Gates

### Local

```powershell
# Install dependencies (reproducible)
npm --prefix frontend ci
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt

# Backend
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python scripts/check_backend_boundaries.py
python scripts/sync_api_contract.py --check
pytest -q
cd ..

# Frontend
npm --prefix frontend audit --omit=dev
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

### Docker

```powershell
# Backend tests
docker compose --profile test run --rm backend-test

# Frontend unit tests (Vitest, run mode)
docker compose --profile test run --rm frontend-test

# Frontend type-check
docker compose --profile test run --rm frontend-typecheck
```

### Pre-commit

```powershell
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files
```

## Architecture

### Backend

- `backend/src/api`: transport layer (FastAPI routes/schemas)
- `backend/src/services`: orchestration/compiler/render helpers
- `backend/src/core`: pure domain logic (formulas/calculations/ops)

Boundary rule:
- `core` must not import `api` or `services`
- `services` must not import `api`

### Frontend

- `frontend/src/components`: UI rendering
- `frontend/src/composables`: page/use-case orchestration
- `frontend/src/stores`: state + actions
- `frontend/src/domain`: pure domain utilities
- `frontend/src/services`: API transport client

Boundary checks are enforced in `frontend/scripts/check-frontend-boundaries.mjs`.

## Frontend/Backend Communication

- Export/report uses a versioned DTO contract (`schema_version`).
- Backend compiles export DTO via `ReportCompiler` (single source of truth).
- API requests include `X-Request-ID`; backend echoes it for traceability.
- Error payloads include `request_id` for debugging.
- API contract files are generated from backend OpenAPI:
  - `docs/openapi.json`
  - `frontend/src/types/generated/openapi.ts`

See:
- `docs/README.md`
- `docs/REPORT_DTO.md`
- `docs/STANDARDS.md`
- `docs/FRONTEND_BACKEND_COMMUNICATION.md`
