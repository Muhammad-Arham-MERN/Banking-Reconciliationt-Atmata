# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Admin Dashboard (Camri Desk) API routes.

Developer-only surface for onboarding client companies: sign in, then list,
create, edit, reveal credentials for, and delete companies.

Auth: POST /api/admin/login is public; every other path here is gated by the
admin branch in auth_middleware (a dedicated admin JWT — see
src/services/admin_auth_service.py). No endpoint below checks auth itself.
"""
import logging
from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.models.admin_models import (
    AdminEmployeeListResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    Company,
    CompanyListResponse,
    CompanyPasswordResponse,
    DeleteResponse,
    PaymentStatus,
)
from src.models.company_request_models import CompanyRequestListResponse
from src.services import company_request_service, company_service
from src.services.admin_auth_service import (
    AdminAuthNotConfiguredError,
    issue_admin_token,
    verify_admin_credentials,
)
from src.services.company_crypto_service import (
    DecryptionError,
    EncryptionUnavailableError,
)
from src.services.company_service import DuplicateCompanyNameError
from src.utils.company_logo_service import (
    UnsupportedLogoTypeError,
    delete_logo,
    logo_content_type,
    logo_path,
    save_logo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _login_error() -> HTTPException:
    """One generic denial — never discloses which field was wrong (FR-004)."""
    return HTTPException(
        status_code=401,
        detail={
            "error": "invalid_credentials",
            "message": "Invalid username or password.",
            "details": None,
        },
    )


def _encryption_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "error": "encryption_unavailable",
            "message": "Server encryption key is not configured.",
            "details": None,
        },
    )


def _trial_window_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"error": "invalid_trial_window", "message": message, "details": None},
    )


def _parse_trial_window(
    effective_status: str | None,
    trial_from: str | None,
    trial_to: str | None,
) -> tuple[date | None, date | None]:
    """Validate and parse the free-trial From/To form fields.

    A blank string (an empty field) counts as absent. When the effective payment
    status is "free_trial" both bounds are required and From must not be after
    To; otherwise the bounds are optional and pass through unchanged.
    """
    clean_from = (trial_from or "").strip() or None
    clean_to = (trial_to or "").strip() or None

    def parse(value: str, field: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise _trial_window_error(f"{field} must be a valid date (YYYY-MM-DD).")

    parsed_from = parse(clean_from, "trial_from") if clean_from else None
    parsed_to = parse(clean_to, "trial_to") if clean_to else None

    if effective_status == "free_trial":
        if parsed_from is None or parsed_to is None:
            raise _trial_window_error(
                "A free trial requires both a From and a To date."
            )
        if parsed_from > parsed_to:
            raise _trial_window_error(
                "The trial From date must be on or before the To date."
            )

    return parsed_from, parsed_to


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(body: AdminLoginRequest):
    """Exchange the environment-configured admin credentials for an admin token."""
    try:
        credentials_ok = verify_admin_credentials(body.username, body.password)
        if not credentials_ok:
            logger.warning("Failed admin sign-in attempt")
            raise _login_error()
        token, expires_at = issue_admin_token()
    except AdminAuthNotConfiguredError as exc:
        logger.error("Admin auth is not configured: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "admin_auth_not_configured",
                "message": "Admin credentials are not configured on the server.",
                "details": None,
            },
        )

    logger.info("Admin signed in")
    return AdminLoginResponse(token=token, expires_at=expires_at)


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies():
    """List every registered company (no password material in the payload)."""
    companies = await company_service.list_companies()
    return CompanyListResponse(companies=companies)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/company-requests", response_model=CompanyRequestListResponse)
async def list_company_requests():
    """List onboarding requests, newest first — a view-only inbox (FR-006)."""
    requests = await company_request_service.list_company_requests()
    return CompanyRequestListResponse(requests=requests)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/companies/{company_id}/employees", response_model=AdminEmployeeListResponse)
async def list_company_employees(company_id: int):
    """A company's employee roster, for the companies-table hover modal (FR-018)."""
    employees = await company_service.list_employees_for_company(company_id)
    return AdminEmployeeListResponse(employees=employees)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/companies", response_model=Company, status_code=201)
