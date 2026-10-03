# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Membership service — the application authorization derived from `employees`.

A membership is not its own table: it is the signed-in account's single
`accepted` employee row. Its existence is what gates the application (FR-009/
FR-010), and deleting the row revokes that access (FR-015/FR-017). The
membership is a gate only — it never grants the company visibility into the
employee's own reconciliation data (FR-024).

All access uses raw asyncpg via db_service (no ORM), with $n placeholders.
"""
import logging
from typing import Optional

from src.services.db_service import db_service

logger = logging.getLogger(__name__)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def get_accepted_membership(account_user_id: int) -> Optional[dict]:
    """Resolve the account's accepted membership, or None when it has none.

    Returns the membership shape (ids stringified) for the API layer; this is
    the single lookup the gate adds per gated request.
    """
    row = await db_service.fetchrow(
        """
        SELECT id, employee_id, employee_name, company_id, company_name,
               status, is_manager
        FROM employees
        WHERE account_user_id = $1 AND status = 'accepted'
        LIMIT 1
        """,
        account_user_id,
    )
    if row is None:
        return None
    return {
        # Stringified — CockroachDB SERIAL ids exceed JS's safe integer range.
        "id": str(row["id"]),
        "employee_id": row["employee_id"],
        "employee_name": row["employee_name"],
        "company_id": str(row["company_id"]),
        "company_name": row["company_name"],
        "status": "accepted",
        "is_manager": bool(row["is_manager"]),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def delete_membership(account_user_id: int) -> bool:
    """Hard-delete the account's employee record.

    This single operation serves BOTH cancelling a pending request (FR-017) and
    leaving a granted company (FR-015): access is revoked either way and the
    user account itself is untouched. Returns True when a row was removed.
    """
    row = await db_service.fetchrow(
        "DELETE FROM employees WHERE account_user_id = $1 RETURNING id",
        account_user_id,
    )
    if row is None:
        return False
    logger.info("Removed membership for account_user_id=%s", account_user_id)
    return True


async def count_for_company(company_id: int) -> int:
    """Number of employee records associated with a company (FR-018 support)."""
    row = await db_service.fetchrow(
        "SELECT COUNT(*) AS count FROM employees WHERE company_id = $1",
        company_id,
    )
    return int(row["count"]) if row else 0

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
