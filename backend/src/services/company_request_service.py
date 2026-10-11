# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company onboarding-request service (FR-006).

Persists "Company Request" submissions for the Admin Dashboard's view-only
Company Requests category. A request has no status and no link to company
account creation — it exists only to be read (and to trigger the notification
email). All access uses raw asyncpg via db_service (no ORM), with $n
placeholders.
"""
import logging
from datetime import datetime
from typing import Any

from src.services.db_service import db_service

logger = logging.getLogger(__name__)

_COLUMNS = (
    "id, company_name, role, website_socials, email, phone, submitted_at"
)


def _iso(value: Any) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def company_request_row_to_dict(row: dict) -> dict:
    """Shape a DB row into the API payload (id stringified for JavaScript)."""
    return {
        "id": str(row["id"]),
        "company_name": row["company_name"],
        "role": row["role"],
        "website_socials": row["website_socials"],
        "email": row["email"],
        "phone": row["phone"],
        "submitted_at": _iso(row.get("submitted_at")),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def create_company_request(
    *,
    company_name: str,
    role: str,
    website_socials: str,
    email: str,
    phone: str,
    account_user_id: int,
    account_email: str,
) -> dict:
    """Persist a company onboarding request and return it as an API dict."""
    row = await db_service.fetchrow(
        f"""
        INSERT INTO company_requests
            (company_name, role, website_socials, email, phone,
             account_user_id, account_email)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING {_COLUMNS}
        """,
        company_name,
        role,
        website_socials,
        email,
        phone,
        account_user_id,
        account_email,
    )
    logger.info("Stored company onboarding request id=%s", row["id"])
    return company_request_row_to_dict(row)


async def list_company_requests() -> list[dict]:
    """Every onboarding request, newest first (admin inbox, FR-006)."""
    rows = await db_service.fetch(
        f"SELECT {_COLUMNS} FROM company_requests ORDER BY submitted_at DESC, id DESC"
    )
    return [company_request_row_to_dict(row) for row in rows]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
