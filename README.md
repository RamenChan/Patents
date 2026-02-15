# Patents

Patent-ready workflow scaffold with Clean Architecture boundaries.

## Purpose
- Capture invention disclosures
- Generate claims and specification drafts
- Track reviews and approvals
- Assemble filing packages with auditability

## Architecture
- Domain: core models and policy checks
- Use Cases: application workflows (ingest, draft, review, export)
- Adapters: ports/interfaces for storage, LLM, and rendering
- Infrastructure: concrete implementations (in-memory stubs, Postgres, DOCX/PDF)
- Workflow: state machine and readiness checks

## Layout
- apps/api: FastAPI app
- apps/cli: CLI demo runner
- docs/architecture: architecture and workflow notes
- migrations: Postgres migration SQL + Alembic
- schemas: JSON schemas for data interchange
- src/patents: core packages (domain, usecases, adapters, infra, workflow)

## Quick Start (CLI Demo)
- Python 3.11+ recommended

```bash
cd /Users/aed/works/Patent/Patents
PYTHONPATH=./src python apps/cli/main.py --demo
```

## API Setup
1. Install dependencies

```bash
cd /Users/aed/works/Patent/Patents
python3 -m pip install -e .
```

2. Prepare Postgres

```bash
export PATENTS_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/patents"
alembic upgrade head
```

If you prefer raw SQL:
```bash
psql "$PATENTS_DATABASE_URL" -f migrations/001_init.sql
```

3. Run the API

```bash
uvicorn apps.api.main:app --reload
```

## API Auth (Optional)
- If `PATENTS_API_KEYS` is set, the API expects `X-API-Key` header.
- Format: `key:role` pairs separated by commas.

Example:
```bash
export PATENTS_API_KEYS="devkey:admin,reviewkey:reviewer"
```

Role gates:
- create invention: inventor, engineer, attorney, admin
- generate claims: engineer, attorney, admin
- compose spec: engineer, attorney, admin
- review: reviewer, attorney, admin
- IDS: analyst, attorney, admin
- export: attorney, admin

## Renderer Output
- Configure output format with `PATENTS_RENDERER` (`text`, `docx`, `pdf`)
- Configure output directory with `PATENTS_STORAGE_DIR`

Example:
```bash
export PATENTS_RENDERER=docx
export PATENTS_STORAGE_DIR=./output
```

## Notes
- API layer wires use cases to a Postgres backend
- DOCX/PDF renderers generate lightweight artifacts; replace with richer templates as needed
