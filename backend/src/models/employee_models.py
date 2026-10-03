# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Pydantic request/response models for the Employee Access Request API
(subscription layer).

Mirrors contracts/employee-api.yaml. All DB access happens through raw asyncpg
(db_service) — these models are the API layer only.

Field constraints are deliberately left to the route: a pydantic length failure
would return FastAPI's own 422 envelope, whereas the contract specifies the
project's {"error","message","details"} 400 for missing fields.
"""
from typing import Literal
from pydantic import BaseModel

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

# Stored on the row. This feature only ever writes "pending" — accept/deny is
# the later company specification's job, but the value is declared now so that
# spec needs no schema change.
EmployeeStatus = Literal["pending", "accepted", "denied"]


class CompanyOption(BaseModel):
    """One entry in the Employee Request company dropdown."""
    # Stringified — CockroachDB SERIAL ids exceed JavaScript's safe integer range.
    id: str
    name: str
    # Path to the signed-in-company logo endpoint, or None when the company has
    # no logo (the dropdown then shows a placeholder).
    logo_url: str | None = None


class CompanyOptionListResponse(BaseModel):
    """GET /api/companies response."""
    companies: list[CompanyOption]


class EmployeeRequestCreate(BaseModel):
    """POST /api/employees/requests request body.

    `employee_id` may arrive with or without the `adam-` prefix and in any
    letter case; the service normalizes it before validation.
    """
    employee_name: str
    employee_id: str
    company_id: str


class EmployeeRequestResponse(BaseModel):
    """POST /api/employees/requests success response."""
    id: str
    employee_name: str
    employee_id: str
    company_id: str
    company_name: str
    status: EmployeeStatus
    created_at: str


class CompanyEmployee(BaseModel):
    """One employee row as shown in the Company Dashboard's Employees table."""
    # Stringified — CockroachDB SERIAL ids exceed JavaScript's safe integer range.
    id: str
    employee_name: str
    employee_id: str
    company_id: str
    company_name: str
    account_email: str = ""
    status: EmployeeStatus
    # Additive Manager flag (FR-019) — never grants application access on its own.
    is_manager: bool = False
    created_at: str


class EmployeeListResponse(BaseModel):
    """GET /api/company/employees response."""
    employees: list[CompanyEmployee]


class EmployeeManagerUpdate(BaseModel):
    """PATCH /api/company/employees/{id} request body (FR-019)."""
    is_manager: bool


class Membership(BaseModel):
    """The signed-in account's accepted company membership.

    Resolved from a single `accepted` employees row; it is the application
    authorization gate (FR-009/FR-010) and drives the membership-aware nav.
    """
    id: str
    employee_id: str
    employee_name: str = ""
    company_id: str
    company_name: str
    status: Literal["accepted"] = "accepted"
    is_manager: bool = False


class MembershipResponse(BaseModel):
    """GET /api/me/membership response — `membership` is null when there is none."""
    membership: Membership | None = None


class DeleteResponse(BaseModel):
    """Generic delete/cancel acknowledgement ({success,message})."""
    success: bool = True
    message: str

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
