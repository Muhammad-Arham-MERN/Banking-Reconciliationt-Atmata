# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Processing cancellation registry.

Allows the frontend to stop an in-flight /reconcile-ai request (page reload,
"Stop" button) so we don't keep paying for LLM calls after the user is gone.

Each in-flight request registers its request_id with a cancel handle. The
cancel endpoint flips a flag (and, for the streaming agent run, calls
result.cancel() to halt the current LLM turn immediately). The route checks
the flag between stages and aborts with a 499-style response.
"""

import logging
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

# request_id -> {"cancelled": bool, "cancel": Optional[Callable[[], None]]}
_ACTIVE_RUNS: Dict[str, Dict] = {}


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def register_run(request_id: str, cancel_fn: Optional[Callable[[], None]] = None) -> None:
    """Register an in-flight run so it can be cancelled."""
    _ACTIVE_RUNS[request_id] = {"cancelled": False, "cancel": cancel_fn}
    logger.debug("Registered in-flight run %s", request_id)


def unregister_run(request_id: str) -> None:
    """Remove a run from the registry (finished/cancelled/cleanup)."""
    _ACTIVE_RUNS.pop(request_id, None)
    logger.debug("Unregistered run %s", request_id)


def update_cancel_handle(request_id: str, cancel_fn: Callable[[], None]) -> None:
    """Attach (or replace) the streaming run's cancel handle once available."""
    entry = _ACTIVE_RUNS.get(request_id)
    if entry is not None:
        entry["cancel"] = cancel_fn


def is_cancelled(request_id: str) -> bool:
    """Whether the client requested cancellation for this run."""
    entry = _ACTIVE_RUNS.get(request_id)
    return bool(entry and entry.get("cancelled"))


def cancel_run(request_id: str) -> bool:
    """Request cancellation of a run. Returns True if the run was found."""
    entry = _ACTIVE_RUNS.get(request_id)
    if entry is None:
        return False
    entry["cancelled"] = True
    cancel_fn = entry.get("cancel")
    if cancel_fn is not None:
        try:
            cancel_fn()
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Cancel handle failed for %s: %s", request_id, e)
    logger.info("Cancellation requested for run %s", request_id)
    return True


def cancel_all_runs() -> None:
    """Cancel every in-flight run (e.g. server shutdown)."""
    for request_id in list(_ACTIVE_RUNS.keys()):
        cancel_run(request_id)


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
