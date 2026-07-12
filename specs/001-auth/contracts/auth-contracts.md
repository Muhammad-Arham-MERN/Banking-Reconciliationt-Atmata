# API Contracts: Auth.js Integration

This document defines the contracts between frontend (Next.js) and backend (FastAPI) for authentication.

## Auth.js Auto-Provided Routes

All handled by `next-auth@5` at `/api/auth/*`:

| Route | Purpose |
|-------|---------|
| `GET /api/auth/signin` | Sign-in page (or redirect to Google) |
| `POST /api/auth/signin/google` | Initiate Google OAuth |
| `GET /api/auth/callback/google` | OAuth callback handler |
| `POST /api/auth/signout` | Sign out |
| `GET /api/auth/session` | Get current session (JSON) |
| `GET /api/auth/csrf` | CSRF token |

## Backend Session Verification Contract

**Purpose**: FastAPI middleware verifies the Auth.js JWT from frontend requests to identify the authenticated user.

### Request Header

```
Authorization: Bearer <next-auth.session-token JWT>
```

### How it works

1. Frontend reads the JWT session token from the `next-auth.session-token` cookie or calls `getToken()` from `next-auth/jwt`
2. Frontend sends the token in the `Authorization` header with requests to the backend
3. Backend middleware decodes and verifies the JWT using `NEXTAUTH_SECRET` (shared env var) and `PyJWT`
4. On success: request context is enriched with `user_id` and `email`
5. On failure: request returns 401 Unauthorized

### Backend Dependencies

- `PyJWT` — decode and verify Auth.js JWT
- Shared `NEXTAUTH_SECRET` environment variable between frontend and backend

### Backend JWT Verification

```python
import jwt
import requests

# Fetch JWKS or use symmetric secret
secret = os.environ["NEXTAUTH_SECRET"]

def verify_auth_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["sub", "email"]}
        )
        return {"user_id": payload["sub"], "email": payload.get("email")}
    except jwt.PyJWTError:
        return None
```

### Error Response

```json
{
  "error": "unauthorized",
  "message": "Authentication required. Please sign in.",
  "status_code": 401
}
```

## Existing Route User Context

Existing API routes that need user context will receive `X-User-Id` and `X-User-Email` headers added by the auth middleware. The routes themselves remain unchanged — only the middleware layer is added.
