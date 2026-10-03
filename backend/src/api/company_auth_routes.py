# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company Dashboard sign-in routes.

POST /api/company/login is the ONE company endpoint in this specification, and
it is the only public path under /api/company — every other path there is gated
by the company branch in auth_middleware. No endpoint here checks auth itself.
"""
import logging

from fastapi import APIRouter, HTTPException

from src.models.company_auth_models import (
    CompanyIdentity,
    CompanyLoginRequest,
    CompanyLoginResponse,
)
from src.services.company_auth_service import (
    CompanyAuthNotConfiguredError,
    issue_company_token,
    verify_company_credentials,
)
from src.services.company_crypto_service import EncryptionUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/company", tags=["company"])


def _invalid_credentials() -> HTTPException:
    """One generic denial — never discloses which field was wrong (FR-017)."""
    return HTTPException(
        status_code=401,
        detail={
            "error": "invalid_credentials",
            "message": "Invalid company name or password.",
            "details": None,
        },
    )


def _unavailable(error: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={"error": error, "message": message, "details": None},
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/login", response_model=CompanyLoginResponse)
async def company_login(body: CompanyLoginRequest):
    """Exchange company credentials for a 24-hour company session token."""
    name = (body.company_name or "").strip()
    if not name or not (body.password or ""):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_field",
                "message": "Company name and password are required.",
                "details": None,
            },
        )

    try:
        row = await verify_company_credentials(name, body.password)
    except EncryptionUnavailableError as exc:
        logger.error("Company sign-in unavailable: %s", exc)
        raise _unavailable(
            "encryption_unavailable",
            "Server encryption key is not configured.",
        )

    if row is None:
        logger.warning("Failed company sign-in attempt")
        raise _invalid_credentials()

    try:
        token, expires_at = issue_company_token(row["id"], row["name"])
    except CompanyAuthNotConfiguredError as exc:
        logger.error("Company auth is not configured: %s", exc)
        raise _unavailable(
            "company_auth_not_configured",
            "Company sign-in is not configured on the server.",
        )

    has_logo = bool(row.get("logo_filename"))
    identity = CompanyIdentity(
        id=str(row["id"]),
        name=row["name"],
        logo_url=f"/api/company/{row['id']}/logo" if has_logo else None,
    )
    logger.info("Company signed in: id=%s", row["id"])
    return CompanyLoginResponse(token=token, expires_at=expires_at, company=identity)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
