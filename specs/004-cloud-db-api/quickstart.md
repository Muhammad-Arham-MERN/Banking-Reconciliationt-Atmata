# Quickstart: Cloud Database API Endpoints

**Feature**: 004-cloud-db-api | **Branch**: `004-cloud-db-api` | **Spec**: [spec.md](./spec.md)

## Prerequisites

- Python 3.11+
- Existing backend running with CockroachDB connected (DATABASE_URL configured)
- Dependencies: `sqlmodel`, `asyncpg`, `psycopg2-binary`, `greenlet`

## Installation

Add to `backend/requirements.prod.txt`:

```txt
sqlmodel>=0.0.22,<1.0
asyncpg>=0.28.0
psycopg2-binary>=2.9.0
greenlet>=3.0
```

Then:

```bash
cd backend
pip install -r requirements.prod.txt
pip install -r requirements.txt   # dev dependencies for testing
```

## Files to Create

| File | Purpose |
|------|---------|
| `backend/src/models/cloud_models.py` | SQLModel table model + Pydantic request/response models |
| `backend/src/services/cloud_service.py` | Business logic for cloud DB operations |
| `backend/src/api/cloud_routes.py` | FastAPI router with GET /api/cloud/files and POST /api/cloud/save |
| `backend/tests/contract/test_cloud_api.py` | Integration tests with httpx.AsyncClient |

## Files to Modify

| File | Change |
|------|--------|
| `backend/src/main.py` | Import and include `cloud_routes` router |
| `backend/requirements.prod.txt` | Add sqlmodel, asyncpg, psycopg2-binary, greenlet |
| `backend/requirements.txt` | Add httpx if not present (for integration testing) |

## Implementation Steps

### 1. SQLModel + Async Engine Setup

Create `backend/src/db/session.py` (new directory):

```python
from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config import settings

# Sync engine for table metadata operations (startup only)
sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

# Async engine for runtime database operations
async_engine = create_async_engine(
    settings.DATABASE_URL,  # Already uses postgresql:// protocol
    echo=False,
    future=True,
)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

**URL conversion note**: The existing `DATABASE_URL` is `postgresql://...`. For async, change to `postgresql+asyncpg://...` at the config level, or build the async URL in code by inserting `+asyncpg`.

### 2. SQLModel Table Model

`backend/src/models/cloud_models.py`:

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class ReconciliationData(SQLModel, table=True):
    __tablename__: str = "reconciliation_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str = Field(max_length=255, unique=True)
    # The existing column is named `data` (JSONB) — mapped via sa_column_kwargs
    file_data: dict | list = Field(sa_column_kwargs={"name": "data"})
    user_id: int = Field(foreign_key="users(id)")
    created_at: Optional[datetime] = Field(default=None)
```

### 3. Pydantic Request/Response Models

Same file, data-only (non-table) models:

```python
from pydantic import BaseModel, Field
from typing import Any


class SaveReconciliationRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_data: list[dict[str, Any]] = Field(..., min_length=1)


class FileListResponse(BaseModel):
    files: list[str]


class SaveSuccessResponse(BaseModel):
    success: bool = True
    message: str = "Reconciliation data saved successfully"
    file_name: str
```

### 4. Service Layer

`backend/src/services/cloud_service.py`:

```python
from src.db.session import async_session_factory
from src.models.cloud_models import ReconciliationData
from sqlmodel import select
from src.services.db_service import db_service


async def get_user_files(user_id: int) -> list[str]:
    """Retrieve file names from users.files JSONB column"""
    row = await db_service.fetchrow(
        "SELECT files FROM users WHERE id = $1", user_id
    )
    return row["files"] if row else []


async def save_reconciliation(
    user_id: int, file_name: str, file_data: list[dict]
) -> None:
    """Upsert a reconciliation record and sync users.files"""
    async with async_session_factory() as session:
        # Check if record exists
        stmt = select(ReconciliationData).where(
            ReconciliationData.file_name == file_name,
            ReconciliationData.user_id == user_id,
        )
        result = await session.exec(stmt)
        existing = result.one_or_none()

        if existing:
            # Upsert: update existing record
            existing.file_data = file_data
            session.add(existing)
        else:
            # Insert: create new record + append to users.files
            record = ReconciliationData(
                file_name=file_name,
                file_data=file_data,
                user_id=user_id,
            )
            session.add(record)
            # Also append file_name to users.files
            await db_service.execute(
                "UPDATE users SET files = files || $1::jsonb WHERE id = $2",
                f'["{file_name}"]',
                user_id,
            )

        await session.commit()
```

### 5. API Routes

`backend/src/api/cloud_routes.py`:

```python
from fastapi import APIRouter, Depends, Request
from src.models.cloud_models import (
    SaveReconciliationRequest,
    FileListResponse,
    SaveSuccessResponse,
)
from src.services.cloud_service import get_user_files, save_reconciliation

router = APIRouter(prefix="/api/cloud", tags=["cloud"])


@router.get("/files", response_model=FileListResponse)
async def list_cloud_files(request: Request):
    user_id = request.state.user_id
    files = await get_user_files(user_id)
    return FileListResponse(files=files)


@router.post("/save", response_model=SaveSuccessResponse)
async def save_cloud_data(
    request: Request,
    body: SaveReconciliationRequest,
):
    user_id = request.state.user_id
    await save_reconciliation(user_id, body.file_name, body.file_data)
    return SaveSuccessResponse(file_name=body.file_name)
```

### 6. Register Router

In `backend/src/main.py`, add:

```python
from src.api.cloud_routes import router as cloud_router
app.include_router(cloud_router)
```

### 7. Test

```bash
cd backend
pytest tests/contract/test_cloud_api.py -v
```

## API Reference

See [contracts/cloud-api.yaml](./contracts/cloud-api.yaml) for the full OpenAPI specification.

### GET /api/cloud/files

Returns `{ "files": ["file1", "file2", ...] }`.  
Requires `Authorization: Bearer <JWT>` header.

### POST /api/cloud/save

Request body:
```json
{
  "file_name": "my-reconciliation",
  "file_data": [
    {
      "name": "Vendor Payment",
      "description": "Monthly vendor payment",
      "debit_credit_value": 15000.00,
      "category": "Accounts Payable"
    }
  ]
}
```

Returns `{ "success": true, "message": "...", "file_name": "my-reconciliation" }`.
