# AI Agent Customization for Solaris Monitoring

This file helps AI coding agents be immediately productive in the Solaris Monitoring codebase.

## 🚀 Quick Start Commands

### Development Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --app-dir src --reload
```

### Docker Setup
```bash
docker compose up --build -d
curl http://localhost:8000/health
docker compose down
```

### Code Quality (Required before PRs)
```bash
ruff check .              # Lint validation
ruff format --check .    # Format validation
mypy src tests           # Type checking
pytest --cov=src --cov-report=term-missing --cov-report=xml  # Tests + coverage (min 90%)
```

### Database Migrations
```bash
alembic upgrade head     # Apply migrations
alembic revision --autogenerate -m "Description"  # Create new migration
```

## 🏗️ Architecture & Design Patterns

### 4-Layer Architecture (src/ folder)

```
Routers (API endpoints) → Schemas (Pydantic models)
                ↓
        Services (Business logic)
                ↓
    Repositories (Data access)
                ↓
Models (SQLAlchemy ORM)
```

**Key Files by Responsibility:**
- **Routers** (`src/utils/routers/`): HTTP endpoints, request validation
  - `cells.py`: CRUD operations for photovoltaic cells
  - `readings.py`: Voltage readings management
  - `health.py`: API health check endpoint
- **Schemas** (`src/utils/schemas/`): Pydantic models for request/response validation
- **Services** (`src/utils/services/`): Business logic, orchestration
  - `CellService`: Manages photovoltaic cells
  - `ReadingService`: Handles readings with analysis (efficiency, anomalies)
- **Repositories** (`src/utils/repositories/`): SQLAlchemy database operations
  - Protocol-based abstractions (`protocols.py`)
  - Implementations: `SqlAlchemyCellRepository`, `SqlAlchemyReadingRepository`
- **Domain** (`src/utils/domain/`): Core business logic independent of frameworks
  - `analysis.py`: Efficiency calculations and anomaly detection
  - `errors.py`: Domain exceptions

### Dependency Injection
- Use FastAPI's `Depends()` pattern (see [src/utils/dependencies.py](src/utils/dependencies.py))
- Services are instantiated fresh per request
- Database session is auto-managed via `get_db()` context manager

### Configuration
- Centralized in [src/utils/config.py](src/utils/config.py) via `Settings` dataclass
- Environment-based: loads from `os.environ`
- In production: `ENVIRONMENT=production` + `DEVICE_API_KEY` are mandatory
- Database URL auto-normalization for Render/Heroku-style URLs

### API Security
- **Read endpoints** (`GET`): Public, no auth required
- **Write endpoints** (`POST/PUT/DELETE`): Require `X-API-Key` header
- Uses `secrets.compare_digest()` to prevent timing attacks

### MQTT Integration
- Optional, enabled only if `MQTT_HOST` env var is set
- Background thread (non-blocking) started in FastAPI lifespan
- Handled in [src/utils/mqtt_adapter.py](src/utils/mqtt_adapter.py)

## 📐 Conventions & Patterns

### Code Style
- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Python**: 3.12+
- **Import order**: E (errors) → F (pyflakes) → I (isort) → UP (upgrades) → B (bugbear)
  - Ruff enforces this via pre-commit style
- **Type hints**: Mandatory for all functions and methods (`disallow_untyped_defs = true`)

### Database Patterns
- **ORM**: SQLAlchemy 2.0 (modern async-ready API)
- **Migrations**: Alembic auto-generated from model changes
- **Timestamps**: Always UTC via custom `UTCDateTime` type in [src/db.py](src/db.py)
  - All `datetime` objects are normalized to UTC on write and re-enforced on read
- **Foreign keys**: Cascade delete enabled (e.g., deleting a cell deletes its readings)

### Testing
- **Framework**: pytest with pytest-cov
- **Min coverage**: 90% (enforced in CI)
- **Fixtures**: Shared in [tests/conftest.py](tests/conftest.py)
- **Fakes**: Mock objects in [tests/fakes.py](tests/fakes.py)
- **Test structure**:
  - `tests/unit/`: Service and utility tests
  - `tests/integration/`: API endpoint tests via `httpx.AsyncClient`
  - `tests/test_smoke.py`: Health check validation

### Business Logic Rules
Reference [docs/API.md](docs/API.md) for rules:
- **Efficiency formula**: `(voltage_measured / rated_voltage) * 100`
- **Max safe voltage**: `rated_voltage * 1.2` (server-derived)
- **Anomaly flags**: voltage exceeds max_safe_voltage OR efficiency < threshold
- **Device clock tolerance**: ±5 minutes (reject readings from future)
- **Inactive cells**: Cannot accept new readings

## ⚠️ Common Pitfalls & Solutions

### 1. **Type Errors with `Callable`**
- **Problem**: mypy complains about `callable` (lowercase)
- **Solution**: Use `from typing import Callable` and write `Callable[[...], ReturnType]`

### 2. **Unused Imports After Cleanup**
- **Problem**: Removing dead code leaves unused imports
- **Solution**: Run `ruff check .` before committing; Ruff will flag them

### 3. **F-strings Without Placeholders**
- **Problem**: `f"message"` triggers F541 (f-string-is-literal)
- **Solution**: Use plain string `"message"` if no interpolation needed

### 4. **Alembic Revision Conflicts**
- **Problem**: Multiple developers create migrations with same timestamp
- **Solution**: Rebase and let Alembic renumber or manually merge `versions/` files

### 5. **datetime Without Timezone**
- **Problem**: SQLite discards `tzinfo`, leading to naive datetimes
- **Solution**: Always use `datetime.datetime.now(datetime.timezone.utc)` or rely on custom `UTCDateTime` type

### 6. **API Key Not Configured in Production**
- **Problem**: DEVICE_API_KEY missing in production raises `ValueError` at startup
- **Solution**: Add `DEVICE_API_KEY` as secret in Render/Docker environment

### 7. **MQTT Connection Hangs**
- **Problem**: MQTT thread blocks startup if broker is unreachable
- **Solution**: MQTT runs in daemon thread; non-blocking. Disable via omitting `MQTT_HOST`.

## 📚 Documentation Reference

- [docs/API.md](docs/API.md): REST API endpoints and business rules
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): Docker, Render production, GitHub Actions setup
- [docs/ESP32_INTEGRATION.md](docs/ESP32_INTEGRATION.md): MQTT/IoT device integration
- [docs/adr/](docs/adr/): Architecture Decision Records
- [README.md](README.md): Project overview and quick start
- [docs/ai_logs/](docs/ai_logs/): Team AI prompts and decisions (see format below)

## 📝 AI Logging Format

When working with AI, log your prompts and decisions in [docs/ai_logs/](docs/ai_logs/) using this structure:

```markdown
# [Team Member Name] - Prompt #[Number]

