# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company service for the Admin Dashboard (Camri Desk).

All access uses raw asyncpg via db_service (no ORM), with $n placeholders.
Passwords are encrypted on the way in and decrypted only on explicit reveal —
the plaintext never touches the database.
"""
import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

import asyncpg

from src.services.company_crypto_service import encrypt_password, decrypt_password
from src.services.db_service import db_service

logger = logging.getLogger(__name__)

_COLUMNS = (
    "id, name, logo_filename, password_encrypted, price_rupees, "
    "payment_status, trial_from, trial_to, trial_started_at, created_at, updated_at"
)

# Same columns, table-qualified for the employee-count join.
_SELECT_COLUMNS = (
    "c.id, c.name, c.logo_filename, c.password_encrypted, c.price_rupees, "
    "c.payment_status, c.trial_from, c.trial_to, c.trial_started_at, "
    "c.created_at, c.updated_at"
)


class DuplicateCompanyNameError(Exception):
    """Raised when a company name already exists (case-insensitive)."""


class TrialNotAssignedError(Exception):
    """Raised when a company tries to start a trial the admin never assigned."""


class TrialExpiredError(Exception):
    """Raised when a company tries to start a trial whose window already ended."""


def _iso(value: Any) -> str:
    return value.isoformat() if isinstance(value, (datetime, date)) else str(value)


def _maybe_iso(value: Any) -> Optional[str]:
    return None if value is None else _iso(value)


def _as_date(value: Any) -> Optional[date]:
    """Coerce a DATE column or an ISO string into a `date` (None when absent)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def compute_trial_state(row: dict) -> str:
    """Derive a company's free-trial state from its stored columns.

    Accepts either a raw DB row (DATE/datetime values) or an API dict (ISO
    strings). One of:
      - "not_assigned": the admin has not set a window (or only one bound).
      - "not_started":  a window exists but the company has not clicked Start.
      - "scheduled":    started, but the window's From date is still ahead.
      - "active":       started and today is within [trial_from, trial_to].
      - "expired":      started and today is past trial_to.
    """
    trial_from = _as_date(row.get("trial_from"))
    trial_to = _as_date(row.get("trial_to"))
    if trial_from is None or trial_to is None:
        return "not_assigned"
    if row.get("trial_started_at") is None:
        return "not_started"
    today = datetime.now(timezone.utc).date()
    if today < trial_from:
        return "scheduled"
    if today > trial_to:
        return "expired"
    return "active"


def trial_is_active(row: dict) -> bool:
    """True when the company's trial currently unlocks employee access."""
    return compute_trial_state(row) == "active"


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def company_row_to_dict(row: dict) -> dict:
    """Shape a DB row into the API payload.

    Deliberately omits the password and its ciphertext: the list response must
    not carry secret material. `has_password` signals that a reveal is possible;
    the value itself comes from the dedicated reveal endpoint.
    """
    company_id = row["id"]
    has_logo = bool(row.get("logo_filename"))
    return {
        # Stringified — CockroachDB SERIAL exceeds JS's safe integer range.
        "id": str(company_id),
        "name": row["name"],
        "logo_url": f"/api/admin/companies/{company_id}/logo" if has_logo else None,
        "has_password": bool(row.get("password_encrypted")),
        "price_rupees": row["price_rupees"],
        "payment_status": row["payment_status"],
        # Free-trial window assigned by the admin + the Start stamp.
        "trial_from": _maybe_iso(row.get("trial_from")),
        "trial_to": _maybe_iso(row.get("trial_to")),
        "trial_started_at": _maybe_iso(row.get("trial_started_at")),
        # Derived (never stored): the company's employee records (FR-018).
        "employee_count": int(row.get("employee_count", 0) or 0),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
    }


