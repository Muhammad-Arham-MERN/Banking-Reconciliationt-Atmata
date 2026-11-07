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

DEFAULT_RECIPIENT = "arhambrowser@gmail.com"


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


def _format_limitation_body(report: dict) -> str:
    """Compose the plain-text body from the report's validated fields only.

    No secrets and no raw financial rows are ever echoed — only what the agent
    passed (FR-015, FR-016).
    """
    return (
        "Reconciliation Atmata — tool limitation report\n\n"
        f"Tool:  {report.get('tool_name', '')}\n"
        f"Run:   {report.get('run_id', '')}\n"
        f"Stage: {report.get('stage', '')}\n\n"
        "ISSUE\n"
        f"{report.get('issue', '')}\n\n"
        "DETAILS\n"
        f"{report.get('details', '')}\n\n"
        "EXAMPLE (anonymised)\n"
        f"{report.get('example', '')}\n\n"
        "ANALOGY\n"
        f"{report.get('analogy', '')}\n\n"
        "PROPOSED SOLUTION\n"
        f"{report.get('proposed_solution', '')}\n\n"
        "WHY (reason)\n"
        f"{report.get('reason', '')}\n"
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def send_agent_limitation_email(report: dict) -> bool:
    """Email the Developer a tool/engine limitation report from the agent.

    Best-effort: never raises into the agent run (FR-005). The subject begins
    with settings.AGENT_LIMITATION_SUBJECT_PREFIX so the Developer's Gmail rule
    files it under the "Reconciliation Atmata" label (FR-002). The body is
    composed only from the report's validated fields — no secrets, no raw
    financial rows (FR-015, FR-016).

    Returns True when an email was handed to the provider, False when the send
    was skipped (no key/sender) or failed.
    """
    api_key = settings.RESEND_API_KEY
    sender = settings.RESEND_FROM_EMAIL
    if not api_key:
        logger.warning("RESEND_API_KEY is not set; skipping agent limitation email.")
        return False
    if not sender:
        logger.warning("RESEND_FROM_EMAIL is not set; skipping agent limitation email.")
        return False

    # Imported lazily so a missing optional dependency never breaks startup.
    try:
        import resend
    except ImportError:
        logger.warning("The 'resend' package is not installed; skipping limitation email.")
        return False

    recipient = settings.AGENT_LIMITATION_NOTIFY_EMAIL or DEFAULT_RECIPIENT
    tool_name = (report.get("tool_name") or "engine").strip()
    email = {
        "from": sender,
        "to": [recipient],
        "subject": f"{settings.AGENT_LIMITATION_SUBJECT_PREFIX}: {tool_name} limitation",
        "text": _format_limitation_body(report),
    }

    try:
        resend.api_key = api_key
        # The SDK's send is synchronous; run it off the event loop.
        await asyncio.to_thread(resend.Emails.send, email)
    except Exception as exc:  # noqa: BLE001 — fail-soft by design (FR-005)
        logger.error("Failed to send agent limitation email: %s", exc)
        return False

    logger.info("Sent agent limitation email to %s", recipient)
    return True

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
