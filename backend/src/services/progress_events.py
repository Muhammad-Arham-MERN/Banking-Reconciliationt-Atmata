# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Progress event bus for live SSE updates during /reconcile-ai.

The sidecar SSE route (POST /reconcile-ai/{request_id}/events) reads from an
asyncio.Queue per request_id while the main reconcile_ai() coroutine (and the
SDK agent tools it spawns in worker threads) push stage events into it.

Thread-safety: the OpenAI Agents SDK runs sync tools in worker threads with no
running event loop, so emit() must never await. asyncio.Queue.put_nowait() is
itself thread-safe, so the tools can push straight onto the queue without
crossing loops. The SSE generator (running on the main loop) awaits queue.get().

Lifecycle is owned by the ROUTE (ai_routes.reconcile_ai), not by
detect_structure: start_progress() right after register_run(), and
stop_progress() in the same finally that unregisters the run. This guarantees
the queue lives for the whole request (upload -> detection -> extraction ->
reconcile -> done), which is also what makes cancellation work across the full
pipeline (see ai_routes is_cancelled checks at every boundary).
"""
import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# request_id -> asyncio.Queue[dict]
_bus: Dict[str, asyncio.Queue] = {}

# Sentinel pushed after the last real event so the SSE generator can exit even
# if no terminal status frame was emitted (e.g. a hard exception path).
_CLOSED = "__closed__"


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def start_progress(request_id: str) -> asyncio.Queue:
    """Create (or reset) the event queue for a request. Returns the queue."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    _bus[request_id] = queue
    logger.debug("Progress queue started for %s", request_id)
    return queue


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def emit(request_id: str, event: dict) -> None:
    """Push a stage/status event onto the request's queue.

    Safe to call from ANY thread (main loop coroutines AND SDK tool worker
    threads): put_nowait is thread-safe and never blocks.
    """
    if not request_id:
        return
    queue = _bus.get(request_id)
    if queue is None:
        # The run finished/unregistered before this event landed - drop it.
        logger.debug("No progress queue for %s; dropping %s", request_id, event.get("key"))
        return
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        # Never block the pipeline on a slow SSE consumer; drop the event.
        logger.warning("Progress queue full for %s; dropping %s", request_id, event.get("key"))


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def emit_stage(
    request_id: str,
    key: str,
    message: str,
    sentiment: str = "neutral",
    emoji: str = "",
    progress_delta: float = 0.0,
) -> None:
    """Convenience wrapper building a stage frame."""
    emit(
        request_id,
        {
            "type": "stage",
            "key": key,
            "message": message,
            "sentiment": sentiment,
            "emoji": emoji,
            "progress_delta": progress_delta,
        },
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def emit_status(request_id: str, state: str, message: str = "") -> None:
    """Push a terminal status frame (done / error / cancelled)."""
    emit(
        request_id,
        {
            "type": "status",
            "state": state,
            "message": message,
        },
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def stop_progress(request_id: str) -> None:
    """Drop the request's queue and signal any waiting SSE generator to exit.

    Idempotent - safe to call more than once per request.
    """
    queue = _bus.pop(request_id, None)
    if queue is None:
        return
    try:
        queue.put_nowait(_CLOSED)
    except asyncio.QueueFull:
        pass
    logger.debug("Progress queue stopped for %s", request_id)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def get_queue(request_id: str) -> Optional[asyncio.Queue]:
    """Return the live queue for a request_id (None if not active)."""
    return _bus.get(request_id)


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
