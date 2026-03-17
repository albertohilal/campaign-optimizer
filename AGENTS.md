Sí. Te dejo una versión completa, lista para copiar y pegar, manteniendo lo que ya tenías y agregando una sección fuerte de **reporting / handoff** para los informes que le pedís a Copilot.

````md
# AGENTS.md

## Repository Purpose

`campaign-optimizer` is a Python 3.11 FastAPI service for analyzing Google Ads campaign performance and generating optimization recommendations. The MVP is intended for one client account first, but the codebase must stay reusable for additional accounts later.

This repository must support both:
- direct API execution for development and testing
- structured technical handoff through repository-based Markdown reports that can be shared with external collaborators or AI assistants without requiring full chat history

---

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

### Phase 3

Implement the findings-to-actions workflow:
- transformation of findings into proposed optimization actions
- prioritization logic
- action payload generation
- human-review-ready output
- persistence of generated action proposals when required

### Phase 4

Harden the system for multi-account and operational use:
- account-aware configuration
- improved validation and error handling
- richer reporting
- better testing coverage
- future MySQL deployment compatibility review

---

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
- Keep business logic out of route handlers whenever possible.
- Keep route modules thin and service modules explicit.
- Prefer deterministic, inspectable logic over hidden automation.

---

## Google Ads Integration Rules

- The codebase must be prepared for the official Google Ads API Python client from day one.
- In development mode, if Google Ads credentials are missing, mock mode must activate automatically.
- Mock mode must allow the app to start and Phase 2 analysis endpoints to remain usable with sample data.
- Real Google Ads authentication errors must be handled as controlled application errors, not raw crashes.
- Keep TODO markers close to future GAQL queries where account-specific adjustments may be needed.
- Avoid coupling the internal domain logic too tightly to raw Google Ads response structures.
- Normalize Google Ads-derived data before analysis whenever reasonable.

---

## Persistence Rules

- Create the `AnalysisReport` model in Phase 1 even if analysis routes arrive in Phase 2.
- Store findings and recommendations as JSON strings for the MVP.
- Keep schema design simple and avoid unnecessary normalization.
- Do not overdesign persistence for action history until the findings-to-actions module is stable.
- Any persistence added for action proposals must be explainable and easy to inspect manually.

---

## API Rules

- The root route should describe the service and current implementation phase.
- The health route should confirm the API is running.
- Endpoints must return predictable JSON payloads.
- Startup should initialize logging and the database safely.
- Error responses should be controlled, explicit, and JSON-based.
- Avoid leaking raw third-party exceptions directly through the API.
- Keep request and response schemas stable once introduced, unless a change is explicitly requested.

---

## Testing Rules

- Keep tests lightweight and focused.
- Phase 1 must include a passing health endpoint test using FastAPI `TestClient`.
- The Phase 1 acceptance target is that `uvicorn app.main:app --reload` starts successfully.
- Add tests for each new route once the route contract becomes meaningful.
- Prefer a few high-value tests over broad but shallow test coverage.
- If a bug is fixed, add or update at least one test when practical.
- Do not claim validation was performed unless the validation step actually ran.

---

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
  docs/
    05-REPORTES/
  tests/
    __init__.py
    test_health.py
  requirements.txt
  README.md
  .env.example
  .gitignore
  AGENTS.md
````

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

Phase 3 likely additions:

```text
app/services/action_mapper.py
app/services/action_prioritizer.py
app/services/action_validator.py
app/schemas_actions.py
```

---

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

---

## Code Change Rules

* Prefer complete, working file updates over partial pseudo-code.
* Keep edits localized to the modules that actually need change.
* Do not perform broad refactors unless they are necessary for the requested task.
* Preserve existing naming unless there is a clear reason to improve it.
* When changing behavior, keep route contracts and service responsibilities explicit.
* Avoid hidden side effects.
* Avoid introducing new dependencies unless clearly justified.
* If a temporary workaround is used, label it clearly with a concise TODO.

---

## Documentation Rules