async def list_companies() -> list[dict]:
    """Every registered company, newest first, with its employee count.

    The count is computed in one LEFT JOIN so the admin table shows it without
    an N+1 query per row (FR-018).
    """
    rows = await db_service.fetch(
        f"""
        SELECT {_SELECT_COLUMNS}, COALESCE(counts.employee_count, 0) AS employee_count
        FROM companies c
        LEFT JOIN (
            SELECT company_id, COUNT(*) AS employee_count
            FROM employees
            GROUP BY company_id
        ) AS counts ON counts.company_id = c.id
        ORDER BY c.created_at DESC, c.id DESC
        """
    )
    return [company_row_to_dict(row) for row in rows]


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def list_employees_for_company(company_id: int) -> list[dict]:
    """A company's employee records, newest first — the admin hover roster (FR-018).

    Returns the AdminEmployee shape (ids stringified, manager flag included).
    """
    rows = await db_service.fetch(
        """
        SELECT id, employee_name, employee_id, status, is_manager
        FROM employees
        WHERE company_id = $1
        ORDER BY created_at DESC, id DESC
        """,
        company_id,
    )
    return [
        {
            "id": str(row["id"]),
            "employee_name": row["employee_name"],
            "employee_id": row["employee_id"],
            "status": row["status"],
            "is_manager": bool(row.get("is_manager")),
        }
        for row in rows
    ]


