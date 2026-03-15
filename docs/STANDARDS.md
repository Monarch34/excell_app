# Development Standards

This document defines the standards for git, testing, code quality, and security in this project.

## Table of Contents

1. [Git Standards](#git-standards)
2. [Testing Standards](#testing-standards)
3. [Code Quality Standards](#code-quality-standards)
4. [Security Standards](#security-standards)

---

## Git Standards

### Branch Naming

| Prefix | Purpose | Example |
|--------|---------|---------|
| `main` / `master` | Production-ready code | - |
| `feature/` | New features | `feature/dark-mode` |
| `fix/` | Bug fixes | `fix/csv-parsing-error` |
| `refactor/` | Code improvements | `refactor/api-structure` |
| `docs/` | Documentation | `docs/api-reference` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:**

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change (no behavior change) |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvement |
| `security` | Security fix |

**Examples:**

```bash
feat(api): add file size validation to upload endpoint
fix(parser): handle UTF-8 BOM in CSV files
docs(readme): update installation instructions
refactor(server): extract shared processing logic
test(csv-parser): add edge case tests for malformed files
```

### Protected Operations

**NEVER do:**
- Force push to `main` / `master`
- Commit secrets (`.env`, `*.pem`, API keys, passwords)
- Use `git reset --hard` on shared branches
- Skip pre-commit hooks without explicit approval

**ALWAYS do:**
- Run `git status` before committing
- Run `git diff` to verify changes
- Create atomic commits (one logical change per commit)
- Write descriptive commit messages

---

## Testing Standards

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── core/               # Core module tests
│   ├── services/           # Service layer tests
│   └── api/                # API route tests
├── integration/             # Cross-module tests
└── snapshots/              # Regression tests
```

### Test Naming

- **Files:** `test_<module_name>.py`
- **Classes:** `Test<ClassName>`
- **Functions:** `test_<behavior_description>`

```python
# test_csv_parser.py
class TestCSVParserParse:
    def test_parse_valid_csv_returns_dataframe(self):
        pass

    def test_parse_raises_on_malformed_header(self):
        pass
```

### Test Markers

Use pytest markers for categorization:

```python
@pytest.mark.unit
def test_fast_isolated_function():
    pass

@pytest.mark.integration
def test_full_pipeline():
    pass

@pytest.mark.slow
def test_large_file_processing():
    pass
```

### Coverage Requirements

- **Minimum coverage:** 80% for new code
- **Critical paths:** 100% coverage (security, calculations)
- **Run coverage:** `pytest --cov=src --cov-report=html`

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest -m unit

# Run specific file
pytest tests/unit/core/test_models.py

# Run in parallel
pytest -n auto
```

---

## Code Quality Standards

### Python Style

- Follow **PEP 8**
- Use **type hints** (Python 3.10+ syntax)
- Maximum line length: **100 characters**
- Use `ruff` for linting + formatting

### Type Hints

Use modern Python 3.10+ syntax:

```python
# Preferred (Python 3.10+)
def process(data: list[dict[str, Any]]) -> dict | None:
    pass

# Avoid (older style)
from typing import List, Dict, Optional
def process(data: List[Dict[str, Any]]) -> Optional[Dict]:
    pass
```

### Error Handling

Use custom exceptions from `src/core/exceptions.py`:

```python
from src.core.exceptions import ValidationError

def validate_dimensions(dims: SpecimenDimensions) -> None:
    if dims.length <= 0:
        logger.error(f"Invalid length: {dims.length}")
        raise ValidationError(
            "Length must be positive",
            details={"provided_length": dims.length}
        )
```

**Exception Hierarchy:**

| Exception | Use Case |
|-----------|----------|
| `AppError` | Base class for all application errors |
| `ValidationError` | Input validation failures |
| `FileFormatError` | File parsing / format issues (CSV, encoding) |
| `ProcessingError` | Data processing failures |
| `FormulaError` | Formula evaluation failures (syntax, cycles, unknown refs) |
| `ConfigurationError` | Config/environment issues |

### Logging

Use `src/utils/logger.get_logger(__name__)`:

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

def process_file(path: str) -> None:
    logger.info(f"Processing file: {path}")
    try:
        # ... processing
        logger.debug(f"Processed {count} rows")
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        raise
```

**Log Levels:**

| Level | Use For |
|-------|---------|
| `DEBUG` | Detailed diagnostic info |
| `INFO` | Routine operations |
| `WARNING` | Unexpected but recoverable |
| `ERROR` | Operation failures |
| `CRITICAL` | System-level failures |

### Docstrings

Use Google-style docstrings for all public functions/classes:

```python
def calculate_toughness(strain: pd.Series, stress: pd.Series) -> float:
    """Calculate toughness as area under stress-strain curve.

    Uses trapezoidal integration for numerical approximation.

    Args:
        strain: Strain values in mm/mm.
        stress: Stress values in MPa.

    Returns:
        Toughness value in MJ/m^3.

    Raises:
        ValueError: If series lengths don't match.

    Example:
        >>> toughness = calculate_toughness(strain_series, stress_series)
        >>> print(f"Toughness: {toughness:.4f} MJ/m^3")
    """
```

### Constants

- Define in appropriate modules:
  - `src/utils/constants.py` - Application-wide constants
  - `src/core/localization/` - Language-specific strings
- Never hardcode values in business logic

---

## Security Standards

### File Uploads

All file uploads MUST be validated:

```python
from src.api.validators import validate_csv_upload

@app.post("/upload")
async def upload(file: UploadFile):
    content = await validate_csv_upload(file)
    # Process validated content
```

**Validation checks:**
- File size limit (50MB max)
- Filename sanitization
- Extension whitelist (.csv only)
- UTF-8 encoding
- Content structure validation

### CORS Configuration

**NEVER** use `allow_origins=["*"]` in production.

Configure via environment variable:

```bash
# .env
CORS_ORIGINS=http://localhost:5173,https://app.example.com
```

### Environment Variables

Required variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins | localhost:5173 |
| `LOG_LEVEL` | Logging level | INFO |

### Secrets Management

**NEVER commit:**
- `.env` files
- API keys or tokens
- Passwords or credentials
- Private keys (`.pem`, `.key`)
- Database connection strings with credentials

**Always use:**
- Environment variables for secrets
- `.gitignore` to exclude sensitive files
- Secret scanning in CI/CD

### Input Validation

- Use Pydantic models for request validation
- Validate numeric ranges for domain values
- Sanitize string inputs
- Use parameterized queries for any database operations

---

## Quick Reference

### Common Commands

```bash
# Development
uvicorn src.api.server:app --reload              # Start backend
cd frontend && npm run dev                        # Start frontend

# Testing
pytest                                            # Run all tests
pytest --cov=src --cov-report=html               # With coverage
pytest -m unit                                    # Unit tests only

# Code Quality
python -m ruff check src tests scripts            # Lint
python -m ruff format src tests scripts           # Format
python scripts/check_backend_boundaries.py        # Layer checks
python scripts/sync_api_contract.py --check       # API contract consistency

# Hooks
pre-commit run --all-files                        # Run configured hooks

# Git
git status                                        # Check status
git diff                                          # Review changes
git log --oneline -10                             # Recent commits
```

### Project Structure

Paths below are from the repository root. Backend commands (pytest, ruff, scripts) are run from the **backend/** directory.

```
excell_app/
├── backend/
│   ├── src/
│   │   ├── api/       # FastAPI routes, schemas, validators
│   │   ├── core/      # Business logic, models, exceptions
│   │   ├── services/  # CSV, Excel, charts
│   │   └── utils/     # Utilities, constants, logging
│   ├── tests/         # Backend test suite
│   └── scripts/       # e.g. sync_api_contract.py, check_backend_boundaries.py
├── frontend/          # Vue 3 app (components, composables, stores, services)
├── docs/              # Project documentation
└── sample_data/       # Test data (gitignored)
```
