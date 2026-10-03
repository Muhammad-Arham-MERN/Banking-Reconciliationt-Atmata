# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Auth verification middleware
Verifies Auth.js JWT tokens from frontend requests, plus the separate admin
session token used by the hidden Admin Dashboard (Camri Desk).
"""
import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from src.services.auth_service import verify_auth_token
from src.services.admin_auth_service import (
    verify_admin_token,
    extract_bearer_token,
)
from src.services.company_auth_service import verify_company_token
from src.services.membership_service import get_accepted_membership

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# Only genuinely-public endpoints skip auth. Everything else — /karwai,
# /reconcile-ai, /history, /cloud, /advisor — requires a Bearer JWT.
AUTH_EXEMPT_PREFIXES = {"/health", "/docs", "/redoc", "/openapi.json"}

# Admin Dashboard (Camri Desk). The login endpoint is the ONE admin path that
# is public; every other /api/admin path is gated right here so a forgotten
# per-route check can never leave company data exposed.
ADMIN_PREFIX = "/api/admin"
ADMIN_LOGIN_PATH = "/api/admin/login"

# Company Dashboard. A company is its own principal — it holds no Google
# (NextAuth) session — so it gets its own branch exactly like the admin: the
# login path is public, every other /api/company path requires the company JWT.
# NOTE: the check matches /api/company and /api/company/… only, NOT a sibling
# like /api/company-requests (which rides the NextAuth branch instead).
COMPANY_PREFIX = "/api/company"
COMPANY_LOGIN_PATH = "/api/company/login"


def _is_company_path(path: str) -> bool:
    """True only for the company branch's own paths.

    A plain startswith("/api/company") would also swallow /api/company-requests —
    a NextAuth-branch path — so require an exact match or a separator.
    """
    return path == COMPANY_PREFIX or path.startswith(COMPANY_PREFIX + "/")

# NextAuth-branch paths a signed-in account may reach WITHOUT an accepted
# company membership (FR-009). Every OTHER path on this branch requires one.
# The list is deliberately exact: it must include the endpoints the
# subscription/request layer itself depends on (the company dropdown and logos,
# the access request, the company onboarding request, and the membership
# lookup/cancel), or the gate would lock out the very flow that creates a
# membership (research D2 — the top task risk).
MEMBERSHIP_ALLOW_PREFIXES = (
    "/api/company-requests",
    "/api/companies",
    "/api/me/membership",
    "/api/employees/requests",
)


async def _handle_admin_request(request: Request, call_next):
    """Verify the admin session token on protected /api/admin paths.

    The admin session is independent of NextAuth: it is a short-lived JWT
    signed with ADMIN_JWT_SECRET, issued by POST /api/admin/login.
    """
    path = request.url.path
    token = extract_bearer_token(request.headers.get("Authorization", ""))

    if not token or not verify_admin_token(token):
        logger.warning("Rejected admin request to %s %s", request.method, path)
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "Admin authentication required. Please sign in.",
                "status_code": 401,
            },
        )

    request.state.admin_authenticated = True
    return await call_next(request)


async def _handle_company_request(request: Request, call_next):
    """Verify the company session token on protected /api/company paths.

    Independent of both NextAuth and the admin session: it is the company JWT
    issued by POST /api/company/login (24h, signed with COMPANY_JWT_SECRET).
    """
    path = request.url.path
    token = extract_bearer_token(request.headers.get("Authorization", ""))
    payload = verify_company_token(token)

    if not payload:
        logger.warning("Rejected company request to %s %s", request.method, path)
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "Company authentication required. Please sign in.",
                "status_code": 401,
            },
        )

    request.state.company_id = payload.get("company_id")
    request.state.company_name = payload.get("company_name")
    return await call_next(request)


async def auth_middleware(request: Request, call_next):
    """
    Middleware that verifies Auth.js JWT on protected routes.
    Adds X-User-Id and X-User-Email headers on successful verification.
    Returns 401 on missing/invalid tokens.
    """
    path = request.url.path

    # Skip auth for public endpoints
    if any(path.startswith(prefix) or path == prefix for prefix in AUTH_EXEMPT_PREFIXES):
        return await call_next(request)

    # Skip auth for CORS preflight requests (no auth header on OPTIONS)
    if request.method == "OPTIONS":
        return await call_next(request)

    # Admin dashboard: its own credential flow and its own token.
    if path == ADMIN_LOGIN_PATH:
        return await call_next(request)

    if path.startswith(ADMIN_PREFIX):
        return await _handle_admin_request(request, call_next)

    # Company dashboard: its own credential flow and its own token.
    if path == COMPANY_LOGIN_PATH:
        return await call_next(request)

    if _is_company_path(path):
        return await _handle_company_request(request, call_next)

    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        logger.warning("Missing Authorization header on %s %s", request.method, path)
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "Authentication required. Please sign in.",
                "status_code": 401,
            },
        )

    token = auth_header.removeprefix("Bearer ").strip()
    user_info = verify_auth_token(token)

    if user_info is None:
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "Invalid or expired token. Please sign in again.",
                "status_code": 401,
            },
        )

    # token.sub is the database users.id (from Auth.js JWT session)
    from src.services.db_service import db_service
    user_row = await db_service.fetchrow(
        "SELECT id FROM users WHERE id::text = $1",
        user_info["user_id"],
    )
    if not user_row:
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "User not found in database. Please sign in again.",
                "status_code": 401,
            },
        )

    user_id_int = user_row["id"]

    # FR-009: without a granted membership the account may reach only the
    # subscription/sign-in layer. The check lives here, server-side, so a
    # frontend redirect cannot be bypassed by calling the API directly. The
    # allow-list keeps the request/dropdown/membership endpoints reachable.
    if not any(path.startswith(prefix) for prefix in MEMBERSHIP_ALLOW_PREFIXES):
        membership = await get_accepted_membership(user_id_int)
        if membership is None:
            logger.warning("Membership required for %s %s", request.method, path)
            return JSONResponse(
                status_code=403,
                content={
                    "error": "membership_required",
                    "message": "A company-granted access is required to use the application.",
                    "status_code": 403,
                },
            )

    # Inject user context into request state and headers
    request.state.user_id = user_id_int
    request.state.user_email = user_info["email"]

    response = await call_next(request)
    response.headers["X-User-Id"] = user_info["user_id"]
    response.headers["X-User-Email"] = user_info["email"]

    return response
# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