* Documentation must reflect the current implemented reality, not the intended future state.
* If architecture or behavior changes materially, update the relevant documentation in the same work cycle whenever practical.
* Keep README high-level and operational.
* Keep AGENTS.md directive and implementation-oriented.
* Put detailed technical reports in `docs/05-REPORTES/`.
* Do not bury key operational facts only inside chat messages.

---

## Reporting Rules

When a task requires analysis, diagnosis, implementation summary, incident review, audit, status update, or technical handoff, the agent must produce a Markdown report inside the repository whenever requested or when the task naturally benefits from persistent documentation.

### Report Location

Store reports in:

`docs/05-REPORTES/`

### Filename Convention

Use:

`YYYY-MM-DD-topic-slug.md`

Examples:

* `2026-03-17-campaigns-endpoint-test-status.md`
* `2026-03-17-metrics-service-diagnostic.md`
* `2026-03-17-findings-to-actions-design.md`

### Report Purpose

Reports are intended to:

* preserve working context across sessions
* support handoff to another agent or collaborator
* make technical reasoning inspectable
* reduce dependence on fragmented prompts or chat history

### Autocontained Handoff Rule

Every report must be understandable by:

* a human collaborator joining late
* an external AI assistant
* the same developer returning later without full chat context

Therefore every report must include enough context to stand on its own.

A valid report must make clear:

* what problem was being solved
* what the current state is
* what was observed
* what was changed or proposed
* what remains pending
* what the exact next step is

### Mandatory Structure

Every report must include these sections in this order:

1. `# Title`
2. `## Objective`
3. `## Context`
4. `## Current State`
5. `## Findings`
6. `## Technical Impact`
7. `## Files Involved`
8. `## Changes Made or Proposed`
9. `## Validation`
10. `## Risks / Pending`
11. `## Recommended Next Step`

### Content Rules

* Be concrete, technical, and verifiable.
* Use exact file paths whenever relevant.
* Distinguish clearly between:

  * observed facts
  * inferred conclusions
  * pending verification
* Do not invent validations that were not run.
* Include logs or error excerpts only when they materially improve diagnosis.
* Prefer clarity over length.
* Avoid vague summaries like "fixed issue" without stating where and how.
* State uncertainty explicitly when present.

---

## Report Types

### Diagnostic Report

Use when the goal is analysis before or without code modification.

Focus on:

* problem statement
* evidence
* likely cause
* candidate solutions
* recommended next action

### Implementation Report

Use when code was modified.

In addition to the mandatory structure, include:

* `## Files Modified`
* `## Commands Run`
* `## Expected Result`
* `## How to Test`

### Incident Report

Use for breakages, regressions, failed runs, or environment issues.

Focus on:

* symptom
* scope
* probable cause
* immediate mitigation
* pending corrective action

### Design Report

Use for architectural proposals or planned modules.

Focus on:

* objective
* constraints
* options considered
* selected direction
* tradeoffs
* next implementation step

---

## Rules for Reports Generated for Copilot or External AI Review

When generating a report intended to be shared outside the current coding session:

* make the report fully self-contained
* include exact paths
* include exact module names
* include route names and service names when relevant
* include assumptions explicitly
* include the recommended continuation prompt if useful

Optional additional section for those cases:

`## Suggested Continuation Prompt`

This section should contain a concise prompt that another agent can use to continue the work without reconstructing the entire context.

---

## Prompt-to-Report Rule

If asked to "prepare a report", "summarize for handoff", "leave context for later", or similar, produce the result in repository report format, not only as chat text, unless explicitly instructed otherwise.

If the work includes both code and reporting, prioritize:

1. correct code
2. honest validation status
3. persistent report in `docs/05-REPORTES/`

---

## Operational Discipline

* Do not confuse plans with implemented behavior.
* Do not state that an endpoint is covered unless a test exists and was run.
* Do not state that a service is integrated unless imports, wiring, and runtime behavior support that claim.
* Do not mark a bug as fixed only because code was edited; a validation step must support the claim.
* Keep the repo state understandable for future continuation.

---

## Preferred Working Style for This Repository

* small, verifiable increments
* explicit file-level changes
* minimal but real tests
* reports that preserve context
* stable foundations before deeper business logic
* diagnostics before abstraction
* implementation after evidence
