# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Notification service — Resend email for company onboarding requests.

The company request is the source of truth; the email is a convenience. Every
send is therefore best-effort: it never raises into the caller, so a mail
outage cannot fail or roll back the stored request (FR-007). When the Resend
key is unset the send is skipped with a warning (dev-friendly).
"""
import asyncio
import logging

from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_RECIPIENT = "ArhamBrowser@gmail.com"


def _format_body(request: dict) -> str:
    return (
        "New company request\n\n"
        f"Company: {request.get('company_name', '')}\n"
        f"Role: {request.get('role', '')}\n"
        f"Website / Socials: {request.get('website_socials', '')}\n"
        f"Email: {request.get('email', '')}\n"
        f"Phone: {request.get('phone', '')}\n"
        f"Submitted: {request.get('submitted_at', '')}\n"
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def send_company_request_notification(request: dict) -> bool:
    """Email the Developer about a new company request. Never raises.

    Returns True when an email was handed to the provider, False when the send
    was skipped (no key/sender) or failed. The failure is logged, never
    propagated — the caller's 201 is unaffected (FR-007).
    """
    api_key = settings.RESEND_API_KEY
    sender = settings.RESEND_FROM_EMAIL
    if not api_key:
        logger.warning("RESEND_API_KEY is not set; skipping company-request notification.")
        return False
    if not sender:
        logger.warning("RESEND_FROM_EMAIL is not set; skipping company-request notification.")
        return False

    # Imported lazily so a missing optional dependency never breaks startup.
    try:
        import resend
    except ImportError:
        logger.warning("The 'resend' package is not installed; skipping notification.")
        return False

    recipient = settings.COMPANY_REQUEST_NOTIFY_EMAIL or DEFAULT_RECIPIENT
    email = {
        "from": sender,
        "to": [recipient],
        "subject": f"New company request: {request.get('company_name', '')}",
        "text": _format_body(request),
    }

    try:
        resend.api_key = api_key
        # The SDK's send is synchronous; run it off the event loop.
        await asyncio.to_thread(resend.Emails.send, email)
    except Exception as exc:  # noqa: BLE001 — fail-soft by design (FR-007)
        logger.error("Failed to send company-request notification: %s", exc)
        return False

    logger.info("Sent company-request notification to %s", recipient)
    return True

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
