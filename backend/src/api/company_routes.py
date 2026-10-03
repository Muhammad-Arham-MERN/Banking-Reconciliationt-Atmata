# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company routes for signed-in (non-admin) users.

The Employee Request dropdown needs the Developer's company list and their
logos, but an employee holds no admin token and /api/admin/* is pinned behind
the admin branch of auth_middleware. These endpoints therefore live under
/api/companies, which rides the ordinary NextAuth branch: any signed-in Google
user may read them, and nothing else. No endpoint here checks auth itself.
"""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.models.employee_models import CompanyOption, CompanyOptionListResponse
from src.services import company_service
from src.utils.company_logo_service import logo_content_type, logo_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["companies"])


def _logo_not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "error": "logo_not_found",
            "message": "Company not found or it has no logo.",
            "details": None,
        },
    )


@router.get("", response_model=CompanyOptionListResponse)
async def list_company_options():
    """Every company the Developer has onboarded, for the request dropdown.

    The logo is exposed as a path rather than inline bytes, and the path points
    at THIS module's endpoint (not the admin one, which an employee cannot call).
    """
    companies = await company_service.list_companies()
    return CompanyOptionListResponse(
        companies=[
            CompanyOption(
                id=company["id"],
                name=company["name"],
                logo_url=(
                    f"/api/companies/{company['id']}/logo"
                    if company["logo_url"]
                    else None
                ),
            )
            for company in companies
        ]
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/{company_id}/logo")
async def get_company_logo(company_id: int):
    """Stream a company logo to a signed-in employee.

    Mirrors the admin logo endpoint's safety headers. The frontend fetches this
    as a blob because an <img> cannot carry the Bearer token.
    """
    row = await company_service.get_company(company_id)
    filename = row.get("logo_filename") if row else None
    if not filename:
        raise _logo_not_found()

    path = logo_path(filename)
    if not path.is_file():
        raise _logo_not_found()

    return FileResponse(
        path,
        media_type=logo_content_type(filename),
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
        },
    )

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