### IA Utilizada: GitHub Copilot (Claude Haiku 4.5)

**Prompt del integrante completo:**
> [Full original prompt here]

**Respuesta de la IA completa:**

[Full AI response with key decisions and changes]

**Qué se aceptó:** [What was kept from the response]
**Qué se denegó:** [What was rejected and why]
**Qué se modificó:** [What was changed after the response]
```

Example: [docs/ai_logs/AI_LOG_Lyla.md](docs/ai_logs/AI_LOG_Lyla.md)

---

## 🔧 When Working on Changes

1. **New Feature**: Create branch → Implement with tests → Run CI validation → PR
2. **Code Quality Fix**: Run `ruff format .`, then `ruff check .` and `mypy src tests`
3. **Database Change**: Create Alembic migration → Test locally → Commit with migration
4. **API Change**: Update endpoint → Update Pydantic schema → Update [docs/API.md](docs/API.md) → Add tests
5. **Configuration**: Add to [src/utils/config.py](src/utils/config.py) → Default sensible value → Document in README

## 🎯 CI/CD Pipeline

GitHub Actions (`.github/workflows/ci-cd.yml`) runs on every push:
1. Lint: `ruff check .`
2. Format: `ruff format --check .`
3. Type check: `mypy src tests`
4. Tests: `pytest --cov=src` (min 90% coverage)
5. Migrations: `alembic upgrade head`
6. Docker build: Multi-stage image for production

All checks must pass before merge. No exceptions.
