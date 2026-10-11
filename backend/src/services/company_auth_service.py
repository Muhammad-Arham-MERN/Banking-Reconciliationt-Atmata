# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company authentication for the Company Dashboard.

A company signs in with its name and access password. The password was stored
Fernet-encrypted by the Admin Dashboard (008), so verification decrypts it and
compares constant-time. A successful sign-in mints a company JWT (HS256) signed
with COMPANY_JWT_SECRET — the company is its own principal, separate from the
admin and from the Google (NextAuth) users.

Nothing here ever logs or returns a password.
"""
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from src.config import settings
from src.services import company_service
from src.services.company_crypto_service import DecryptionError, decrypt_password

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
COMPANY_SUBJECT_PREFIX = "company:"


class CompanyAuthNotConfiguredError(Exception):
    """Raised when the company signing secret is absent.

    Surfaces as 503: company sign-in must refuse to issue a session rather than
    authenticate against nothing.
    """


def _compare_digest(left: str, right: str) -> bool:
    """Constant-time string comparison (UTF-8 safe)."""
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def verify_company_credentials(name: str, password: str) -> Optional[dict]:
    """Return the company row when the name + password match, else None.

    The company name is matched case-insensitively after trimming (FR-027). The
    stored Fernet token is decrypted and compared in constant time. An unknown
    company and a wrong password are indistinguishable to the caller — both
    return None so the route can send one generic denial (FR-017).
    """
    row = await company_service.get_company_by_name((name or "").strip())
    if row is None:
        return None

    try:
        stored_password = decrypt_password(row["password_encrypted"])
    except DecryptionError as exc:
        # A rotated or corrupt key is an operator problem, not a wrong password.
        logger.error("Could not decrypt company password for id=%s: %s", row["id"], exc)
        return None

    if not _compare_digest(password or "", stored_password):
        return None

    return row


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def issue_company_token(company_id: int, company_name: str) -> tuple[str, str]:
    """Mint a company JWT. Returns (token, expires_at ISO-8601).

    Raises CompanyAuthNotConfiguredError when COMPANY_JWT_SECRET is missing — the
    caller must fail closed rather than issue an unsigned session.
    """
    secret = (settings.COMPANY_JWT_SECRET or "").strip()
    if not secret:
        raise CompanyAuthNotConfiguredError("COMPANY_JWT_SECRET is not configured.")

    ttl_hours = settings.COMPANY_JWT_TTL_HOURS or 24
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ttl_hours)

    payload = {
        "sub": f"{COMPANY_SUBJECT_PREFIX}{company_id}",
        "company_id": company_id,
        "company_name": company_name,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token, expires_at.isoformat()


def verify_company_token(token: str) -> Optional[dict]:
    """Return the payload for a valid, unexpired company JWT, else None.

    Used by the company branch of auth_middleware to gate any future
    /api/company/* path.
    """
    secret = (settings.COMPANY_JWT_SECRET or "").strip()
    if not secret or not token:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Company token has expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid company token: %s", exc)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unexpected company token verification error: %s", exc)
        return None

    if not str(payload.get("sub", "")).startswith(COMPANY_SUBJECT_PREFIX):
        return None
    return payload

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
