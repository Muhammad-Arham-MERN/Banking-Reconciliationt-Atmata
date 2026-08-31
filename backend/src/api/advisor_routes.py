# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Advisor Routes (Subh al Baqaya — AI Reconciler Advisor, feature 007).

New, dedicated, auth-protected endpoints for the Reconciler Agent (FR-001).
These are NOT exempt from authentication (unlike /karwai and /reconcile-ai):
the frontend sends the Bearer JWT via the existing auth middleware.

- POST /advisor/reconcile — run the agent over the complete final
  discrepancies list + cumulative Bank/Company balance context + history.
  Streams the response token-by-token (FR-008c); any agent failure is retried
  up to 3 attempts, then a friendly error surfaces (FR-006). Cancellation
  mid-stream returns the existing 499 behavior.
- POST /advisor/{request_id}/cancel — cancel a running advisor turn.
"""
import asyncio
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from src.models.advisor_models import (
    AdvisorReconcileRequest,
    AdvisorResponse,
)
from src.services.advisor_service import (
    AdvisorError,
    FRIENDLY_ADVISOR_ERROR,
    run_advisor,
)
from src.services.processing_cancellation import (
    cancel_run,
    is_cancelled,
    register_run,
    unregister_run,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/advisor/reconcile")
async def advisor_reconcile(request: AdvisorReconcileRequest):
    """
    Run the Reconciler Agent over the given reconciliation context.

    Stateless (FR-008a): every call re-sends the CURRENT live discrepancy
    context (reflecting any reconciles applied so far) plus the conversation
    history, keyed by the reconciliation request_id. The agent receives ONLY
    the final discrepancies list + balance context — never the raw file data.

    The response streams token-by-token (SSE-style). The final frame carries
    the typed AdvisorResponse (suggestions + chat_message) the frontend
    consumes directly. On cancellation, returns the existing 499 JSON; after
    3 failed attempts, returns 503 with a friendly error (no partial state).
    """
    request_id = (request.request_id or "").strip() or str(uuid.uuid4())
    register_run(request_id)

    if is_cancelled(request_id):
        unregister_run(request_id)
        raise HTTPException(
            status_code=499,
            detail={
                "error": "cancelled",
                "message": "Processing cancelled by user",
                "details": {"request_id": request_id},
            },
        )

    async def event_stream():
        try:
            async def stream_callback(delta: str) -> None:
                # Stream raw text deltas as SSE-style token frames.
                yield f"data: {json.dumps({'type': 'token', 'delta': delta})}\n\n"

            advisor_response: Optional[AdvisorResponse] = await run_advisor(
                request,
                request_id,
                stream_callback=stream_callback,
            )

            # Final frame: the typed structured output (FR-002a).
            yield (
                "data: "
                + json.dumps(
                    {"type": "result", "data": advisor_response.model_dump()}
                )
                + "\n\n"
            )
        except asyncio.CancelledError:
            logger.info("Run %s cancelled by user", request_id)
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "status": 499,
                        "error": "cancelled",
                        "message": "Processing cancelled by user",
                    }
                )
                + "\n\n"
            )
        except AdvisorError as e:
            logger.error("Advisor failed after retries for %s: %s", request_id, e)
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "status": 503,
                        "error": "agent_unavailable",
                        "message": e.message or FRIENDLY_ADVISOR_ERROR,
                    }
                )
                + "\n\n"
            )
        except Exception as e:
            logger.error("Unexpected error in /advisor/reconcile: %s", e)
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "status": 422,
                        "error": "processing_error",
                        "message": FRIENDLY_ADVISOR_ERROR,
                    }
                )
                + "\n\n"
            )
        finally:
            unregister_run(request_id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/advisor/{request_id}/cancel")
async def advisor_cancel(request_id: str):
    """Cancel an in-flight Reconciler Agent turn (Stop button / page reload).

    Flips the cancellation flag and halts the streaming LLM run immediately.
    Returns 200 even if the run already finished (idempotent), mirroring the
    existing /reconcile-ai/{request_id}/cancel behavior.
    """
    found = cancel_run(request_id)
    return {
        "request_id": request_id,
        "cancelled": found,
        "message": "Processing cancelled" if found else "No active run found",
    }


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
