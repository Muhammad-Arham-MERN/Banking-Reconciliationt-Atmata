# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company onboarding-request routes (NextAuth branch).

A signed-in account submits the "Company Request" onboarding flow here. The
submission is persisted for the Admin Dashboard's view-only Company Requests
category and a notification email is sent to the Developer best-effort — an
email failure never fails the request (FR-006/FR-007). Identity comes from
request.state (populated by the middleware), never from the body. No endpoint
here checks auth itself.

Note the path: /api/company-requests is deliberately NOT under /api/company, so
it rides the ordinary NextAuth branch rather than the company-JWT branch.
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from src.models.company_request_models import CompanyRequest, CompanyRequestCreate
from src.services import company_request_service, notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/company-requests", tags=["company-requests"])

MAX_NAME_LENGTH = 255


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("", response_model=CompanyRequest, status_code=201)
async def create_company_request(body: CompanyRequestCreate, request: Request):
    """Store a company onboarding request, then best-effort notify the Developer."""
    company_name = (body.company_name or "").strip()
    if not company_name or len(company_name) > MAX_NAME_LENGTH:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_field",
                "message": "Company name is required.",
                "details": None,
            },
        )

    record = await company_request_service.create_company_request(
        company_name=company_name,
        role=(body.role or "").strip()[:255],
        website_socials=(body.website_socials or "").strip()[:255],
        email=(body.email or "").strip()[:255],
        phone=(body.phone or "").strip()[:64],
        account_user_id=request.state.user_id,
        account_email=getattr(request.state, "user_email", "") or "",
    )

    # Best-effort: the row is already stored, so a mail failure must not fail
    # the request (FR-007). The service never raises.
    await notification_service.send_company_request_notification(record)

    return CompanyRequest(**record)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
