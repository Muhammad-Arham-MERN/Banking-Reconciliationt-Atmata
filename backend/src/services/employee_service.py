# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Employee service for the subscription layer's Employee Request flow.

All access uses raw asyncpg via db_service (no ORM), with $n placeholders.

This module is the single authority on what a valid employee ID is: the
subscription page's "Generate" button is a convenience, but every submitted
value is re-normalized and re-validated here. Duplicate (id, company) pairs
surface as a typed error for the route to translate into a 409.
"""
import logging
import re
from datetime import datetime
from typing import Any, Optional

import asyncpg

from src.services.db_service import db_service

logger = logging.getLogger(__name__)

ID_PREFIX = "adam-"
# After the prefix: 6-12 characters of lowercase letters and digits.
_ID_BODY_PATTERN = re.compile(r"^[a-z0-9]{6,12}$")

_COLUMNS = (
    "id, employee_name, employee_id, company_id, company_name, status, created_at"
)

# The company-dashboard view adds the submitter's email and the Manager flag.
_COMPANY_COLUMNS = (
    "id, employee_name, employee_id, company_id, company_name, "
    "account_email, status, is_manager, created_at"
)


class InvalidEmployeeIdError(Exception):
    """Raised when an employee ID does not fit the `adam-` shape."""


class DuplicateEmployeeRequestError(Exception):
    """Raised when this employee ID has already requested this company."""


class ActiveRequestExistsError(Exception):
    """Raised when the account already has a pending/accepted request (FR-017)."""


def _iso(value: Any) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def normalize_employee_id(raw: str) -> str:
    """Canonicalize an employee ID to `adam-` + 6-12 lowercase alphanumerics.

    Accepts a typed or generated value in any letter case, with or without the
    prefix, and never doubles an existing one. Storing the canonical lowercase
    form is what makes the (employee_id, company_id) unique index a plain index
    and what makes "Adam-A1B2C3" and "adam-a1b2c3" the same employee.

    Raises InvalidEmployeeIdError when the remainder is not the expected shape.
    """
    body = (raw or "").strip().lower()
    if body.startswith(ID_PREFIX):
        body = body[len(ID_PREFIX):]
    if not _ID_BODY_PATTERN.match(body):
        raise InvalidEmployeeIdError(raw)
    return f"{ID_PREFIX}{body}"


def employee_row_to_dict(row: dict) -> dict:
    """Shape a DB row into the API payload (ids stringified for JavaScript)."""
    return {
        "id": str(row["id"]),
        "employee_name": row["employee_name"],
        "employee_id": row["employee_id"],
        "company_id": str(row["company_id"]),
        "company_name": row["company_name"],
        "status": row["status"],
        "created_at": _iso(row.get("created_at")),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def create_employee_request(
    *,
    employee_name: str,
    employee_id: str,
    company_id: int,
    company_name: str,
    account_user_id: int,
    account_email: str,
) -> dict:
    """Record a pending access request and return it as an API dict.

    `employee_id` must already be normalized (see normalize_employee_id).
    Raises ActiveRequestExistsError when the account already holds a
    pending or accepted request to ANY company (FR-017/FR-025 — one active
    request per account). Raises DuplicateEmployeeRequestError when this ID has
    already requested this company — the composite unique index is the authority
    there, so the rule also holds when two submits race.
    """
    existing = await db_service.fetchrow(
        """
        SELECT id FROM employees
        WHERE account_user_id = $1 AND status IN ('pending', 'accepted')
        LIMIT 1
        """,
        account_user_id,
    )
    if existing is not None:
        raise ActiveRequestExistsError(account_user_id)

    try:
        row = await db_service.fetchrow(
            f"""
            INSERT INTO employees
                (employee_name, employee_id, company_id, company_name,
                 account_user_id, account_email, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'pending')
            RETURNING {_COLUMNS}
            """,
            employee_name,
            employee_id,
            company_id,
            company_name,
            account_user_id,
            account_email,
        )
    except asyncpg.UniqueViolationError as exc:
        raise DuplicateEmployeeRequestError(employee_id) from exc

    logger.info(
        "Recorded employee access request id=%s for company id=%s",
        row["id"],
        company_id,
    )
    return employee_row_to_dict(row)


def company_employee_row_to_dict(row: dict) -> dict:
    """Shape a DB row for the Company Dashboard (ids stringified)."""
    return {
        "id": str(row["id"]),
        "employee_name": row["employee_name"],
        "employee_id": row["employee_id"],
        "company_id": str(row["company_id"]),
        "company_name": row["company_name"],
        "account_email": row.get("account_email", "") or "",
        "status": row["status"],
        "is_manager": bool(row.get("is_manager")),
        "created_at": _iso(row.get("created_at")),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def list_employees_for_company(
    company_id: int, query: Optional[str] = None
) -> list[dict]:
    """Every employee record for a company, newest first (FR-001).

    `query` is an optional server-side filter matched case-insensitively against
    employee_id then employee_name. The dashboard filters client-side for an
    instant response (research D10); this exists for API parity.
    """
    if query and query.strip():
        like = f"%{query.strip().lower()}%"
        rows = await db_service.fetch(
            f"""
            SELECT {_COMPANY_COLUMNS}
            FROM employees
            WHERE company_id = $1
              AND (lower(employee_id) LIKE $2 OR lower(employee_name) LIKE $2)
            ORDER BY created_at DESC, id DESC
            """,
            company_id,
            like,
        )
    else:
        rows = await db_service.fetch(
            f"""
            SELECT {_COMPANY_COLUMNS}
            FROM employees
            WHERE company_id = $1
            ORDER BY created_at DESC, id DESC
            """,
            company_id,
        )
    return [company_employee_row_to_dict(row) for row in rows]


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def grant_access(company_id: int, employee_record_id: int) -> Optional[dict]:
    """Set an employee record to 'accepted', enabling its account (FR-003).

    Scoped by company_id so a company can never grant another company's record.
    Returns the updated employee dict, or None when no such record exists.
    """
    row = await db_service.fetchrow(
        f"""
        UPDATE employees
        SET status = 'accepted', updated_at = NOW()
        WHERE id = $1 AND company_id = $2
        RETURNING {_COMPANY_COLUMNS}
        """,
        employee_record_id,
        company_id,
    )
    if row is None:
        return None
    logger.info(
        "Granted access to employee record id=%s for company id=%s",
        row["id"],
        company_id,
    )
    return company_employee_row_to_dict(row)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def revoke_access(company_id: int, employee_record_id: int) -> Optional[dict]:
    """Revert a granted employee record back to 'pending' (un-grant).

    Scoped by company_id. The account immediately loses application access,
    because the membership gate resolves only 'accepted' rows. Returns the
    updated record, or None when no such record exists.
    """
    row = await db_service.fetchrow(
        f"""
        UPDATE employees
        SET status = 'pending', updated_at = NOW()
        WHERE id = $1 AND company_id = $2
        RETURNING {_COMPANY_COLUMNS}
        """,
        employee_record_id,
        company_id,
    )
    if row is None:
        return None
    logger.info(
        "Revoked access for employee record id=%s (company id=%s)",
        employee_record_id,
        company_id,
    )
    return company_employee_row_to_dict(row)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def delete_employee(company_id: int, employee_record_id: int) -> bool:
    """Delete an employee record, revoking any access it granted (FR-004).

    Scoped by company_id. Returns True when a record was removed, else False.
    """
    row = await db_service.fetchrow(
        "DELETE FROM employees WHERE id = $1 AND company_id = $2 RETURNING id",
        employee_record_id,
        company_id,
    )
    if row is None:
        return False
    logger.info(
        "Deleted employee record id=%s for company id=%s",
        employee_record_id,
        company_id,
    )
    return True


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def set_manager(
    company_id: int, employee_record_id: int, is_manager: bool
) -> Optional[dict]:
    """Assign or remove the Manager role for an employee (FR-019).

    The flag is additive: it only surfaces the Company Dashboard nav entry for
    an account that already holds accepted access, and never grants access on
    its own. Scoped by company_id; returns None when no such record exists.
    """
    row = await db_service.fetchrow(
        f"""
        UPDATE employees
        SET is_manager = $3, updated_at = NOW()
        WHERE id = $1 AND company_id = $2
        RETURNING {_COMPANY_COLUMNS}
        """,
        employee_record_id,
        company_id,
        is_manager,
    )
    if row is None:
        return None
    logger.info(
        "Set is_manager=%s on employee record id=%s for company id=%s",
        is_manager,
        employee_record_id,
        company_id,
    )
    return company_employee_row_to_dict(row)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
