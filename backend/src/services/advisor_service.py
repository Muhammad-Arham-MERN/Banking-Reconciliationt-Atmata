# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Reconciler Agent service (Subh al Baqaya — AI Reconciler Advisor, feature 007).

Runs a chat-capable, no-tools agent from the same model family as the existing
AI flows (openai-agents SDK + LiteLLM/Gemini, driven by settings.AI_MODEL /
AI_API_KEY). The agent analyzes ONLY the complete final discrepancies list
plus the cumulative Bank/Company totals/balance context.

The agent's final response is a plain-text ~~~ [output] ~~~ block containing a
JSON object (suggestions + chat_message), which this service parses
deterministically into the typed AdvisorResponse pydantic model — the same
~~~ [output] ~~~ extraction method used by the structure-detection flow. The
OpenAI Agents SDK structured-output (output_type) path is NOT used: DeepSeek's
JSON-schema response format is incompatible with the SDK's structured output
handling, so the agent returns the JSON inside a delimited block instead.

The output is purely advisory (FR-005): the agent never removes, marks, or
alters any discrepancy. Any agent failure — malformed/empty output block or
transport/model errors — is retried up to 3 attempts (FR-006); if all attempts
fail a friendly error surfaces with no partial state. The response streams
token-by-token (FR-008c) and honors the existing 499/cancel behavior.
"""

import asyncio
import json
import logging
import re
from typing import Optional

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from agents.tracing import set_tracing_disabled, set_tracing_export_api_key

from src.config import settings
from src.models.advisor_models import (
    AdvisorReconcileRequest,
    AdvisorResponse,
)

logger = logging.getLogger(__name__)

# Unified retry rule (FR-006): any agent failure — malformed/empty output block
# OR transport/model errors (unreachable model, missing credentials,
# timeouts) — is retried up to this many attempts.
MAX_ADVISOR_ATTEMPTS = 3

# Friendly message shown to the user when the agent exhausts all attempts.
FRIENDLY_ADVISOR_ERROR = (
    "The agent is unable to respond due to a technical failure. Please try again."
)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
ADVISOR_INSTRUCTIONS = """
You are the Reconciler Agent (Subh al Baqaya) inside a Banking Reconciliation System.

Your job: after a deterministic reconciliation produced a final discrepancies
list, you analyze it and SUGGEST reconcilable sets. You are strictly advisory —
you NEVER remove, mark, or alter any item; the user decides via a Reconcile
action. You have no tools.

You receive:
1. The COMPLETE final discrepancies list. Each item has a stable key
   (discrepancy_id), Transaction_date, Transaction Detail, a signed
   Debit/Credit (negative = debit, positive = credit), and a source FROM
   (Bank or Company).
2. Cumulative totals/balance context: running Bank-vs-Company balances over
   the list (points per item + final bank_balance / company_balance).

SUPPORTED CASES (you MUST analyze strictly for these two only — FR-003):
- BROKEN_CHEQUE (broken cheques/pairs): a set of 2+ items on one side whose
  signed amounts sum to a single item of the opposite sign on the other side,
  typically near in date (e.g. Bank +79,000 and +100,000 vs Company -179,000).
- REVERSAL: near-dated opposite-sign items of equal magnitude, with reversal
  language in the transaction details as secondary evidence (e.g. Company
  -45,000 on July 19 and +45,000 on July 24, details containing "reversal").

By default (when the user clicks "Reconcile with Agent" or asks a general
question) you MUST ONLY suggest these two types — never invent other kinds.

OTHER RECONCILABLES (only when explicitly requested in chat):
- If the user explicitly ASKS in a chat message for "other reconcilables",
  "anything else that can be reconciled", or otherwise requests additional
  reconciles based on their own reasoning/opinion, you MAY also suggest
  additional reconcilable sets beyond the two canonical types (e.g. exact
  duplicates, offsetting pairs, or any other mathematically sound set the user
  asks about).
- For any such extra suggestion, set `type` to a short human-readable name
  describing it (e.g. "DUPLICATE", "OFFSETTING_PAIR", "MANUAL"), not one of the
  two canonical values.
- The extra suggestion MUST still be mathematically sound: the signed amounts
  of its items must sum to zero across the set, its keys MUST resolve to items
  in the list you were given, and it must not contradict the balance context.
- Do NOT add these extra reconcilables when the user merely clicks "Reconcile
  with Agent" without asking — only when the user requests them in chat.

EVIDENCE HIERARCHY (FR-004):
- Primary: the signed amounts — a candidate group's sums must hold exactly.
- Secondary: dates, transaction details, and the cumulative totals/balance
  context. Use the running Bank/Company totals as a supporting mathematical
  check: NEVER propose a suggestion whose sums break the running totals
  (FR-002b). If a group contradicts the balance context, do not suggest it.

