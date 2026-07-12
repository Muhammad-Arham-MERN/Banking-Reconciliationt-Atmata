# Research: Cloud Database API Endpoints

**Feature**: 004-cloud-db-api | **Date**: 2026-07-10 | **Plan**: [plan.md](./plan.md)

## Clarification 1: SQLModel + Existing asyncpg Setup

- **Decision**: Layer SQLModel's async engine alongside the existing raw asyncpg pool.
- **Rationale**: The existing `DatabaseService` (raw asyncpg pool) powers all current routes. FR-005 mandates SQLModel for new DB operations. Creating a separate SQLAlchemy async engine for SQLModel routes is the least invasive approach — existing routes keep working unchanged, new routes use SQLModel. Both share the same CockroachDB instance.
- **Pattern (from research)**:
  1. Create a **sync engine** via `sqlmodel.create_engine("postgresql://...")` for table metadata creation only
  2. Create an **async engine** via `sqlalchemy.ext.asyncio.create_async_engine("postgresql+asyncpg://...")` for runtime queries
  3. Wire an `AsyncSession` dependency via `sqlmodel.ext.asyncio.session.AsyncSession` with `sessionmaker`
  4. Call `SQLModel.metadata.create_all(sync_engine)` at startup alongside the existing migration runner
  5. Add `asyncpg`, `psycopg2-binary`, `greenlet`, `sqlmodel` to `requirements.prod.txt`
- **Alternatives considered**:
  - *Migrate existing pool to SQLAlchemy async engine*: Too invasive, would break existing routes
  - *Use sync SQLModel in async endpoints via run_in_executor*: Would block the event loop, worse performance

## Clarification 2: Existing Table Schema Alignment

- **Decision**: Use the existing tables as-is with ALTER TABLE to add only missing constraints/columns.
- **Rationale**: The `reconciliation_data` table already has `file_name VARCHAR(255) UNIQUE NOT NULL`, `data JSONB`, `user_id INTEGER REFERENCES users(id)`, `created_at TIMESTAMPTZ`. The `users.files` column is `JSONB DEFAULT '[]'::jsonb`. No schema changes are needed — the existing migrations already added all required columns. SQLModel models will map to these existing tables using `table=True` with the correct column names.
- **Mapping**:
  - `reconciliation_data.file_name` → SQLModel field `file_name: str`
  - `reconciliation_data.data` → SQLModel field `file_data: dict` (JSONB → dict mapping)
  - `reconciliation_data.user_id` → SQLModel field `user_id: int` (foreign key to users)
  - `users.files` → SQLModel field `files: list` (JSONB → list[str] mapping)
- **Test data**: Use a dedicated test schema or a separate test CockroachDB database. The existing migration script is idempotent (IF NOT EXISTS).

## Clarification 3: Test Strategy

- **Decision**: Use `httpx.AsyncClient` with the FastAPI `TestClient` for endpoint integration tests, backed by a real CockroachDB test database instance.
- **Rationale**: Mocking the database layer would miss real SQLModel/SQLAlchemy async behavior and CockroachDB-specific quirks. Using the actual database gives confidence in the upsert logic and auth integration. A test database is configured via a `TEST_DATABASE_URL` environment variable.
- **Pattern**: 
  1. Create a `conftest.py` with `TestClient` and `AsyncClient` fixtures
  2. Use `pytest-asyncio` for async test methods (already configured)
  3. Mock JWT token generation for authenticated test requests
  4. Clean up test data per test via deletion by `user_id`
  5. Add integration tests that cover all acceptance scenarios from spec
- **Alternatives considered**:
  - *SQLite in-memory*: SQLite doesn't support JSONB natively, and CockroachDB dialect differences would cause issues
  - *Full mocking*: Would miss real async query behavior and upsert edge cases

## Technology Choices

### SQLModel for ORM (FR-005)

- **Decision**: Use SQLModel `0.0.22+` (latest compatible with Python 3.11) with async support via `sqlmodel.ext.asyncio.session`
- **Rationale**: Explicitly mandated by FR-005. SQLModel provides Pydantic v2 integration (already in the stack) and SQLAlchemy ORM under the hood
- **Alternatives considered**: Raw asyncpg queries (violates FR-005), SQLAlchemy directly (not mandated, would add separate ORM)

### CockroachDB as Backend

- **Decision**: Use the existing CockroachDB Cloud instance (already configured via `DATABASE_URL`)
- **Rationale**: Already deployed and running. All migrations are idempotent. CockroachDB's PostgreSQL compatibility means SQLModel works seamlessly.
- **Alternatives considered**: Not applicable — the database is already chosen and running.

### JWT Auth (Existing Pattern)

- **Decision**: Use the existing `auth_middleware` and `auth_service` — no changes needed
- **Rationale**: FR-004 mandates auth on all endpoints. The existing middleware already checks JWT Bearer tokens and populates `request.state.user_id`. New endpoints just read `request.state.user_id`.
- **Alternatives considered**: None — reuse existing auth.

### Request Logging (Existing Pattern)

- **Decision**: No changes needed to the existing `log_requests` middleware
- **Rationale**: It's registered at the app level via `@app.middleware("http")` in `main.py` and already logs all requests. FR-010 is satisfied automatically.
- **Alternatives considered**: None — already handled by existing infrastructure.
