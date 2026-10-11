# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Pydantic request/response models for the Company onboarding-request inbox
(FR-006).

Mirrors contracts/membership-api.yaml + contracts/admin-api.yaml. A company
request is a standalone, view-only record: it has no status lifecycle and no
link to company account creation — the Developer onboards companies manually
after contacting them. All DB access happens through raw asyncpg (db_service).

Field constraints are deliberately left to the route: a pydantic failure would
return FastAPI's own 422 envelope, whereas the contract uses the project's
{"error","message","details"} 400 for a missing company name.
"""
from pydantic import BaseModel

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ


class CompanyRequestCreate(BaseModel):
    """POST /api/company-requests request body.

    Only `company_name` is required; the remaining fields are stored as '' when
    blank (the cinematic flow already applies basic format checks in-browser).
    """
    company_name: str
    role: str = ""
    website_socials: str = ""
    email: str = ""
    phone: str = ""


class CompanyRequest(BaseModel):
    """A stored onboarding request as listed in the Admin Dashboard."""
    # Stringified — CockroachDB SERIAL ids exceed JavaScript's safe integer range.
    id: str
    company_name: str
    role: str = ""
    website_socials: str = ""
    email: str = ""
    phone: str = ""
    submitted_at: str


class CompanyRequestListResponse(BaseModel):
    """GET /api/admin/company-requests response."""
    requests: list[CompanyRequest]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
