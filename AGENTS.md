# AGENTS.md

## Repository Purpose

`campaign-optimizer` is a Python 3.11 FastAPI service for analyzing Google Ads campaign performance and generating optimization recommendations. The MVP is intended for one client account first, but the codebase must stay reusable for additional accounts later.

## Delivery Phases

### Phase 1

Implement only the runnable foundation:
- project structure
- configuration
- logging
- database setup
- ORM models
- API schemas
- shared dependencies
- FastAPI app bootstrap
- root route
- health route
- README
- `.env.example`
- `.gitignore`
- `requirements.txt`
- basic health test

### Phase 2

Implement business features on top of the Phase 1 foundation:
- Google Ads API wrapper
- campaigns route
- metrics service
- analyzer
- recommendations service
- report generator
- analysis routes

## Architecture Rules

- Use FastAPI for the API layer.
- Use Python 3.11-compatible code.
- Keep modules small, readable, and production-oriented.
- Prefer clear service boundaries over premature abstraction.
- Use SQLAlchemy in a minimal way only.
- Do not add repository patterns, unit-of-work layers, or Alembic in this MVP.
- Use SQLite by default for local development.
- Keep the database setup compatible with a later move to MySQL by relying on `DATABASE_URL` and SQLAlchemy.
- Use environment variables loaded from a `.env` file.
- Use type hints where they add clarity.
- Add docstrings to important functions.
- Use standard library logging only.
- Do not introduce additional infrastructure (Docker, Redis, background workers, queues) during Phase 1.

## Google Ads Integration Rules

- The codebase must be prepared for the official Google Ads API Python client from day one.
- In development mode, if Google Ads credentials are missing, mock mode must activate automatically.
- Mock mode must allow the app to start and Phase 2 analysis endpoints to remain usable with sample data.
- Real Google Ads authentication errors must be handled as controlled application errors, not raw crashes.
- Keep TODO markers close to future GAQL queries where account-specific adjustments may be needed.

## Persistence Rules

- Create the `AnalysisReport` model in Phase 1 even if analysis routes arrive in Phase 2.
- Store findings and recommendations as JSON strings for the MVP.
- Keep schema design simple and avoid unnecessary normalization.

## API Rules

- The root route should describe the service and current implementation phase.
- The health route should confirm the API is running.
- Endpoints must return predictable JSON payloads.
- Startup should initialize logging and the database safely.

## Testing Rules

- Keep tests lightweight and focused.
- Phase 1 must include a passing health endpoint test using FastAPI `TestClient`.
- The Phase 1 acceptance target is that `uvicorn app.main:app --reload` starts successfully.

## Repository Layout

```text
campaign-optimizer/
  app/
    __init__.py
    main.py
    config.py
    logger.py
    database.py
    models.py
    schemas.py
    dependencies.py
    routes/
      __init__.py
      health.py
    services/
      __init__.py
    utils/
      __init__.py
  data/
    reports/
  tests/
    __init__.py
    test_health.py
  requirements.txt
  README.md
  .env.example
  .gitignore
  AGENTS.md
```

Phase 2 planned additions inside the existing package structure:

```text
app/routes/analysis.py
app/routes/campaigns.py
app/services/google_ads_client.py
app/services/metrics_service.py
app/services/analyzer.py
app/services/recommendations.py
app/services/report_generator.py
app/utils/date_ranges.py
app/utils/helpers.py
```

## Phase 1 Implementation Notes

* Create the full package layout now so imports stay stable later.
* It is acceptable for Phase 2 files to be absent until that phase begins, but the directories must already exist.
* During Phase 1, do not create placeholder implementations for Phase 2 modules unless explicitly requested.
* Creating the directories for future modules is enough.
* Keep the root and health responses explicit that the project is currently in Phase 1.
* Favor complete files over stubs for anything included in Phase 1 scope.
* Keep `app/main.py` limited to app creation, startup initialization, and router registration.
* Do not place business logic in `app/main.py`.
* Database initialization must be safe to run multiple times without breaking the app.