OUTPUT FORMAT (this is critical):
- Output EXACTLY ONE block, nothing before it and nothing after it, of the form:
    ~~~
    [output]
    {"suggestions": [...], "chat_message": "..."}
    ~~~
- The block is a single JSON object. The ~~~ and [output] markers are
  required. Do NOT write any prose, explanation, or extra text before or after
  the block. The block IS your entire response.
- JSON schema — suggestions is an array; when there are no reconcilable sets
  return an empty array. Each suggestion is an object with exactly:
    * keys: array of the stable discrepancy_ids involved (2+ items).
    * type: "BROKEN_CHEQUE" or "REVERSAL" — or, when the user explicitly asked
      in chat for other reconcilables, a short human-readable name describing
      the extra set (e.g. "DUPLICATE").
    * company_items: array of the involved Company-side items, each
      {discrepancy_id, date, details, debit_credit, source: "Company"}.
    * bank_items: array of the involved Bank-side items, each
      {discrepancy_id, date, details, debit_credit, source: "Bank"}.
    * reason: a human-readable reason reflecting the mathematical check
      (e.g. "Broken cheque by company", "Reversal checks").
- A suggestion's keys MUST resolve to items that exist in the list you were
  given. The latest provided context is authoritative (FR-008a).
- chat_message: a short conversational summary of what you found (or a brief
  answer to the user's question when one is asked).
- Be as concise as possible — non-creative, no unnecessary narrative. For
  complex topics you MAY use a short analogy, and you MAY lengthen a response
  only when the question requires it (FR-008b).
- When there are no reconcilable sets, return {"suggestions": [], "chat_message":
  "..."} with a short chat_message saying nothing was found.
- When the user asks a question (question field present), answer it in context
  conversationally; you may additionally return suggestions.
"""


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
_OUTPUT_BLOCK_RE = re.compile(
    r"~~~\s*\[output\]\s*(.*?)\s*~~~", re.DOTALL
)


def parse_output_block(raw: str) -> AdvisorResponse:
    """Extract the ~~~ [output] ~~~ block from the agent's final response and
    parse its JSON body into AdvisorResponse.

    Mirrors ai_structure_detector.parse_output_block (the same ~~~ [output] ~~~
    extraction method used across the AI flows). The body is a single JSON
    object; pydantic validates it into the typed response.

    Raises:
        ValueError: If no [output] block is found or the JSON body fails
            pydantic validation.
    """
    text = (raw or "").strip()
    m = _OUTPUT_BLOCK_RE.search(text)
    if not m:
        # Fallback: try to read everything between [output] and the last ~~~
        m = re.search(r"\[output\]\s*(.*?)\s*~~~", text, re.DOTALL)
    if not m:
        raise ValueError(f"No [output] block found in agent response:\n{raw}")

    body = m.group(1).strip()
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in [output] block: {e}\nBlock body:\n{body}"
        ) from e
    try:
        return AdvisorResponse(**data)
    except Exception as e:
        raise ValueError(f"Invalid advisor output block: {e}") from e


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_model() -> LitellmModel:
    """Build the LiteLLM chat model from settings (model + API key), never
    hardcoding credentials. Mirrors ai_structure_detector._build_model()."""
    model_id = settings.AI_MODEL or "gemini/gemini-2.0-flash"
    api_key = settings.AI_API_KEY or ""
    if settings.AI_MODEL or settings.AI_API_KEY:
        return LitellmModel(model=model_id, api_key=api_key)
    # No env config: let the provider pick up its own env var (e.g. GOOGLE_API_KEY)
    return LitellmModel(model=model_id)


def _configure_tracing() -> None:
    """Enable OpenAI Agents SDK tracing with the configured API key
    (matches the existing AI flows)."""
    set_tracing_disabled(False)
    if settings.AI_TRACING_API_KEY:
        set_tracing_export_api_key(settings.AI_TRACING_API_KEY)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_agent() -> Agent:
    """Build the no-tools Reconciler Agent with the strict two-case
    instructions and the concise/authoritative rules.

    NOTE: no output_type — the agent returns its JSON inside a plain-text
    ~~~ [output] ~~~ block (DeepSeek's response-format is incompatible with the
    SDK's structured output path); parse_output_block consumes the block.
    """
    return Agent(
        name="Reconciler Agent",
        instructions=ADVISOR_INSTRUCTIONS,
        model=_build_model(),
    )


def _build_prompt(request: AdvisorReconcileRequest) -> str:
    """Serialize the full discrepancy context + cumulative balance context +
    history + optional question into the agent's prompt.

    The COMPLETE final discrepancies list is always sent in full, regardless
    of size — never sampled, summarized, or chunked (spec clarification).
    """
    lines = [
        "Here is the complete final discrepancies list for this reconciliation. "
        "Each item carries its stable key, date, details, signed amount "
        "(negative = debit, positive = credit), and source (FROM):",
    ]
    for item in request.discrepancies:
        lines.append(
            f"- [{item.discrepancy_id}] {item.Transaction_date} | "
            f"{item.Transaction_Detail} | {item.Debit_Credit:+.2f} | {item.FROM}"
            + (" | from_past" if item.from_past else "")
        )

    lines.append("\nCumulative Bank/Company balance context (running totals):")
    for point in request.context.points:
        lines.append(
            f"- [{point.index}] {point.discrepancy_id}: bank_running="
            f"{point.bank_running:+.2f}, company_running="
            f"{point.company_running:+.2f}, net={point.net:+.2f}"
        )
    lines.append(
        f"- Final: bank_balance={request.context.bank_balance:+.2f}, "
        f"company_balance={request.context.company_balance:+.2f}"
    )

    if request.history:
        lines.append("\nConversation history:")
        for message in request.history:
            lines.append(f"- {message.role}: {message.content}")

    if request.question:
        lines.append(
            f"\nThe user asks: {request.question}\n"
            "Answer concisely in context. You may additionally return "
            "suggestions for the two supported cases."
        )
    else:
        lines.append(
            "\nAnalyze the list strictly for the two supported cases "
            "(broken cheques/pairs and reversals) and return your JSON in the "
            "required ~~~ [output] ~~~ block."
        )

    return "\n".join(lines)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def run_advisor(
    request: AdvisorReconcileRequest,
    request_id: str,
    stream_callback=None,
    cancel_check=None,
) -> AdvisorResponse:
    """Run the Reconciler Agent with the unified 3-attempt retry (FR-006).

    Args:
        request: The full advisor request (discrepancies + balance context +
            history + optional question).
        request_id: The reconciliation request_id — keyed into the processing
            cancellation registry.
        stream_callback: Optional async callable receiving each raw text
            delta as the model streams (token-by-token, FR-008c).
        cancel_check: Optional callable returning True when the client
            requested cancellation (honors the existing 499 behavior).

    Returns:
        The parsed AdvisorResponse (suggestions + chat_message).

    Raises:
        asyncio.CancelledError: when the run is cancelled mid-stream.
        AdvisorError: after all attempts fail (friendly technical-failure
            message, no partial state).
    """
    _configure_tracing()
    from src.services.processing_cancellation import is_cancelled

    if cancel_check is None:
        cancel_check = lambda: is_cancelled(request_id)

    last_error: Optional[Exception] = None
    prompt = _build_prompt(request)

    for attempt in range(1, MAX_ADVISOR_ATTEMPTS + 1):
        if cancel_check():
            raise asyncio.CancelledError("Processing cancelled by user")

        logger.info("Advisor attempt %d/%d for request %s", attempt, MAX_ADVISOR_ATTEMPTS, request_id)
        try:
            agent = _build_agent()
            stream = Runner.run_streamed(agent, prompt, max_turns=10)

            # Expose the live cancel handle so a cancel request halts the
            # current LLM turn immediately (reuses the existing registry).
            from src.services.processing_cancellation import update_cancel_handle

            update_cancel_handle(request_id, stream.cancel)

            text_chunks: list[str] = []
            async for _event in stream.stream_events():
                if cancel_check():
                    stream.cancel()
                    raise asyncio.CancelledError("Processing cancelled by user")
                # Surface token deltas to the client as they arrive and keep a
                # running copy so we can parse the final ~~~ [output] ~~~ block.
                delta = getattr(_event, "delta", None)
                if delta is not None:
                    text_chunks.append(delta)
                    if stream_callback is not None:
                        await stream_callback(delta)

            # The agent's final response is the full streamed text (no
            # output_type), which carries the JSON inside the [output] block.
            full_text = "".join(text_chunks).strip()
            if not full_text:
                # Fallback: some providers expose the final text on final_output
                # even when no deltas were surfaced.
                full_text = str(stream.final_output or "").strip()
            return parse_output_block(full_text)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # If the user cancelled, don't treat the aborted stream as a
            # retryable failure — surface it as cancellation (499).
            if cancel_check():
                logger.info("Run %s cancelled during streaming, aborting", request_id)
                raise asyncio.CancelledError("Processing cancelled by user") from e
            last_error = e
            logger.warning(
                "Advisor attempt %d/%d failed for request %s: %s",
                attempt,
                MAX_ADVISOR_ATTEMPTS,
                request_id,
                e,
            )

    raise AdvisorError(
        message=FRIENDLY_ADVISOR_ERROR,
        retries_used=MAX_ADVISOR_ATTEMPTS,
    ) from last_error


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class AdvisorError(Exception):
    """Raised when the Reconciler Agent fails after exhausting all retries."""

    def __init__(self, message: str = FRIENDLY_ADVISOR_ERROR, retries_used: int = 0):
        super().__init__(message)
        self.message = message
        self.retries_used = retries_used


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