async def get_company(company_id: int) -> Optional[dict]:
    """One raw company row (includes password_encrypted) or None."""
    return await db_service.fetchrow(
        f"SELECT {_COLUMNS} FROM companies WHERE id = $1",
        company_id,
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def get_company_by_name(name: str) -> Optional[dict]:
    """One raw company row matched case-insensitively on the given name.

    The company name is the company's sign-in identifier (FR-027). The existing
    uq_company_name_lower index serves this lookup efficiently. Includes
    password_encrypted so the caller can verify it — it is never returned to the
    client.
    """
    return await db_service.fetchrow(
        f"SELECT {_COLUMNS} FROM companies WHERE lower(name) = lower($1) LIMIT 1",
        name,
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def create_company(
    name: str,
    password_plain: str,
    price_rupees: int,
    payment_status: str,
    logo_filename: Optional[str] = None,
    trial_from: Optional[date] = None,
    trial_to: Optional[date] = None,
) -> dict:
    """Create a company. The password is encrypted before it reaches the DB.

    Raises EncryptionUnavailableError (from the crypto service) when the Fernet
    key is unusable — nothing is written in that case.
    """
    encrypted = encrypt_password(password_plain)

    try:
        row = await db_service.fetchrow(
            f"""
            INSERT INTO companies
                (name, logo_filename, password_encrypted, price_rupees,
                 payment_status, trial_from, trial_to)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING {_COLUMNS}
            """,
            name, logo_filename, encrypted, price_rupees, payment_status,
            trial_from, trial_to,
        )
    except asyncpg.UniqueViolationError as exc:
        raise DuplicateCompanyNameError(name) from exc

    logger.info("Created company '%s' (id=%s)", name, row["id"])
    return company_row_to_dict(row)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def update_company(
    company_id: int,
    *,
    name: Optional[str] = None,
    password_plain: Optional[str] = None,
    price_rupees: Optional[int] = None,
    payment_status: Optional[str] = None,
    logo_filename: Optional[str] = None,
    trial_from: Optional[date] = None,
    trial_to: Optional[date] = None,
) -> Optional[dict]:
    """Partially update a company. Only the supplied fields change.

    The password is re-encrypted only when a new one is provided. When the
    free-trial window actually changes the Start stamp is cleared, so a
    re-assigned trial must be Started again. Setting the status back to
    "pending" REVOKES the free trial outright (window + Start stamp cleared), so
    the company's employees lose access until a new trial is assigned. Returns
    the updated row as an API dict, or None when the company does not exist.
    """
    assignments: list[str] = []
    values: list[Any] = []

    def add(column: str, value: Any) -> None:
        values.append(value)
        assignments.append(f"{column} = ${len(values)}")

    # A "pending" status revokes the trial, so its dates are not set below.
    revoking_trial = payment_status == "pending"

    if name is not None:
        add("name", name)
    if password_plain is not None:
        add("password_encrypted", encrypt_password(password_plain))
    if price_rupees is not None:
        add("price_rupees", price_rupees)
    if payment_status is not None:
        add("payment_status", payment_status)
    if logo_filename is not None:
        add("logo_filename", logo_filename)

    if not revoking_trial and (trial_from is not None or trial_to is not None):
        current = await db_service.fetchrow(
            "SELECT trial_from, trial_to FROM companies WHERE id = $1",
            company_id,
        )
        if current is not None:
            new_from = trial_from if trial_from is not None else current["trial_from"]
            new_to = trial_to if trial_to is not None else current["trial_to"]
            if new_from != current["trial_from"] or new_to != current["trial_to"]:
                add("trial_from", new_from)
                add("trial_to", new_to)
                # A newly (re)assigned window must be Started again.
                assignments.append("trial_started_at = NULL")

    # Revoke: back to "pending" clears the whole trial so the membership gate
    # (which needs an active, started, in-window trial) refuses the employees.
    if revoking_trial:
        assignments.append("trial_from = NULL")
        assignments.append("trial_to = NULL")
        assignments.append("trial_started_at = NULL")

    assignments.append("updated_at = NOW()")
    values.append(company_id)

    try:
        row = await db_service.fetchrow(
            f"""
            UPDATE companies
            SET {", ".join(assignments)}
            WHERE id = ${len(values)}
            RETURNING {_COLUMNS}
            """,
            *values,
        )
    except asyncpg.UniqueViolationError as exc:
        raise DuplicateCompanyNameError(name or "") from exc

    if row is None:
        return None

    logger.info("Updated company id=%s", company_id)
    return company_row_to_dict(row)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def start_company_trial(company_id: int) -> Optional[dict]:
    """Stamp the free-trial Start time for a company.

    Idempotent: starting an already-started trial returns the current row. Raises
    TrialNotAssignedError when the admin never assigned a window, and
    TrialExpiredError when the assigned window already ended. Returns None only
    when the company does not exist.
    """
    row = await get_company(company_id)
    if row is None:
        return None

    if row.get("trial_from") is None or row.get("trial_to") is None:
        raise TrialNotAssignedError(company_id)

    if row.get("trial_started_at") is not None:
        return company_row_to_dict(row)

    today = datetime.now(timezone.utc).date()
    if today > row["trial_to"]:
        raise TrialExpiredError(company_id)

    updated = await db_service.fetchrow(
        f"""
        UPDATE companies
        SET trial_started_at = NOW(), updated_at = NOW()
        WHERE id = $1
        RETURNING {_COLUMNS}
        """,
        company_id,
    )
    logger.info("Started free trial for company id=%s", company_id)
    return company_row_to_dict(updated)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def delete_company(company_id: int) -> Optional[str]:
    """Delete a company and cascade to its employee records.

    Deleting the company removes its employee (access request) records too, so
    those accounts immediately lose application access; the underlying signed-in
    user accounts are NOT deleted (FR-023). Both statements run in one
    transaction so a failure cannot leave the company gone but employees
    orphaned. Returns the logo filename for the caller to clean up, or None when
    the company did not exist.
    """
    async with db_service.transaction() as conn:
        row = await conn.fetchrow(
            "DELETE FROM companies WHERE id = $1 RETURNING logo_filename",
            company_id,
        )
        if row is None:
            # Nothing deleted — no cascade, and the transaction commits empty.
            return None
        await conn.execute(
            "DELETE FROM employees WHERE company_id = $1",
            company_id,
        )
    logger.info("Deleted company id=%s and its employee records", company_id)
    return row["logo_filename"]


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def reveal_password(company_id: int) -> Optional[str]:
    """Decrypt a company's stored password on demand.

    Returns None when the company does not exist. Raises DecryptionError when
    the stored token cannot be read with the current key.
    """
    row = await db_service.fetchrow(
        "SELECT password_encrypted FROM companies WHERE id = $1",
        company_id,
    )
    if row is None:
        return None
    return decrypt_password(row["password_encrypted"])

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
