# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Pydantic request/response models for the Company Dashboard sign-in API.

Mirrors contracts/company-auth-api.yaml. These are the API layer only — the
credential check itself lives in company_auth_service.
"""
from pydantic import BaseModel, Field

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ


class CompanyLoginRequest(BaseModel):
    """POST /api/company/login request body.

    Credentials travel in the JSON body, never the query string, so they never
    appear in URLs or logs.
    """
    company_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class CompanyIdentity(BaseModel):
    """The small slice of a company the dashboard may display.

    Carries NO password material — not the plaintext and not the ciphertext.
    """
    # Stringified — CockroachDB SERIAL ids exceed JavaScript's safe integer range.
    id: str
    name: str
    logo_url: str | None = None


class CompanyLoginResponse(BaseModel):
    """POST /api/company/login success response."""
    token: str
    # Sign-in time + COMPANY_JWT_TTL_HOURS (24 by default).
    expires_at: str
    company: CompanyIdentity


class CompanyTrialState(BaseModel):
    """The signed-in company's free-trial state (GET/POST /api/company/trial).

    `status` is one of: not_assigned, not_started, scheduled, active, expired.
    Dates are ISO strings (YYYY-MM-DD); `trial_started_at` is a full timestamp or
    null until the company clicks Start.
    """
    status: str
    trial_from: str | None = None
    trial_to: str | None = None
    trial_started_at: str | None = None

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
