# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Admin authentication for the hidden dashboard (Camri Desk).

The Developer's username and password live ONLY in the environment. A
successful sign-in mints a short-lived admin JWT (HS256) signed with
ADMIN_JWT_SECRET — deliberately separate from NEXTAUTH_SECRET so the admin
session is independent of normal application users.

The frontend keeps that token in sessionStorage, so the session ends when the
browser closes; the token's own `exp` is only a backstop.
"""
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from src.config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ADMIN_SUBJECT = "admin"
ADMIN_ROLE_CLAIM = "admin"


class AdminAuthNotConfiguredError(Exception):
    """Raised when the admin credentials or signing secret are absent.

    Surfaces as 503: the dashboard must refuse to authenticate rather than
    compare against empty values.
    """


def _compare_digest(left: str, right: str) -> bool:
    """Constant-time string comparison (UTF-8 safe).

    hmac.compare_digest rejects non-ASCII `str` inputs, so both sides are
    encoded first.
    """
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def verify_admin_credentials(username: str, password: str) -> bool:
    """Check the submitted admin credentials against the environment values.

    Both fields are always compared (no short-circuit) so a wrong username and
    a wrong password take the same path. The caller returns one generic message
    either way, so the response never discloses which field was wrong.
    """
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise AdminAuthNotConfiguredError(
            "Admin credentials are not configured on the server."
        )

    username_ok = _compare_digest(username or "", settings.ADMIN_USERNAME)
    password_ok = _compare_digest(password or "", settings.ADMIN_PASSWORD)
    return username_ok and password_ok


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def issue_admin_token() -> tuple[str, str]:
    """Mint an admin JWT. Returns (token, expires_at ISO-8601)."""
    secret = (settings.ADMIN_JWT_SECRET or "").strip()
    if not secret:
        raise AdminAuthNotConfiguredError("ADMIN_JWT_SECRET is not configured.")

    ttl_hours = settings.ADMIN_JWT_TTL_HOURS or 12
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ttl_hours)

    payload = {
        "sub": ADMIN_SUBJECT,
        ADMIN_ROLE_CLAIM: True,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token, expires_at.isoformat()


def verify_admin_token(token: str) -> bool:
    """Verify an admin JWT. Returns False for anything invalid or expired."""
    secret = (settings.ADMIN_JWT_SECRET or "").strip()
    if not secret or not token:
        return False
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Admin token has expired")
        return False
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid admin token: %s", exc)
        return False
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unexpected admin token verification error: %s", exc)
        return False

    return payload.get("sub") == ADMIN_SUBJECT and payload.get(ADMIN_ROLE_CLAIM) is True


def extract_bearer_token(auth_header: Optional[str]) -> str:
    """Pull the token out of an `Authorization: Bearer <token>` header."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return ""
    return auth_header.removeprefix("Bearer ").strip()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
