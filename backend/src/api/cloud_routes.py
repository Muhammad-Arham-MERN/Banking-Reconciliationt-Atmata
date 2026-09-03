# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Cloud Database API routes
Endpoints for storing and retrieving reconciliation data in CockroachDB.
"""
import logging
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from src.models.cloud_models import (
    SaveReconciliationRequest,
    FileListResponse,
    SaveSuccessResponse,
    PastFileListResponse,
    PastFileMeta,
    LoadPastFileResponse,
    CreatePastFileRequest,
    UpdatePastFileRequest,
    UpdatePastFileResponse,
    DeleteResponse,
    ExcelImportResponse,
)
from src.services.cloud_service import (
    get_user_files,
    save_reconciliation,
    get_user_files_meta,
    get_reconciliation,
    create_reconciliation,
    update_reconciliation,
    delete_reconciliation,
)
from src.services import past_files_excel_service
from src.utils.file_helpers import (
    save_uploaded_file,
    delete_file,
    validate_upload_file,
    get_file_path,
)
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cloud", tags=["cloud"])

EXCEL_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@router.get("/load_files_cloud", response_model=FileListResponse)
async def list_cloud_files(request: Request):
    """Return the list of stored file names for the authenticated user."""
    user_id = request.state.user_id
    files = await get_user_files(user_id)
    return FileListResponse(files=files)


@router.post("/save_files_cloud", response_model=SaveSuccessResponse)
async def save_cloud_data(
    request: Request,
    body: SaveReconciliationRequest,
):
    """Save or overwrite reconciliation data for the authenticated user."""
    user_id = request.state.user_id
    await save_reconciliation(user_id, body.file_name, body.file_data)
    return SaveSuccessResponse(file_name=body.file_name)


# ============================================================================
# Past Reconciliations — View / Create / Edit / Delete / Excel
# ============================================================================


@router.get("/files", response_model=PastFileListResponse)
async def list_past_files(request: Request):
    """Metadata for every stored past file (newest first)."""
    user_id = request.state.user_id
    files = await get_user_files_meta(user_id)
    return PastFileListResponse(files=[PastFileMeta(**meta) for meta in files])


@router.get("/files/{file_id}", response_model=LoadPastFileResponse)
async def load_past_file(request: Request, file_id: int):
    """Full contents of one stored past file (user-scoped)."""
    user_id = request.state.user_id
    file_data = await get_reconciliation(user_id, file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="Past reconciliation file not found")
    return LoadPastFileResponse(**file_data)


@router.post("/files", response_model=LoadPastFileResponse)
async def create_past_file(request: Request, body: CreatePastFileRequest):
    """Create a new (possibly empty) past reconciliation file."""
    user_id = request.state.user_id
    # Reject duplicate names for this user so the file list stays unambiguous.
    existing = await get_user_files_meta(user_id)
    if any(f["file_name"].lower() == body.file_name.lower() for f in existing):
        raise HTTPException(
            status_code=409,
            detail=f"A file named '{body.file_name}' already exists. Choose a different name.",
        )
    new_id = await create_reconciliation(
        user_id, body.file_name, body.reconciliation_type, body.file_data
    )
    return LoadPastFileResponse(
        file_id=str(new_id),
        file_name=body.file_name,
        reconciliation_type=body.reconciliation_type,
        discrepancies=body.file_data,
    )


@router.put("/files/{file_id}", response_model=UpdatePastFileResponse)
async def update_past_file(
    request: Request, file_id: int, body: UpdatePastFileRequest
):
    """Update a past file's data and/or rename it (user-scoped)."""
    user_id = request.state.user_id
    updated = await update_reconciliation(
        user_id, file_id, file_name=body.file_name, file_data=body.file_data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Past reconciliation file not found")
    return UpdatePastFileResponse(
        file_id=updated["file_id"],
        file_name=updated["file_name"],
        entry_count=len(updated["discrepancies"]),
    )


@router.delete("/files/{file_id}", response_model=DeleteResponse)
async def delete_past_file(request: Request, file_id: int):
    """Delete a stored past file (user-scoped)."""
    user_id = request.state.user_id
    deleted_name = await delete_reconciliation(user_id, file_id)
    if not deleted_name:
        raise HTTPException(status_code=404, detail="Past reconciliation file not found")
    return DeleteResponse(message=f"Past reconciliation '{deleted_name}' deleted successfully")


@router.get("/files/{file_id}/excel")
async def download_past_file_excel(request: Request, file_id: int):
    """Download the Edit template for a stored past file (prefilled)."""
    user_id = request.state.user_id
    file_data = await get_reconciliation(user_id, file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="Past reconciliation file not found")

    content = past_files_excel_service.build_template(
        file_data["reconciliation_type"], file_data["discrepancies"]
    )
    safe_name = past_files_excel_service.safe_filename_part(file_data["file_name"])
    filename = f"{safe_name}.xlsx"

    return StreamingResponse(
        iter([content]),
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/excel-template")
async def download_create_template(request: Request, reconciliation_type: str = "bank"):
    """Download an empty Create template (four empty category blocks)."""
    if reconciliation_type not in ("bank", "vendor"):
        raise HTTPException(status_code=400, detail="reconciliation_type must be 'bank' or 'vendor'")
    content = past_files_excel_service.build_template(reconciliation_type, [])
    filename = f"{reconciliation_type}-past-reconciliation-template.xlsx"

    return StreamingResponse(
        iter([content]),
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/files/import-excel", response_model=ExcelImportResponse)
async def import_past_file_excel(
    request: Request,
    file: UploadFile = File(...),
    file_id: int | None = Form(default=None),
    file_name: str | None = Form(default=None),
    reconciliation_type: str = Form(default="bank"),
):
    """
    Upload a filled template, parse it, and save the discrepancies.

    - file_id present  -> update that stored file (Edit with Excel)
    - file_id absent   -> create a new file (Create with Excel)
    The uploaded temp file is always deleted after processing.
    """
    user_id = request.state.user_id
    if not (file.filename or "").lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel file (.xlsx or .xls).",
        )

    file_path = get_file_path(file.filename or "upload.xlsx")
    try:
        content = await file.read()
        await save_uploaded_file(content, file_path)

        valid, errors = validate_upload_file(file_path, file.filename or "", "excel")
        if not valid:
            raise HTTPException(status_code=400, detail="; ".join(errors))

        try:
            discrepancies = past_files_excel_service.parse_template(content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if file_id is not None:
            existing = await get_reconciliation(user_id, file_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Past reconciliation file not found")
            target_name = file_name or existing["file_name"]
            updated = await update_reconciliation(
                user_id, file_id, file_name=target_name, file_data=discrepancies
            )
            final_id = updated["file_id"]
            final_name = updated["file_name"]
        else:
            target_name = (file_name or "").strip()
            if not target_name:
                raise HTTPException(
                    status_code=400, detail="file_name is required when creating a new file"
                )
            final_id = str(
                await create_reconciliation(
                    user_id, target_name, reconciliation_type, discrepancies
                )
            )
            final_name = target_name

        return ExcelImportResponse(
            file_id=final_id,
            file_name=final_name,
            reconciliation_type=existing["reconciliation_type"]
            if file_id is not None
            else reconciliation_type,
            entry_count=len(discrepancies),
            discrepancies=discrepancies,
        )
    finally:
        if file_path.exists():
            delete_file(file_path)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
