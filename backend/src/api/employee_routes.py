# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Employee Access Request routes (subscription layer).

The submit endpoint is used by a signed-in employee, so it rides the ordinary
NextAuth branch of auth_middleware — never /api/admin, which an employee cannot
reach. Identity comes from request.state (populated by the middleware) and
never from the body, so a client cannot record a request as someone else.
No endpoint here checks auth itself.
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from src.models.employee_models import (
    EmployeeRequestCreate,
    EmployeeRequestResponse,
)
from src.services import company_service, employee_service
from src.services.employee_service import (
    ActiveRequestExistsError,
    DuplicateEmployeeRequestError,
    InvalidEmployeeIdError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/employees", tags=["employees"])

MAX_NAME_LENGTH = 255


def _error(status_code: int, error: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": error, "message": message, "details": None},
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/requests", response_model=EmployeeRequestResponse, status_code=201)
async def create_employee_request(body: EmployeeRequestCreate, request: Request):
    """Record a pending employee access request.

    Validated in a deliberate order so the employee gets the most useful
    message: the required fields, then the `adam-` ID shape, then the company,
    then the per-company duplicate.
    """
    employee_name = body.employee_name.strip()
    if not employee_name or len(employee_name) > MAX_NAME_LENGTH:
        raise _error(400, "missing_field", "Employee name is required.")

    raw_id = body.employee_id.strip()
    if not raw_id:
        raise _error(400, "missing_field", "Employee ID is required.")

    try:
        employee_id = employee_service.normalize_employee_id(raw_id)
    except InvalidEmployeeIdError:
        raise _error(
            400,
            "invalid_employee_id",
            "The ID must be 6-12 letters or digits "
            "(the adam- prefix is added automatically).",
        )

    raw_company_id = body.company_id.strip()
    if not raw_company_id.isdigit():
        raise _error(400, "missing_field", "Please choose a company to request.")

    company = await company_service.get_company(int(raw_company_id))
    if company is None:
        raise _error(404, "company_not_found", "Company not found.")

    try:
        record = await employee_service.create_employee_request(
            employee_name=employee_name,
            employee_id=employee_id,
            company_id=company["id"],
            # Snapshot of the name the employee actually saw in the dropdown.
            company_name=company["name"],
            account_user_id=request.state.user_id,
            account_email=getattr(request.state, "user_email", "") or "",
        )
    except ActiveRequestExistsError:
        raise _error(
            409,
            "active_request_exists",
            "You already have an active request. Cancel it before making a new one.",
        )
    except DuplicateEmployeeRequestError:
        raise _error(
            409,
            "employee_id_taken",
            "This ID has already requested this company.",
        )

    return EmployeeRequestResponse(**record)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
