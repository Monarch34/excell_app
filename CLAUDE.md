# CLAUDE.md

Project instructions for Claude Code. This is the single source of truth for architecture, conventions, and rules.

## Project Overview

Excel analysis web app: Vue 3 SPA frontend + FastAPI backend. Users upload CSV files, define formulas/calculations, run analysis pipelines, generate charts, and export XLSX reports. SQLite for persistence, in-memory TTL cache for uploaded datasets.

## Commands

### Backend (run from `backend/`)

```bash
uvicorn src.api.server:app --reload --port 8000   # dev server
pytest -q                                          # all tests
pytest -m unit                                     # unit only
pytest tests/unit/test_foo.py                      # single file
pytest -k "test_name"                              # single test by name
python -m ruff check src tests scripts             # lint
python -m ruff format src tests scripts            # format
python scripts/check_backend_boundaries.py         # layer import rules
python scripts/sync_api_contract.py --check        # API contract in sync
```

### Frontend (run from `frontend/`)

```bash
npm run dev                  # Vite dev server (port 5173)
npm run build                # production build
npm run lint                 # Biome + boundary checks
npm run type-check           # vue-tsc
npm run test -- --run        # Vitest single run
npm run check                # lint + type-check + test + build
```

### Docker

```bash
docker compose up --build                                    # dev (backend :8001, frontend :7173)
docker compose --profile test run --rm backend-test          # backend tests
docker compose --profile test run --rm frontend-test         # frontend tests
docker compose --profile test run --rm frontend-typecheck    # type check
```

### Pre-commit

```bash
pre-commit install && pre-commit install --hook-type pre-push
pre-commit run --all-files
```

## Architecture

### Backend — Layered with strict boundaries

```
api/ → services/ → core/
```

- **api/** — FastAPI transport: routers, Pydantic schemas, validation, middleware. Entry point: `src/api/server.py`
- **services/** — Orchestration: chart generation, CSV parsing, report compilation, XLSX building, formula context. **Cannot import `api`.**
- **core/** — Pure domain logic: calculations, formula engine, column mapping, database, chart filtering. **Cannot import `api` or `services`.**
- **domain/** — Value objects & DTOs (e.g., `ExportRequest`)
- **infrastructure/** — Persistence (config repository)

Boundary rules enforced by `scripts/check_backend_boundaries.py` (runs in pre-commit).

### Frontend — Feature-based Vue 3 + Pinia

- **views/** — Page-level components
- **features/** — Feature modules by domain (analysis, charts, columns, config, formulas, import, params, settings)
- **composables/** — Use-case orchestration (API calls, state transforms)
- **stores/** — Pinia state + actions (with persistence plugin)
- **domain/** — Pure utilities. **Cannot import components, stores, services, or Vue.**
- **services/** — Axios API client with `X-Request-ID` interceptor
- **shared/** — Reusable UI primitives (`AppDataTable`, `AppField`, `AppNotice`)
- **ui-foundation/** — Design tokens & CSS

Path alias: `@/*` maps to `src/*`. PrimeVue component library with custom theme.

### API Contract

Backend Pydantic schemas → OpenAPI spec (`backend/openapi.json`) → generated TypeScript types (`frontend/src/shared/types/generated/openapi.ts`).

- Generate: `python backend/scripts/sync_api_contract.py`
- Validate: `python backend/scripts/sync_api_contract.py --check`
- Gated in pre-push hook.

All endpoints versioned under `/api/v3/`.

## Rules

### Backend

- Custom exceptions in `core/exceptions.py`: `AppError`, `ValidationError`, `FileFormatError`, `ProcessingError`, `FormulaError`, `ConfigurationError`. These map to structured error responses `{ detail, code, request_id }`.
- Use `src/utils/logger.get_logger(__name__)` for logging.
- Type hints required (Python 3.10+ syntax: `list[str]`, `dict | None`).
- Pydantic models for all request/response validation.
- File uploads validated: size limit, filename sanitization, extension whitelist, UTF-8 encoding.
- CORS: never `allow_origins=["*"]`. Configure via `CORS_ORIGINS` env var.

### Frontend

- No `any` in domain/types/services — enforced by `scripts/check-no-any.mjs`.
- Stores cannot import components; domain cannot import Vue — enforced by `scripts/check-frontend-boundaries.mjs`.
- Frontend auto-attaches `X-Request-ID` header; backend echoes it in responses.
- UI components must not construct raw backend payloads. Use composables as DTO mappers.
- One mapper/composable per endpoint flow. Domain/store models stay separate from transport DTOs.

### API Communication

- Frontend sends typed API payloads; backend validates with Pydantic schemas.
- Export/report DTO versioned with `schema_version`.
- Error envelope: `{ detail, code, request_id }`.
- `ReportCompiler` is the single source of truth for export logic.
- Anti-patterns: duplicating payload shaping across components, ad-hoc error formats, service layer importing API types, domain logic depending on raw backend field names.

## Testing

- **Backend markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **Snapshot tests**: syrupy
- **Property-based tests**: hypothesis
- **Frontend**: Vitest for unit, Playwright for E2E

## Git Conventions

Conventional Commits: `feat(scope):`, `fix(scope):`, `refactor(scope):`, `docs(scope):`, `test(scope):`, `chore(scope):`, `perf(scope):`.

Branch prefixes: `feature/`, `fix/`, `refactor/`, `docs/`.

## Environment Variables

See `.env.example`. Key vars: `CORS_ORIGINS` (comma-separated, never `*`), `MAX_FILE_SIZE_MB` (default 50), `STORE_TTL_SECONDS` (default 3600), `ANALYSIS_DB_PATH`, `VITE_API_URL`.
