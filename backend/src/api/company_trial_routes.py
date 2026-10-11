# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company Dashboard free-trial routes (company-JWT branch).

The Developer assigns a free-trial window from the Admin Dashboard; the company
sees it here and activates it by clicking Start. Everything rides the company
branch of auth_middleware, so the company authenticates with the token issued by
POST /api/company/login and its identity comes from request.state.company_id —
never from the request body, which makes it unspoofable. No endpoint here checks
auth itself.

Endpoints:
  GET  /api/company/trial        the signed-in company's assigned trial + state
  POST /api/company/trial/start  stamp the Start time (idempotent)
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from src.models.company_auth_models import CompanyTrialState
from src.services import company_service
from src.services.company_service import TrialExpiredError, TrialNotAssignedError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/company", tags=["company-trial"])


def _company_id(request: Request) -> int:
    """The signed-in company's id, taken from the verified token."""
    return int(request.state.company_id)


def _trial_state(row: dict) -> CompanyTrialState:
    """Build the wire payload (status + ISO dates) from a row or API dict."""
    return CompanyTrialState(
        status=company_service.compute_trial_state(row),
        trial_from=row.get("trial_from"),
        trial_to=row.get("trial_to"),
        trial_started_at=row.get("trial_started_at"),
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/trial", response_model=CompanyTrialState)
async def get_company_trial(request: Request):
    """The signed-in company's assigned free-trial window and its current state."""
    company_id = _company_id(request)
    row = await company_service.get_company(company_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": "Company not found.",
                "details": None,
            },
        )
    return _trial_state(company_service.company_row_to_dict(row))


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/trial/start", response_model=CompanyTrialState)
async def start_company_trial(request: Request):
    """Activate the company's free trial (idempotent once started).

    Fails with 400 when the admin never assigned a window, or when the assigned
    window already ended. Starting does not require the window's From date to
    have arrived — access simply unlocks on/after that date.
    """
    company_id = _company_id(request)
    try:
        company = await company_service.start_company_trial(company_id)
    except TrialNotAssignedError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "trial_not_assigned",
                "message": "No free trial has been assigned to your company yet.",
                "details": None,
            },
        )
    except TrialExpiredError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "trial_expired",
                "message": "This free-trial window has already ended. Ask for a new one.",
                "details": None,
            },
        )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": "Company not found.",
                "details": None,
            },
        )

    return _trial_state(company)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
