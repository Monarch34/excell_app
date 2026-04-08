# Excell App

Mechanical test data analysis app with FastAPI backend and Vue 3 frontend.

## Stack

- Backend: Python, FastAPI, pandas, matplotlib, openpyxl
- Frontend: Vue 3, Pinia, PrimeVue, Plotly

## Run Locally

### Docker (Recommended)

```bash
docker compose up --build
```

This starts:
- `backend` on `http://localhost:8001`
- `frontend-dev` on `http://localhost:7173`
- Frontend API calls are proxied to the backend container

If file watching is unreliable (WSL), enable polling:

```bash
WATCHFILES_FORCE_POLLING=true CHOKIDAR_USEPOLLING=true VITE_USE_POLLING=true docker compose up --build
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt -r requirements-dev.txt
uvicorn src.api.server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## Quality Gates

```bash
# Backend (from backend/)
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python scripts/check_backend_boundaries.py
python scripts/sync_api_contract.py --check
pytest -q

# Frontend (from frontend/)
npm run check    # lint + type-check + test + build
```

### Pre-commit

```bash
pip install pre-commit
pre-commit install && pre-commit install --hook-type pre-push
pre-commit run --all-files
```

## Architecture

### Backend

```
api/ → services/ → core/
```

- `api/` — FastAPI routes, schemas, validation
- `services/` — orchestration, compilation, rendering (cannot import `api`)
- `core/` — pure domain logic (cannot import `api` or `services`)

### Frontend

- `views/` — page-level components
- `features/` — domain feature modules
- `composables/` — use-case orchestration
- `stores/` — Pinia state + actions
- `domain/` — pure utilities (no Vue imports)
- `services/` — API transport client

### API Contract

Backend Pydantic schemas → `backend/openapi.json` → `frontend/src/shared/types/generated/openapi.ts`. Requests include `X-Request-ID` for traceability.

## Deploy

### Production (local Docker)

```bash
docker compose -f docker-compose.prod.yml up --build
```

Frontend on port 80, proxies `/api/` to backend internally.

### Railway

1. Push to GitHub
2. Create a new project on Railway, connect the repo
3. Add two services — **backend** (root path: `backend/`) and **frontend** (root path: `frontend/`)
4. Backend: add a persistent volume mounted at `/app/data`
5. Backend env vars: `CORS_ORIGINS=https://<your-frontend-domain>`
6. Frontend env var: `BACKEND_URL=http://backend.railway.internal:8000`
7. Deploy — Railway detects each `Dockerfile` and `railway.toml` automatically
