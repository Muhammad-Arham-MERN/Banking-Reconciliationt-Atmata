# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Pydantic request/response models for the Cloud Database API endpoints.
SQLModel has been removed — all DB operations use raw asyncpg via db_service.
"""
from typing import Any, Literal
from pydantic import BaseModel, Field


class SaveReconciliationRequest(BaseModel):
    """POST /api/cloud/save request body."""
    file_name: str = Field(..., min_length=1, max_length=255)
    file_data: list[dict[str, Any]] = Field(..., min_length=0)


class FileListResponse(BaseModel):
    """GET /api/cloud/files response."""
    files: list[str]


class SaveSuccessResponse(BaseModel):
    """POST /api/cloud/save success response."""
    success: bool = True
    message: str = "Reconciliation data saved successfully"
    file_name: str


# ============================================================================
# Past Reconciliations — View / Create / Edit / Delete / Excel
# ============================================================================

ReconciliationType = Literal["bank", "vendor"]


class PastFileMeta(BaseModel):
    """Metadata for one stored past reconciliation file.

    file_id is a STRING: CockroachDB SERIAL keys exceed JavaScript's safe
    integer range, so a numeric JSON id would be rounded on the frontend and
    every subsequent id-based lookup would 404.
    """
    file_id: str
    file_name: str
    created_at: str
    entry_count: int
    reconciliation_type: str


class PastFileListResponse(BaseModel):
    """GET /api/cloud/files response (metadata list, newest first)."""
    files: list[PastFileMeta]


class LoadPastFileResponse(BaseModel):
    """GET /api/cloud/files/{file_id} response (full file contents)."""
    file_id: str
    file_name: str
    reconciliation_type: str
    discrepancies: list[dict[str, Any]]


class CreatePastFileRequest(BaseModel):
    """POST /api/cloud/files request body."""
    file_name: str = Field(..., min_length=1, max_length=255)
    reconciliation_type: ReconciliationType = "bank"
    file_data: list[dict[str, Any]] = Field(default_factory=list)


class UpdatePastFileRequest(BaseModel):
    """PUT /api/cloud/files/{file_id} request body (both fields optional)."""
    file_name: str | None = Field(default=None, min_length=1, max_length=255)
    file_data: list[dict[str, Any]] | None = None


class UpdatePastFileResponse(BaseModel):
    """PUT /api/cloud/files/{file_id} success response."""
    success: bool = True
    message: str = "Past reconciliation updated successfully"
    file_id: str
    file_name: str
    entry_count: int


class DeleteResponse(BaseModel):
    """DELETE /api/cloud/files/{file_id} success response."""
    success: bool = True
    message: str = "Past reconciliation deleted successfully"


class ExcelImportResponse(BaseModel):
    """POST /api/cloud/files/import-excel success response."""
    success: bool = True
    message: str = "Excel file parsed and saved successfully"
    file_id: str
    file_name: str
    reconciliation_type: str = "bank"
    entry_count: int
    discrepancies: list[dict[str, Any]]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