async def create_company(
    name: str = Form(..., min_length=1, max_length=255),
    password: str = Form(..., min_length=1),
    price_rupees: int = Form(..., ge=0),
    payment_status: PaymentStatus = Form("pending"),
    trial_from: str | None = Form(None),
    trial_to: str | None = Form(None),
    logo: UploadFile | None = File(None),
):
    """Register a company, encrypting its access password at rest."""
    parsed_trial_from, parsed_trial_to = _parse_trial_window(
        payment_status, trial_from, trial_to
    )

    logo_filename = None
    if logo is not None and logo.filename:
        try:
            logo_filename = await save_logo(logo)
        except UnsupportedLogoTypeError as exc:
            raise HTTPException(
                status_code=415,
                detail={
                    "error": "unsupported_logo_type",
                    "message": str(exc),
                    "details": None,
                },
            )

    try:
        company = await company_service.create_company(
            name=name.strip(),
            password_plain=password,
            price_rupees=price_rupees,
            payment_status=payment_status,
            logo_filename=logo_filename,
            trial_from=parsed_trial_from,
            trial_to=parsed_trial_to,
        )
    except DuplicateCompanyNameError:
        # Roll back the just-written logo — the company was never created.
        delete_logo(logo_filename)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "company_name_exists",
                "message": "A company with this name already exists.",
                "details": None,
            },
        )
    except EncryptionUnavailableError as exc:
        delete_logo(logo_filename)
        raise _encryption_unavailable(exc)

    return Company(**company)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.put("/companies/{company_id}", response_model=Company)
async def update_company(
    company_id: int,
    name: str | None = Form(None, max_length=255),
    password: str | None = Form(None),
    price_rupees: int | None = Form(None, ge=0),
    payment_status: PaymentStatus | None = Form(None),
    trial_from: str | None = Form(None),
    trial_to: str | None = Form(None),
    logo: UploadFile | None = File(None),
):
    """Update a company. Omitted fields are left unchanged."""
    existing = await company_service.get_company(company_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": "Company not found.",
                "details": None,
            },
        )

    # Treat blank strings from the form as "not provided".
    clean_name = name.strip() if name and name.strip() else None
    clean_password = password if password else None

    # Validate the trial window against the status that will be in force after
    # this update — the supplied status, else the stored one when dates arrive.
    has_trial_input = bool((trial_from or "").strip()) or bool((trial_to or "").strip())
    effective_status = payment_status
    if effective_status is None and has_trial_input:
        effective_status = existing["payment_status"]
    parsed_trial_from, parsed_trial_to = _parse_trial_window(
        effective_status, trial_from, trial_to
    )

    new_logo_filename = None
    if logo is not None and logo.filename:
        try:
            new_logo_filename = await save_logo(logo)
        except UnsupportedLogoTypeError as exc:
            raise HTTPException(
                status_code=415,
                detail={
                    "error": "unsupported_logo_type",
                    "message": str(exc),
                    "details": None,
                },
            )

    try:
        company = await company_service.update_company(
            company_id,
            name=clean_name,
            password_plain=clean_password,
            price_rupees=price_rupees,
            payment_status=payment_status,
            logo_filename=new_logo_filename,
            trial_from=parsed_trial_from,
            trial_to=parsed_trial_to,
        )
    except DuplicateCompanyNameError:
        delete_logo(new_logo_filename)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "company_name_exists",
                "message": "A company with this name already exists.",
                "details": None,
            },
        )
    except EncryptionUnavailableError as exc:
        delete_logo(new_logo_filename)
        raise _encryption_unavailable(exc)

    # Replace succeeded — drop the previous logo file (best effort).
    if new_logo_filename and existing.get("logo_filename"):
        delete_logo(existing["logo_filename"])

    return Company(**company)


@router.delete("/companies/{company_id}", response_model=DeleteResponse)
async def delete_company(company_id: int):
    """Delete a company, revoking its access."""
    logo_filename = await company_service.delete_company(company_id)
    if logo_filename is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": "Company not found.",
                "details": None,
            },
        )

    # Row is gone; clean up its logo file (best effort).
    delete_logo(logo_filename)
    return DeleteResponse()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/companies/{company_id}/password", response_model=CompanyPasswordResponse)
async def reveal_company_password(company_id: int):
    """Decrypt and return a company's password on demand (reveal/copy).

    This is the only endpoint that ever returns a plaintext credential.
    """
    try:
        password = await company_service.reveal_password(company_id)
    except EncryptionUnavailableError as exc:
        raise _encryption_unavailable(exc)
    except DecryptionError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "decryption_failed",
                "message": str(exc),
                "details": None,
            },
        )

    if password is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": "Company not found.",
                "details": None,
            },
        )

    return CompanyPasswordResponse(password=password)


@router.get("/companies/{company_id}/logo")
async def get_company_logo(company_id: int):
    """Stream a company's logo with a safe, explicit content type."""
    row = await company_service.get_company(company_id)
    filename = row.get("logo_filename") if row else None
    if not filename:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "logo_not_found",
                "message": "Company not found or it has no logo.",
                "details": None,
            },
        )

    path = logo_path(filename)
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "logo_not_found",
                "message": "Company not found or it has no logo.",
                "details": None,
            },
        )

    return FileResponse(
        path,
        media_type=logo_content_type(filename),
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
        },
    )

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
