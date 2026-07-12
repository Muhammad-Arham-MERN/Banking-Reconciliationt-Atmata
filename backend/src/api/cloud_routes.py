# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Cloud Database API routes
Endpoints for storing and retrieving reconciliation data in CockroachDB.
"""
import logging
from fastapi import APIRouter, Request
from src.models.cloud_models import (
    SaveReconciliationRequest,
    FileListResponse,
    SaveSuccessResponse,
)
from src.services.cloud_service import get_user_files, save_reconciliation
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cloud", tags=["cloud"])


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

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
