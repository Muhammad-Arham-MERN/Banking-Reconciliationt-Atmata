# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Pydantic request/response models for the Admin Dashboard (Camri Desk) API.

Mirrors contracts/admin-api.yaml. All DB access happens through raw asyncpg
(db_service) — these models are the API layer only.
"""
from typing import Literal
from pydantic import BaseModel, Field

from src.models.employee_models import EmployeeStatus

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

# Rendered in the UI as Pending / Free Trial / Paid. Kept as safe, unspaced
# identifiers on the wire (never "Free Trial" as a key).
PaymentStatus = Literal["pending", "free_trial", "paid"]


class AdminLoginRequest(BaseModel):
    """POST /api/admin/login request body.

    Credentials travel in the JSON body, never the query string: the global
    security middleware inspects the URL for suspicious patterns and the auth
    middleware would otherwise see them in logs.
    """
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AdminLoginResponse(BaseModel):
    """POST /api/admin/login success response."""
    token: str
    # Server-side backstop only — the browser session ends when the browser
    # closes regardless of this expiry.
    expires_at: str


class CompanyWriteRequest(BaseModel):
    """Validated create/update payload for a company.

    The route builds this from multipart form fields so the same validation
    rules apply whether the logo file is present or not.
    """
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    price_rupees: int = Field(..., ge=0)
    payment_status: PaymentStatus = "pending"
    # Free-trial window (ISO YYYY-MM-DD). Required when payment_status is
    # "free_trial" — enforced by the route so the error envelope matches the
    # contract.
    trial_from: str | None = None
    trial_to: str | None = None


class Company(BaseModel):
    """A company as returned to the dashboard list.

    Carries NO password material — not the plaintext and not the Fernet
    ciphertext. `has_password` signals that a reveal is possible; the value is
    fetched on demand from the dedicated password endpoint.
    """
    # Stringified — CockroachDB SERIAL ids exceed JavaScript's safe integer
    # range, so a numeric JSON id would be rounded by the browser.
    id: str
    name: str
    logo_url: str | None = None
    has_password: bool = True
    price_rupees: int
    payment_status: PaymentStatus
    # Free-trial window the admin assigned (ISO dates) and the Start stamp.
    trial_from: str | None = None
    trial_to: str | None = None
    trial_started_at: str | None = None
    # Derived (never stored): the number of employee records for this company
    # (FR-018). Computed in the list query so the table shows it without N+1.
    employee_count: int = 0
    created_at: str
    updated_at: str


class CompanyListResponse(BaseModel):
    """GET /api/admin/companies response."""
    companies: list[Company]


class CompanyPasswordResponse(BaseModel):
    """GET /api/admin/companies/{id}/password response (decrypted on demand)."""
    password: str


class DeleteResponse(BaseModel):
    """DELETE /api/admin/companies/{id} success response."""
    success: bool = True
    message: str = "Company deleted successfully"


class AdminEmployee(BaseModel):
    """One employee in the admin companies-table hover roster (FR-018)."""
    # Stringified — CockroachDB SERIAL ids exceed JavaScript's safe integer range.
    id: str
    employee_name: str
    employee_id: str
    status: EmployeeStatus
    is_manager: bool = False


class AdminEmployeeListResponse(BaseModel):
    """GET /api/admin/companies/{id}/employees response."""
    employees: list[AdminEmployee]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
