# Frontend-Backend Communication Guide

This project uses a contract-first communication model.

## 1. Use DTO contracts, not ad-hoc payloads

- Frontend sends typed API payloads from `frontend/src/types/api.ts`.
- Backend validates with Pydantic schemas in `src/api/schemas.py`.
- Export/report DTO is versioned with `schema_version`.

## 2. Keep transformation in one place

- Frontend maps UI/store state -> API DTO in composables (for export: `useConfigExportReport`).
- Backend maps DTO -> compiled report artifacts in `ReportCompiler`.
- Avoid rebuilding payload shape in multiple components.

## 3. Standard error envelope

Backend errors should include:
- `detail`
- `code`
- `request_id`

Frontend should display user-safe messages and keep `request_id` available for debugging.

## 4. Request correlation

- Frontend sends `X-Request-ID` automatically via Axios interceptor.
- Backend middleware propagates or generates `X-Request-ID`.
- Response headers include `X-Request-ID`.

This enables fast issue tracing from UI logs to backend logs.

## 5. Ownership boundaries

- `api` layer: validation + transport only.
- `services` layer: orchestration/compilation only.
- `core` layer: pure business logic only.
- UI components should not contain backend payload logic.

## 6. Recommended evolution path

1. Add endpoint-specific DTO mappers in frontend (one file per endpoint flow).
2. Add snapshot tests for request/response DTOs.
3. Add OpenAPI-based contract checks in CI.
4. Introduce `schema_version` migration handling when DTO changes.

## 7. Endpoint playbook (use this for every new feature)

1. Define/extend backend Pydantic request/response schemas.
2. Add matching frontend wire types in `frontend/src/types/api.ts`.
3. Create or update one mapper/composable that builds the request DTO.
4. Keep domain/store models separate from transport DTOs.
5. Add tests:
   - backend integration test for response envelope
   - frontend mapper test for payload shape
   - happy-path + error-path API client test

## 8. Contract checklist before merge

- Request and response fields are explicitly typed.
- Error shape includes `detail`, `code`, `request_id`.
- `X-Request-ID` is propagated both directions.
- No UI component constructs raw backend payloads directly.
- Any breaking DTO change increments/handles `schema_version`.

## 9. Anti-patterns to avoid

- Duplicating payload shaping in multiple Vue components.
- Returning endpoint-specific ad-hoc error formats.
- Backend service layer importing API schema types.
- Frontend domain logic depending on raw backend field names.

## 10. OpenAPI sync command

Use backend as the contract source. Run from the **backend/** directory:

```powershell
cd backend
.\venv\Scripts\python.exe scripts\sync_api_contract.py
```

This updates:
- `docs/openapi.json`
- `frontend/src/types/generated/openapi.ts`

Validation-only mode:

```powershell
.\venv\Scripts\python.exe scripts\sync_api_contract.py --check
```

## 11. Active API v3 endpoints

- `POST /api/v3/datasets/upload`
- `POST /api/v3/datasets/detect-columns`
- `POST /api/v3/formulas/validate`
- `POST /api/v3/formulas/preview`
- `POST /api/v3/processing/run`
- `GET /api/v3/processing/runs/{run_id}/data`
- `POST /api/v3/charts/metrics`
- `POST /api/v3/reports/xlsx`
- `GET /api/v3/configs/limits`
- `GET /api/v3/configs` — list saved configs
- `POST /api/v3/configs` — save config
- `GET /api/v3/configs/{config_id}` — get one config
- `DELETE /api/v3/configs/{config_id}`
- `GET /api/v3/health`
