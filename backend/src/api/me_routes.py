# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Signed-in account ("me") routes — membership resolution and leave/cancel.

These ride the ordinary NextAuth branch of auth_middleware; the account identity
comes from request.state.user_id (populated by the middleware) and never from
the request. /api/me/membership is on the membership allow-list, so an account
with no grant can still read its (empty) membership and cancel a pending
request. No endpoint here checks auth itself.
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from src.models.employee_models import DeleteResponse, MembershipResponse
from src.services import membership_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/me", tags=["membership"])


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/membership", response_model=MembershipResponse)
async def get_my_membership(request: Request):
    """The signed-in account's accepted membership, or null when it has none."""
    membership = await membership_service.get_accepted_membership(request.state.user_id)
    return MembershipResponse(membership=membership)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.delete("/membership", response_model=DeleteResponse)
async def leave_or_cancel_membership(request: Request):
    """Cancel a pending request, or leave a granted company (hard delete).

    One operation for both cases (FR-015/FR-017): the account's employee record
    is deleted, access is revoked, and the user account is untouched.
    """
    deleted = await membership_service.delete_membership(request.state.user_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "no_membership",
                "message": "You have no membership to leave.",
                "details": None,
            },
        )
    return DeleteResponse(success=True, message="Membership removed.")

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
