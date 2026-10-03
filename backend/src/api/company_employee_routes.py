# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company Dashboard employee-management routes (company-JWT branch).

Everything here rides the company branch of auth_middleware, so a company
authenticates with the token issued by POST /api/company/login and its identity
comes from request.state.company_id — never from the request body, which makes
it unspoofable. No endpoint here checks auth itself.

Endpoints:
  GET    /api/company/employees              list (optional ?q=)
  POST   /api/company/employees/{id}/grant   grant access (FR-003)
  POST   /api/company/employees/{id}/revoke  un-grant (revert to pending)
  DELETE /api/company/employees/{id}         delete a request (FR-004)
  PATCH  /api/company/employees/{id}         assign/remove Manager (FR-019)
  GET    /api/company/{company_id}/logo      the signed-in company's logo (D9)
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from src.models.employee_models import (
    CompanyEmployee,
    DeleteResponse,
    EmployeeListResponse,
    EmployeeManagerUpdate,
)
from src.services import company_service, employee_service
from src.utils.company_logo_service import logo_content_type, logo_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/company", tags=["company-employees"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "error": "employee_not_found",
            "message": "No such employee for this company.",
            "details": None,
        },
    )


def _logo_not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "error": "logo_not_found",
            "message": "Company not found or it has no logo.",
            "details": None,
        },
    )


def _company_id(request: Request) -> int:
    """The signed-in company's id, taken from the verified token."""
    return int(request.state.company_id)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/employees", response_model=EmployeeListResponse)
async def list_company_employees(request: Request, q: Optional[str] = None):
    """Every employee record for the signed-in company, newest first (FR-001)."""
    employees = await employee_service.list_employees_for_company(_company_id(request), q)
    return EmployeeListResponse(employees=employees)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/employees/{employee_id}/grant", response_model=CompanyEmployee)
async def grant_employee_access(employee_id: int, request: Request):
    """Grant access — enables the specific signed-in account bound to the row."""
    employee = await employee_service.grant_access(_company_id(request), employee_id)
    if employee is None:
        raise _not_found()
    return CompanyEmployee(**employee)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/employees/{employee_id}/revoke", response_model=CompanyEmployee)
async def revoke_employee_access(employee_id: int, request: Request):
    """Revert a grant back to pending — the account loses application access."""
    employee = await employee_service.revoke_access(_company_id(request), employee_id)
    if employee is None:
        raise _not_found()
    return CompanyEmployee(**employee)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.delete("/employees/{employee_id}", response_model=DeleteResponse)
async def delete_company_employee(employee_id: int, request: Request):
    """Delete a request, revoking any access it had granted (FR-004)."""
    deleted = await employee_service.delete_employee(_company_id(request), employee_id)
    if not deleted:
        raise _not_found()
    return DeleteResponse(success=True, message="Employee request deleted.")


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.patch("/employees/{employee_id}", response_model=CompanyEmployee)
async def set_company_employee_manager(
    employee_id: int, body: EmployeeManagerUpdate, request: Request
):
    """Assign or remove the Manager role for an employee (FR-019)."""
    employee = await employee_service.set_manager(
        _company_id(request), employee_id, body.is_manager
    )
    if employee is None:
        raise _not_found()
    return CompanyEmployee(**employee)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/{company_id}/logo")
async def get_company_logo(company_id: int, request: Request):
    """Stream the signed-in company's logo.

    Fixes the logo_url returned by login under this same branch (D9): a company
    principal holds no NextAuth token, so the employee/admin logo endpoints are
    unreachable from the dashboard. The path id must match the token's company so
    a company cannot read another company's logo by guessing an id.
    """
    if _company_id(request) != company_id:
        raise _logo_not_found()

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
