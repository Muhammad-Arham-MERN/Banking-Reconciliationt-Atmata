# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Advisor request/response pydantic models (AI Reconciler Advisor, feature 007).

Typed structured output contract for the Reconciler Agent. Mirrors the
existing pydantic convention (reconciliation_models.py, api_models.py) and
the structured-output pattern used for FileStructureOutput. No persistence —
the advisor is stateless (FR-008a).
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class ChatMessage(BaseModel):
    """A single conversational message in the stateless chat history."""

    role: Literal["user", "assistant"] = Field(description="Sender of the message")
    content: str = Field(description="Message text")


class AdvisorDiscrepancy(BaseModel):
    """A single final unmatched transaction sent to the Reconciler Agent.

    Carries the stable backend-generated key (FR-002); the key is internal
    and never rendered in the UI. The wire format uses the safe underscore
    key Transaction_Detail (never the fragile spaced form of the raw
    reconciliation dicts) and keeps the Debit/Credit slash key the rest of
    the app already uses.
    """

    discrepancy_id: str = Field(description="Stable backend-generated key (e.g. 'Bank:1')")
    Transaction_date: str = Field(description="Transaction date (YYYY-MM-DD)")
    Transaction_Detail: str = Field(description="Transaction details")
    Debit_Credit: float = Field(
        alias="Debit/Credit",
        description="Signed amount: negative = debit, positive = credit",
    )
    FROM: Literal["Bank", "Company"] = Field(description="Source of the item")
    from_past: Optional[bool] = Field(default=None, description="History-merged entry flag")

    model_config = {"populate_by_name": True}


class BalancePoint(BaseModel):
    """One running-balance point over the discrepancy list, in list order."""

    index: int = Field(description="1-based position in the list")
    discrepancy_id: str = Field(description="The item this point belongs to")
    bank_running: float = Field(description="Cumulative Bank total up to and including this item")
    company_running: float = Field(description="Cumulative Company total up to and including this item")
    net: float = Field(description="bank_running + company_running")


class BalanceContext(BaseModel):
    """Cumulative Bank-vs-Company totals over the final discrepancies (FR-002b)."""

    points: List[BalancePoint] = Field(description="One point per discrepancy, in list order")
    bank_balance: float = Field(description="Final cumulative Bank total")
    company_balance: float = Field(description="Final cumulative Company total")


class AdvisorReconcileRequest(BaseModel):
    """Request body for POST /advisor/reconcile.

    Stateless (FR-008a): every follow-up re-sends the CURRENT live discrepancy
    context plus the conversation history, keyed by request_id.
    """

    request_id: str = Field(description="Reconciliation request_id; keys the conversation")
    discrepancies: List[AdvisorDiscrepancy] = Field(
        description="The COMPLETE final discrepancies list (never raw file data)"
    )
    context: BalanceContext = Field(description="Cumulative Bank/Company balance context")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    question: Optional[str] = Field(default=None, description="Optional follow-up question")


class AdvisorSuggestionItem(BaseModel):
    """A discrepancy item grouped inside a suggestion, labeled by side."""

    discrepancy_id: str = Field(description="Reference into the live list")
    date: str = Field(description="Transaction date")
    details: str = Field(description="Transaction details")
    debit_credit: float = Field(description="Signed amount")
    source: Literal["Bank", "Company"] = Field(description="FROM source")


class AdvisorSuggestion(BaseModel):
    """A group of 2+ discrepancy items forming a reconcilable set (FR-007)."""

    keys: List[str] = Field(description="Stable discrepancy_ids for the grouped items (2+)")
    type: str = Field(
        description=(
            "The suggestion type. Canonical types are BROKEN_CHEQUE and "
            "REVERSAL; when the user explicitly asks in chat, the agent may "
            "return an additional human-readable type name (e.g. DUPLICATE)."
        )
    )
    company_items: List[AdvisorSuggestionItem] = Field(description="Involved Company-side items")
    bank_items: List[AdvisorSuggestionItem] = Field(description="Involved Bank-side items")
    reason: str = Field(description="Human-readable reason reflecting the mathematical check")


class AdvisorResponse(BaseModel):
    """Typed structured output returned by the Reconciler Agent (FR-002a)."""

    suggestions: List[AdvisorSuggestion] = Field(
        default_factory=list, description="Agent suggestions; empty when none found"
    )
    chat_message: str = Field(description="Free-text conversational message alongside suggestions")


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
