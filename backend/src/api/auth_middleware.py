# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Auth verification middleware
Verifies Auth.js JWT tokens from frontend requests
"""
import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from src.services.auth_service import verify_auth_token

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
AUTH_EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}
AUTH_EXEMPT_PREFIXES = {
    "/health", "/docs", "/redoc", "/openapi.json",
    # NOTE: /karwai is deliberately NOT exempt (feature 008) — it is the most
    # crucial API endpoint and must be Bearer-authenticated like the rest.
    "/reconcile-ai", "/history",
}


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

    # Inject user context into request state and headers
    request.state.user_id = user_id_int
    request.state.user_email = user_info["email"]

    response = await call_next(request)
    response.headers["X-User-Id"] = user_info["user_id"]
    response.headers["X-User-Email"] = user_info["email"]

    return response
# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
