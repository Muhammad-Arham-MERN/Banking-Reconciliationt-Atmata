# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Pydantic request/response models for the Cloud Database API endpoints.
SQLModel has been removed — all DB operations use raw asyncpg via db_service.
"""
from typing import Any
from pydantic import BaseModel, Field


class SaveReconciliationRequest(BaseModel):
    """POST /api/cloud/save request body."""
    file_name: str = Field(..., min_length=1, max_length=255)
    file_data: list[dict[str, Any]] = Field(..., min_length=1)


class FileListResponse(BaseModel):
    """GET /api/cloud/files response."""
    files: list[str]


class SaveSuccessResponse(BaseModel):
    """POST /api/cloud/save success response."""
    success: bool = True
    message: str = "Reconciliation data saved successfully"
    file_name: str

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
