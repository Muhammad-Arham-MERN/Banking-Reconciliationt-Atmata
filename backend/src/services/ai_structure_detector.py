# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
AI Structure Detector Service (Istikhraj e Data Ma'a AI)

Runs an OpenAI Agents SDK agent with three file-inspection tools to derive the
exact structure of an uploaded PDF bank statement and an Excel company ledger,
so the deterministic reconciliation pipeline can extract transactions from any
file layout without manual column mapping.

This module is the AI-side counterpart of the existing deterministic
processors (pdf_processor.py, excel_processor.py). The old flow is untouched
(FR-012); this service powers the new /reconcile-ai endpoint (FR-011).
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pdfplumber
from agents import Agent, OutputGuardrail, RunContextWrapper, Runner
from agents.decorators import tool
from agents.exceptions import OutputGuardrailTripwireTriggered
from agents.extensions.models.litellm_model import LitellmModel
from agents.guardrail import GuardrailFunctionOutput
from agents.tracing import set_tracing_disabled, set_tracing_export_api_key
from pydantic import BaseModel

from src.config import settings
from src.services.judge_structure_service import build_judge_tool
from src.services.pdf_structure_store import upsert_profile
from src.utils.structure_assessor import assess_pdf_structure

logger = logging.getLogger(__name__)

# Max detection attempts per file (FR-008): 3 retries on failed LLM behaviour.
MAX_DETECTION_ATTEMPTS = 3

# Max times the output guardrail may trip before the whole flow fails: after
# the main agent produces an output that fails the assessor/guardrail checks,
# it is re-run with the full conversation + failure feedback up to this many
# times. Independent of MAX_DETECTION_ATTEMPTS (LLM-failure retries).
MAX_GUARDRAIL_RETRIES = 3

# Friendly message shown to the user when detection fails (FR-009).
FRIENDLY_RETRY_MESSAGE = "We couldn't analyze your files. Please try again."

# Message shown when the agent exhausted its guardrail retries (failed output).
AGENT_FAILED_MESSAGE = "Agent failed to extract the PDF Structure."

# Message shown when the agent exhausted its LLM-failure retries (internal).
AGENT_INTERNAL_ERROR_MESSAGE = "Agent had internal server error."


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class AIDetectionError(Exception):
    """Raised when AI structure detection fails after exhausting retries."""

    def __init__(
        self,
        message: str = FRIENDLY_RETRY_MESSAGE,
        retries_used: int = 0,
        side: Optional[str] = None,
        reason: str = "unknown",
    ):
        super().__init__(message)
        self.message = message
        self.retries_used = retries_used
        self.side = side
        # reason: "guardrail_failed" (output failed the guardrail checks after
        # MAX_GUARDRAIL_RETRIES), "llm_failed" (LLM-failure retries exhausted),
        # or "unknown".
        self.reason = reason


class FileStructureOutput(BaseModel):
    """The machine-readable structure description emitted by the agent.

    Mirrors the canonical output contract from the validated prototype
    (test.py). Every field feeds the deterministic extractors directly.
    """

    columns_pdf: list[str]
    columns_excel: list[str]
    header_words_pdf: list[str]
    rows_dropped_pdf: int
    # Per-page support: a single scalar applies to every page; a 2-element
    # list [page1, page2] means page 1 differs from the continuation pages
    # (page 2's value is canonical for pages 3+). This matters for statements
    # whose first page carries an account-header block above the band while
    # continuation pages start straight at the data band.
    header_top_pdf: float | list[float]
    column_boundaries_pdf: list[float]
    band_top_pdf: float | list[float]
    date_pattern_pdf: str
    # Optional Opening Balance read from the statement header (usually the
    # upper region of page 1). It is NOT consumed by the deterministic
    # extractors (backward-compatible); the agent passes it to the
    # assess_structure evaluation tool, which uses it in the arithmetic and
    # closing-balance checks (FR-005).
    opening_balance_pdf: Optional[float] = None

    # ---- Explicit PDF column ROLES (agent-provided, replace fuzzy matching) --
    # The agent reads the exact header text and names WHICH columns_pdf entry
    # plays each role, instead of the system guessing by substring. This is
    # what the assessor's Saghir arithmetic and the production transformer use
    # to find the date/details/debit/credit/balance columns deterministically.
    # Exactly one of the two amount forms must be provided:
    #   - separate: pdf_debit_column + pdf_credit_column (both set)
    #   - combined: pdf_debit_credit_combined_column (set, rare)
    # pdf_balance_column is optional (some statements print no running balance);
    # when absent the arithmetic balance checks are skipped.
    pdf_transaction_date_column: Optional[str] = None
    pdf_details_column: Optional[str] = None
    pdf_debit_column: Optional[str] = None
    pdf_credit_column: Optional[str] = None
    pdf_debit_credit_combined_column: Optional[str] = None
    pdf_balance_column: Optional[str] = None



def parse_output_block(raw: str) -> FileStructureOutput:
    """Extract the ~~~ [output] ~~~ block from the agent's final response and
    parse it into FileStructureOutput.

    The agent is instructed to emit exactly one block:
        ~~~
        [output]
        columns_pdf: [...]
        ...
        ~~~
    Values are parsed as JSON where possible (lists, floats, ints, strings).

    Raises:
        AIDetectionError: If no parseable [output] block is found or the block
            fails pydantic validation.
    """
    import json
    import re

    text = raw.strip()
    # Find the block: ~~~ ... ~~~
    m = re.search(r"~~~\s*\[output\]\s*(.*?)\s*~~~", text, re.DOTALL)
    if not m:
        # Fallback: try to read everything between [output] and the last ~~~
        m = re.search(r"\[output\]\s*(.*?)\s*~~~", text, re.DOTALL)
    if not m:
        raise AIDetectionError(f"No [output] block found in agent response:\n{raw}")

    body = m.group(1).strip()
    data: dict = {}
    # Each line: name: value
    for line in body.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        # Try JSON first (handles lists, numbers, quoted strings).
        try:
            data[name] = json.loads(value)
        except json.JSONDecodeError:
            # Fallback: strip matching surrounding quotes if present.
            # Regex values like "^\d{2}/\d{2}/\d{2}$" fail JSON parsing because
            # \d is not a valid JSON escape, so they arrive still quoted.
            if len(value) >= 2 and value[0] == value[-1] == '"':
                data[name] = value[1:-1]
            else:
                data[name] = value

    try:
        return FileStructureOutput(**data)
    except Exception as e:
        raise AIDetectionError(f"Invalid structure output block: {e}")


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_guardrail_verdict_message(assessment: dict) -> str:
    """Build the human-readable verdict summary fed back to the agent on tripwire.

    Combines the assess_structure tool verdict (Saghir/Kabir/Ihsan) into one
    concise, actionable message.
    """
    parts = ["Your proposed structure FAILED the output guardrail validation."]

    assessor_summary = assessment.get("issues") or []
    if assessment.get("suggestions"):
        assessor_summary += assessment["suggestions"]
    if assessor_summary:
        parts.append("Assessor issues/suggestions:\n- " + "\n- ".join(str(s) for s in assessor_summary))

    kabir = assessment.get("kabir_check") or {}
    if kabir.get("tier"):
        parts.append(
            f"Kabir (completeness): tier={kabir.get('tier')}, "
            f"diff_pct={kabir.get('diff_pct')}, dated_leftovers={kabir.get('dated_leftovers')}"
        )
    ihsan = assessment.get("ihsan_check") or {}
    if ihsan.get("closing_balance") is not None:
        parts.append(
            f"Ihsan (closing-balance anchor): closing_balance={ihsan.get('closing_balance')}, "
            f"diff={ihsan.get('diff')}, page={ihsan.get('page')}"
        )

    parts.append(
        "You MUST fix your proposed structure (columns, boundaries, band_top, "
        "header_top, rows_dropped, date_pattern, opening balance, or the "
        "reconciliation type) so the assess_structure tool returns "
        "overall_pass: true, then re-emit the [output] block."
    )
    return "\n\n".join(parts)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_guardrail(
    verdict_holder: dict,
    request_id: Optional[str] = None,
) -> OutputGuardrail:
    """Build the output guardrail.

    The guardrail's ONLY job is to check the assess_structure tool's verdict
    (the overall_pass the agent already received in-conversation). It does not
    parse [output] blocks, re-run the assessor, or judge structure plausibility
    - it reads the tool's recorded verdict from the shared verdict_holder.

    Uses the SDK's native OutputGuardrail + GuardrailFunctionOutput so a
    tripwire raises OutputGuardrailTripwireTriggered with full run context.
    """
    from src.services.processing_cancellation import is_cancelled

    async def guardrail_fn(context, agent, agent_output):
        if request_id and is_cancelled(request_id):
            raise asyncio.CancelledError("Processing cancelled by user")

        assessment = verdict_holder.get("last")
        logger.info(
            "Output guardrail read verdict_holder['last']: present=%s, overall_pass=%s, "
            "keys=%s",
            assessment is not None,
            bool(assessment.get("overall_pass")) if assessment else None,
            sorted(assessment.keys()) if assessment else None,
        )
        if assessment:
            logger.info(
                "Output guardrail verdict details: saghir=%s, kabir=%s, ihsan=%s, "
                "total_rows=%s, rows_checked=%s, first_mismatch=%s",
                (assessment.get("cumulative_check") or {}).get("passed"),
                (assessment.get("kabir_check") or {}).get("passed"),
                (assessment.get("ihsan_check") or {}).get("passed"),
                assessment.get("total_rows"),
                (assessment.get("cumulative_check") or {}).get("rows_checked"),
                (assessment.get("cumulative_check") or {}).get("first_mismatch_row"),
            )
        if not assessment:
            # The agent never called assess_structure (its instructions mandate
            # it before emitting output) - there is no pass/fail verdict to
            # trust, so treat this as a failed validation.
            return GuardrailFunctionOutput(
                output_info={
                    "ok": False,
                    "verdict": (
                        "The agent did not call the assess_structure tool before "
                        "emitting its output, so there is no validation verdict. "
                        "Call assess_structure until it returns overall_pass: true."
                    ),
                    "assessment": None,
                },
                tripwire_triggered=True,
            )

        overall_pass = bool(assessment.get("overall_pass"))

        # The guardrail's pass/fail decision comes ONLY from the
        # assess_structure tool verdict (overall_pass).
        ok = overall_pass
        logger.info(
            "Output guardrail verdict: ok=%s (assessor=%s)",
            ok,
            overall_pass,
        )

        return GuardrailFunctionOutput(
            output_info={
                "ok": ok,
                "verdict": _build_guardrail_verdict_message(assessment),
                "assessment": assessment,
            },
            tripwire_triggered=not ok,
        )

    return OutputGuardrail(
        name="Assessor output guardrail (assess_structure verdict)",
        guardrail_function=guardrail_fn,
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_agent_tools(
    pdf_path: Path,
    excel_path: Path,
    sheet_name: str,
    request_id: Optional[str] = None,
    reconciliation_type: str = "bank",
    verdict_holder: Optional[dict] = None,
) -> list:
    """Create the file-inspection tools bound to the uploaded file paths.

    The prototype (test.py) read from hardcoded assets_dev paths; in the real
    flow the files arrive as multipart uploads, so the tools are closures over
    the request's saved file paths.

    Args:
        request_id: Optional request id forwarded into the assess_structure
            tool so the assessor's nested LLM runs honor the cancellation
            registry (a cancel request halts the evaluation mid-run).
        reconciliation_type: Which books the statement belongs to - "bank"
            (default) or "vendor". Becomes the default the agent starts from
            when calling assess_structure (the agent may still override it).

    Returns:
        List of tools for the Agent: judge_structure_by_cover, read_excel,
        read_pdf, read_pdf_words, assess_structure.
    """

    @tool
    def read_excel(drop: int = 0, lines: int = 3) -> str:
        """Read `lines` rows of an Excel file starting after `drop` rows and return them as a table.

        Args:
            drop: How many initial rows to skip (default 0).
            lines: How many rows to show (default 3).
        """
        df = pd.read_excel(excel_path, header=None, sheet_name=sheet_name)
        return df.iloc[drop : drop + lines].to_string(index=False, header=False)

    @tool
    def read_pdf(drop: int = 0, lines: int = 3, page: Optional[int] = None) -> str:
        """Read `lines` rows of the tables found in a PDF and return them as tables.

        Use `page` (0-based) to inspect a specific page's table (e.g. page=1 for
        page 2's table) so you can compare page 1 vs page 2 content.

        Args:
            drop: How many initial rows to skip in each table (default 0).
            lines: How many rows to show per table (default 3).
            page: 0-based page index to inspect (default None = all pages).
        """
        tables = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages = [pdf.pages[page]] if page is not None else pdf.pages
            for pg in pages:
                table = pg.extract_table()
                if table:
                    tables.append(pd.DataFrame(table[1:], columns=table[0]))
        if not tables:
            return "No tables found in PDF."
        return "\n\n".join(
            f"Table {i + 1}:\n{tbl.iloc[drop : drop + lines].to_string(index=False)}"
            for i, tbl in enumerate(tables)
        )

    @tool
    def read_pdf_words(drop: int = 0, lines: int = 10, page: Optional[int] = None) -> str:
        """Read the raw word geometry of the FIRST TWO pages of the PDF in one call.

        Returns each word with its physical x0..x1 span and the line's top
        coordinate, grouped into visual lines. This is the ONLY tool that shows
        where columns actually start and end on the page.

        By default BOTH page 1 and page 2 are returned, separated by a clear
        divider, so you can compare their header/band positions in a single call.
        Use `drop` and `lines` to page through the visual lines (default 10 lines
        per page). Use `page` (0-based) to inspect only one specific page.

        Args:
            drop: How many initial visual lines to skip (default 0).
            lines: How many visual lines to show per page (default 10).
            page: 0-based page index to inspect alone (default None = pages 1-2).
        """
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages_to_show = [pdf.pages[page]] if page is not None else pdf.pages[:2]
            pages_words = []
            for page_obj in pages_to_show:
                pages_words.append(page_obj.extract_words())

        out = []
        for pi, words in enumerate(pages_words):
            if page is None:
                out.append(f"\n========== PAGE {pi + 1} OF 2 ==========")
            else:
                out.append(f"\n========== PAGE {page + 1} ==========")
            visual_lines: dict[float, list[dict]] = {}
            for w in words:
                visual_lines.setdefault(round(w["top"], 1), []).append(w)
            sorted_tops = sorted(visual_lines)
            for top in sorted_tops[drop : drop + lines]:
                row_words = sorted(visual_lines[top], key=lambda w: w["x0"])
                cells = " ".join(
                    f"{w['text']!r}[{w['x0']:.1f}-{w['x1']:.1f}]" for w in row_words
                )
                out.append(f"top={top:7.1f} | {cells}")
            if not visual_lines:
                out.append("No words found on this page.")
        return "\n".join(out) if out else "No words found in this range."

    @tool
    def assess_structure(
        columns_pdf: list[str],
        header_top_pdf: float | list[float],
        rows_dropped_pdf: int,
        column_boundaries_pdf: list[float],
        band_top_pdf: float | list[float],
        date_pattern_pdf: str,
        pdf_transaction_date_column: str,
        pdf_details_column: str,
        pdf_debit_column: Optional[str] = None,
        pdf_credit_column: Optional[str] = None,
        pdf_debit_credit_combined_column: Optional[str] = None,
        pdf_balance_column: Optional[str] = None,
        opening_balance: Optional[float] = None,
        reconciliation_type: str = reconciliation_type,
        entity_name: Optional[str] = None,
    ) -> str:
        """Score the proposed PDF structure with THREE complementary checks.

        Runs the production extractor with your current proposed structure
        (columns_pdf, header_top_pdf, column_boundaries_pdf, band_top_pdf,
        date_pattern_pdf, rows_dropped_pdf) and validates the extracted data
        three ways:

          (1) SAGHIR - the statement's own arithmetic: every transaction moves
              a running balance, so the extracted rows must be self-consistent
              (per-row cumulative sweep vs the Cumulative Balance column
              within a 50-unit tolerance, plus a final opening + net change
              check). Supports SPARSE balances: the running total always
              advances on every row, and is compared only where the statement
              prints a balance cell (Habib-style statements print one balance
              per day-group).
          (2) KABIR - completeness: an independent raw extraction (no
              band/header clipping, no reuse of your structure) date-filters
              every visual line of the PDF and compares the raw dated row
              count against your structure's row count. A structure that
              silently drops entire pages can pass Saghir (an empty page
              fails no arithmetic) but cannot pass Kabir.
          (3) IHSAN - the closing-balance anchor (final gate): a nested agent
              reads the statement's printed CLOSING BALANCE from the tail
              pages, and the assessor checks opening + net change against it
              (same 50-unit tolerance). This defeats the self-consistent-
              subset trap - a dropped final-day group passes Saghir and Kabir
              but FAILS Ihsan. Ihsan runs only when Saghir AND Kabir both
              passed (strict short-circuit); an inconclusive Ihsan (no closing
              balance printed) defers to the deterministic checks.

        Pass `opening_balance` = the Opening Balance figure you read from the
        statement - usually in the UPPER part of page 1 (around the header
        block, near the top, just above or near the first data rows) but NOT
        always exactly the first row of the table or only in the header
        block; look dynamically in that upper region for any figure labelled
        as an opening/start balance. It is auto-verified against the first
        cumulative row. Omit it (or pass None) when the statement has no
        usable opening-balance figure - the arithmetic checks still run and
        verify against the first cumulative row.

        Pass `reconciliation_type` = "bank" (default) or "vendor". The Debit
        and Credit columns are always unsigned magnitudes; the sign they
        carry depends on whose books the statement belongs to:
          - "bank":   Credit is money in (+) and Debit is money out (-), so
                      the signed amount is credit - debit.
          - "vendor": the roles invert (a vendor ledger records a credit as a
                      debt the vendor owes you, i.e. negative, and a debit as
                      money you owe, i.e. positive), so the signed amount is
                      debit - credit.
        The statement's Cumulative Balance column is compared directly, so
        only the sign applied to the two amount columns flips between the two
        types. A structure that passes as "bank" will FAIL as "vendor" (and
        vice versa) if you choose the wrong type - pick the one matching the
        file you are reading.

        COLUMN ROLES (critical): name EXACTLY which entry of columns_pdf
        plays each role, using the exact header text as it appears in
        read_pdf_words. The system does NOT guess roles from column names -
        you tell it. Exactly ONE amount form must be provided:
          - separate Debit + Credit columns: set BOTH pdf_debit_column and
            pdf_credit_column (leave pdf_debit_credit_combined_column null).
          - combined Debit/Credit column (rare): set
            pdf_debit_credit_combined_column (leave both debit and credit
            null).
        pdf_transaction_date_column and pdf_details_column are required.
        pdf_balance_column is optional (the running Balance/Cumulative
        column); when the statement prints no running balance, omit it and
        the arithmetic balance checks are skipped.

        Returns a JSON verdict: 'overall_pass' true only when ALL THREE
        checks pass. On failure, 'issues'/'suggestions',
        'cumulative_check.first_mismatch_row', 'kabir_check' (tier, diff_pct,
        dated_leftovers), and 'ihsan_check' (closing_balance, diff, page)
        pinpoint the problem - fix your structure (band_top, boundaries,
        column order, the opening balance, or the reconciliation type) and
        call this tool again until it passes.

        Args:
            columns_pdf: The full list of PDF column names, left-to-right.
            header_top_pdf: Header line top (scalar or [page1, page2]).
            rows_dropped_pdf: Visual lines above the header.
            column_boundaries_pdf: x-coordinates between adjacent columns.
            band_top_pdf: First data row top (scalar or [page1, page2]).
            date_pattern_pdf: Regex matching the transaction dates.
            pdf_transaction_date_column: Exact name of the date column.
            pdf_details_column: Exact name of the description/details column.
            pdf_debit_column: Exact name of the Debit column (with
                pdf_credit_column) for the separate amount form.
            pdf_credit_column: Exact name of the Credit column (with
                pdf_debit_column) for the separate amount form.
            pdf_debit_credit_combined_column: Exact name of the combined
                Debit/Credit column for the rare combined form.
            pdf_balance_column: Exact name of the running Balance/Cumulative
                column (optional).
            opening_balance: Opening Balance from the statement header (optional).
            reconciliation_type: "bank" (default) or "vendor" - which books
                the statement belongs to (controls the Credit/Debit sign).
            entity_name: The bank/vendor name you read from the PDF (the
                statement header / letterhead). Pass it when the PDF carries an
                identifiable name - when this structure fully passes
                (overall_pass: true), it is PERSISTED for future runs under
                this name, so the next upload of the same bank/vendor skips
                full detection. OMIT it when the PDF has no identifiable name:
                a nameless structure is never persisted.
        """
        import json as _json

        # Enforce the mutually-exclusive amount-column contract up front so
        # the agent cannot call the tool with a half-specified structure.
        has_separate = pdf_debit_column is not None or pdf_credit_column is not None
        has_combined = pdf_debit_credit_combined_column is not None
        if has_separate and has_combined:
            return _json.dumps(
                {
                    "overall_pass": False,
                    "issues": [
                        "Provide EITHER separate pdf_debit_column + "
                        "pdf_credit_column OR the combined "
                        "pdf_debit_credit_combined_column, not both."
                    ],
                    "suggestions": [
                        "Pick the amount form that matches the statement and "
                        "re-call assess_structure."
                    ],
                }
            )
        if has_separate and (pdf_debit_column is None or pdf_credit_column is None):
            return _json.dumps(
                {
                    "overall_pass": False,
                    "issues": [
                        "Both pdf_debit_column AND pdf_credit_column must be "
                        "set when using the separate amount form."
                    ],
                    "suggestions": [
                        "Set both debit and credit column names (or switch to "
                        "the combined form)."
                    ],
                }
            )
        if not has_separate and not has_combined:
            return _json.dumps(
                {
                    "overall_pass": False,
                    "issues": [
                        "No amount column provided: set pdf_debit_column + "
                        "pdf_credit_column (separate form) or "
                        "pdf_debit_credit_combined_column (combined form)."
                    ],
                    "suggestions": [
                        "Name the amount column(s) exactly as they appear in "
                        "the header."
                    ],
                }
            )

        assessment = assess_pdf_structure(
            pdf_path=pdf_path,
            columns=columns_pdf,
            header_top=header_top_pdf,
            rows_dropped=rows_dropped_pdf,
            boundaries=column_boundaries_pdf,
            band_top=band_top_pdf,
            date_pattern=date_pattern_pdf,
            opening_balance=opening_balance,
            reconciliation_type=reconciliation_type,
            entity_name=entity_name,
            use_ihsan=True,
            request_id=request_id,
            pdf_transaction_date_column=pdf_transaction_date_column,
            pdf_details_column=pdf_details_column,
            pdf_debit_column=pdf_debit_column,
            pdf_credit_column=pdf_credit_column,
            pdf_debit_credit_combined_column=pdf_debit_credit_combined_column,
            pdf_balance_column=pdf_balance_column,
        )
        # Record the verdict in the shared holder so the output guardrail can
        # check it (the guardrail's ONLY input is this tool's pass/fail).
        if verdict_holder is not None:
            verdict_holder["last"] = assessment
            logger.info(
                "assess_structure tool wrote verdict_holder['last']: overall_pass=%s, "
                "saghir=%s, kabir=%s, ihsan=%s, total_rows=%s, issues=%s",
                assessment.get("overall_pass"),
                (assessment.get("cumulative_check") or {}).get("passed"),
                (assessment.get("kabir_check") or {}).get("passed"),
                (assessment.get("ihsan_check") or {}).get("passed"),
                assessment.get("total_rows"),
                assessment.get("issues"),
            )
        # Persistence hook: any fully-passing, NAMED structure is upserted to
        # the store so future uploads of the same bank/vendor skip full
        # detection (Path A). Fires on Path A (a corrected known-entity
        # structure keeps the store fresh when a bank changes layout) and on
        # Path B (a brand-new entity). Fire-and-log: a DB failure is logged and
        # never fails the reconciliation (fail-open).
        #
        # ONLY the PDF structure is persisted - never the Excel structure.
        # The stored profile is consumed by assess_structure on the next run
        # (PDF params only), so columns_excel has no place here.
        #
        # This tool must stay SYNC (def, not async def): the SDK runs sync
        # tools in a worker thread with no running event loop, which is what
        # the assessor's nested AgentRunner.run_sync() calls (Kabir/Ihsan)
        # require. The asyncpg upsert is bridged onto the MAIN loop (where the
        # pool lives) from the worker thread - never a fresh loop, which would
        # raise "Future attached to a different loop".
        if bool(assessment.get("overall_pass")) and entity_name:
            try:
                structure_payload = {
                    "columns_pdf": columns_pdf,
                    "rows_dropped_pdf": rows_dropped_pdf,
                    "header_top_pdf": header_top_pdf,
                    "column_boundaries_pdf": column_boundaries_pdf,
                    "band_top_pdf": band_top_pdf,
                    "date_pattern_pdf": date_pattern_pdf,
                    "opening_balance_pdf": opening_balance,
                    "pdf_transaction_date_column": pdf_transaction_date_column,
                    "pdf_details_column": pdf_details_column,
                    "pdf_debit_column": pdf_debit_column,
                    "pdf_credit_column": pdf_credit_column,
                    "pdf_debit_credit_combined_column": pdf_debit_credit_combined_column,
                    "pdf_balance_column": pdf_balance_column,
                    "reconciliation_type": reconciliation_type,
                }
                from src.services.db_service import run_on_main_loop

                def _fire_upsert() -> None:
                    try:
                        run_on_main_loop(
                            lambda: upsert_profile(
                                entity_name=entity_name,
                                entity_type=reconciliation_type,
                                structure=structure_payload,
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to persist structure profile for %r (fire-and-log): %s",
                            entity_name,
                            e,
                        )

                # Fire-and-forget: do not block the agent turn on the DB write.
                import threading

                threading.Thread(
                    target=_fire_upsert,
                    name=f"upsert-profile-{entity_name}",
                    daemon=True,
                ).start()
            except Exception as e:
                logger.warning(
                    "Failed to persist structure profile for %r (fire-and-log): %s",
                    entity_name,
                    e,
                )
        return _json.dumps(assessment, indent=2, default=str)

    return [
        build_judge_tool(
            pdf_path,
            reconciliation_type=reconciliation_type,
            request_id=request_id,
        ),
        read_excel,
        read_pdf,
        read_pdf_words,
        assess_structure,
    ]


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
AGENT_INSTRUCTIONS = """
You are an agent that is part of a complex Banking Reconciliation System, here are some details:
What is your task? Your task is to identify the exact page properties (defined later) intelligently, that can be passed to the Reconciliation System for easily extracting data from pdf and excel and compare them.

Why you are important? There are multiple pdfs and excels, they can have completely different format and structure, defining each format systematically is non-feasible for any System, so you are given such tools you can use to identify such page properties that can be input in our deterministic system and get results from pdf and excel accurately.

How is ths achieved? You have 5 tools for reading pdf and excel and evaluating results

[JUDGE - CALL THIS FIRST]
  - FIRST, before any file inspection, call the judge_structure_by_cover tool. It reads whose PDF this is from its first lines and checks whether the system already knows that bank/vendor's PDF structure. It returns either:
      * "KNOWN_ENTITY <name>:" followed by the full stored structure JSON, or
      * "NO_DATA" (unknown/new entity, or the judge tool errored).
  - If it returns a KNOWN structure: DO NOT re-detect from scratch. Take those stored values (columns_pdf, header_top_pdf, column_boundaries_pdf, band_top_pdf, date_pattern_pdf, rows_dropped_pdf, opening_balance_pdf, and the column roles), call assess_structure with them + the entity name to VERIFY they still fit THIS file. If assess_structure passes (overall_pass: true), emit the [output] block with those values. If it fails (the bank changed its layout), FIX the structure and re-validate with assess_structure, or fall back to full detection from scratch.
  - If it returns NO_DATA (new file, or the judge tool errors/returns garbage): detect the structure from scratch as usual.
  - When you identify the bank/vendor name from the PDF, pass it as entity_name to assess_structure. OMIT it only when the PDF has no identifiable name (a nameless structure is never persisted).

[EXCEL]
  - Use excel read tool and get column names, you may not see column names in first call because only one row is returned you may have to reuse tool until you get to column names.
  - You will return columns only these 4 or 5 columns from the lot, in this exact order:
      Combined Debit/Credit case (4 columns): [transaction date column name, transaction details column name, Total/Sum column name, Debit/Credit column name]
      Separate Debit/Credit case (5 columns): [transaction date column name, transaction details column name, Total/Sum column name, Debit column name, Credit column name]
  - Column role definitions (apply these to the Excel file, exactly like the PDF rules):
      * transaction date column: the column whose values are the transaction dates (e.g. "Posting Date", "Date", "Tran. Date", "Transaction Date").
      * transaction details column: the description/narrative/particulars column (e.g. "Details", "Description", "Particulars", "Narrative").
      * Total/Sum/Cumulative column: the column whose value is the CONTINUOUS RUNNING TOTAL of the debit and credit amounts — the balance after each row, built up from an opening balance and accumulating row by row (e.g. "Cumulative Balance (LC)", "Running Balance", "Balance", "Total", "Sum", "Closing Balance"). It is NOT a column of individual transaction amounts, and NOT a per-row debit or credit amount. Name an exact column that exists in the file; never invent a name.
      * amount column(s): the column(s) holding the individual transaction amounts — either a single combined Debit/Credit column (4-column case) or separate Debit and Credit columns (5-column case, e.g. "Debit (LC)" and "Credit (LC)").
  - Every value you name MUST be an exact header text present in the Excel file — never invent a column name.

[PDF]
  - Use the pdf read tool to see the table CONTENT row by row (dates, details, amounts).
  - Use the read_pdf_words tool to see the GEOMETRY of the FIRST TWO pages in ONE call (it returns page 1 AND page 2, each word with its x0..x1 span and line top coordinate, separated by a divider).
    * The reason is that in some cases there are such pdfs whose 1st page differs than second page, and in most cases the 1st page matches exactly the 2nd pages and so on, so in the first special case, instead of 1st page, the 2nd page's structure becomes canonical for all other pages
  - Identify the exact line where the column headers live (the line containing header words like "Tran. Date", "Debit", "Credit", "Balance","cheque ref" etc).
  - Report the header words you found EXACTLY as they appear in the read_pdf_words output, in left-to-right order, together with the line's top coordinate.
  - Report the number of visual lines above the header line that had to be skipped (rows dropped). The header line itself is NOT counted as dropped.
  - Group the header words into columns: words that together form one header (e.g. "Tran." "Date" -> "Tran. Date", "Chq" "/" "Ref" "No" -> "Chq / Ref No") belong to ONE group; a gap between two groups marks a column boundary.
  - Compute column_boundaries_pdf: for every gap between two adjacent column groups, the boundary is the midpoint between the previous group's rightmost x1 and the next group's leftmost x0. This yields exactly (number of columns - 1) ascending x-coordinates.
  - VERIFY each boundary against the DATA rows shown by read_pdf_words (not just the header): a boundary must fall in an empty gap, and no data word may straddle it. If a boundary would cut a data column, shift it to the widest empty gap between that column's words and the next column's words.
  - Identify the transaction band top: band_top_pdf = the top coordinate of the first data row (just below the header line).
  - Identify the date pattern: look at the first-column dates in the data rows (e.g. "05-MAY-26") and report a regex that matches exactly those date strings (e.g. ^\\d{2}-[A-Z]{3}-\\d{2}$).
  - COLUMN ROLES (critical): the system does NOT guess which column is which - YOU name them, using the EXACT header text as it appears in read_pdf_words. Identify:
      * pdf_transaction_date_column: the transaction-date column (e.g. "Tran. Date", "Booking Date", "Date").
      * pdf_details_column: the description/narrative/particulars column (e.g. "Transaction Details", "Description", "Particulars").
      * The amount columns, in EXACTLY ONE of these two forms:
          - separate form (standard): pdf_debit_column + pdf_credit_column (both, e.g. "Debit" and "Credit", "Debit (LC)" and "Credit (LC)").
          - combined form (rare): pdf_debit_credit_combined_column (a single column holding both debit and credit, e.g. "C/D (LC)").
      * pdf_balance_column (optional): the running Balance/Cumulative/Closing Balance column (e.g. "Balance", "Cumulative", "Closing Balance"). Omit it (null) when the statement prints no running balance.
    Every role value MUST be one of the entries in columns_pdf - never invent a name that is not on the page.
  - PER-PAGE BAND/HEADER CONTRACT (critical): read_pdf_words shows BOTH page 1 and page 2 in the SAME call. Read the ACTUAL top coordinates for EACH page from that output. Only band_top and header_top can differ between pages - the columns and boundaries are always global.
    * For EACH page, identify the header line top (the line containing "Tran. Date"/"Debit"/"Credit" etc.) and the band top (the first data row just below the header).
    * If page 1 and page 2 have the SAME header line top and SAME first-data-row top, emit band_top_pdf and header_top_pdf as SINGLE scalar numbers (this is the standard case).
    * If they DIFFER (e.g. page 1 has an account header block above the table, page 2 starts straight at the table), emit each as a 2-element list: [page1_value, page2_value]. Page 2's value is the canonical structure for all continuation pages (pages 3+ reuse page 2's value automatically).
  - Identify the Opening Balance: the figure from which debits are subtracted and to which credits are added (it may be labelled "Opening Balance", "B/F", "Balance Brought Forward", "Balance at Period Start", "Ledger", etc.). It is usually found in the UPPER part of page 1 - around the header block, near the top, just above or near the first data rows - but do NOT assume it is exactly the first row of the table or only in the header block. Look dynamically in the upper region of the page (header area and the lines just above/between the header and the first rows) for any figure labelled as an opening/start balance, and pass what you find to the assess_structure tool and emit it as opening_balance_pdf. If none exists, omit it (use null) - the assessor will still run the arithmetic checks and auto-verify the balance against the first cumulative row.
  - VALIDATE with assess_structure: BEFORE emitting your final output block, call the assess_structure tool with your proposed structure, the opening balance, and the reconciliation type ("bank" or "vendor"). It scores your structure THREE ways: (1) SAGHIR re-runs the extractor and checks the statement's own arithmetic (running balance vs the Cumulative Balance column on every row that prints a balance - sparse balances supported; in a "bank" statement Credit is + and Debit is -; in a "vendor" ledger the roles invert (Credit -, Debit +). Pick the type that matches the file - if you choose the wrong one, the running balance will diverge and you must switch it. (2) KABIR independently counts the raw dated rows of the PDF (no band/header clipping) and compares them against your structure's row count - it catches structures that silently drop whole pages, which Saghir cannot see. (3) IHSAN (final gate, runs only after Saghir AND Kabir pass) reads the statement's printed CLOSING BALANCE from the tail pages and checks opening + net change against it - this catches a dropped final-day group that Saghir and Kabir both miss. If 'overall_pass' is false, read 'issues'/'suggestions'/'cumulative_check.first_mismatch_row'/'kabir_check' (tier, diff_pct, dated_leftovers)/'ihsan_check' (closing_balance, diff, page), fix your structure (band_top, boundaries, column order, opening balance, or reconciliation type), and call assess_structure again. Only emit the output block once assess_structure returns overall_pass: true (or a non-perfect score with no arithmetic failure).

YOUR OUTPUT (follow this contract EXACTLY). These values feed a deterministic extractor (extract_pdf) directly - ALL of them are mandatory:
  - columns_pdf: The list of all pdf columns
  - columns_excel: the required column names from the Excel file, in the exact order [date, details, Total/Sum, amount column(s)]. 4 names for the combined Debit/Credit case, 5 names for the separate Debit + Credit case.
  - header_words_pdf: the exact header word strings from read_pdf_words, in left-to-right order.
  - rows_dropped_pdf: number of visual lines above the header line.
  - header_top_pdf: the numeric 'top=' coordinate of the header line, as a scalar OR [page1, page2] per the contract above.
  - column_boundaries_pdf: the x-coordinates between adjacent columns (midpoints of the empty gaps), ascending, exactly len(columns_pdf) - 1 values.
  - band_top_pdf: the top coordinate of the first transaction data row, as a scalar OR [page1, page2] per the contract above.
  - date_pattern_pdf: the regex matching the transaction dates.
  - opening_balance_pdf: the Opening Balance figure from the statement header (a number, e.g. 1542389.32). Omit it (or use null) when the statement has no usable opening-balance header.
  - COLUMN ROLES (all values MUST be exact entries from columns_pdf):
      * pdf_transaction_date_column (required): the date column name.
      * pdf_details_column (required): the description/details column name.
      * Amount columns - EXACTLY ONE form:
          - pdf_debit_column + pdf_credit_column (separate form), OR
          - pdf_debit_credit_combined_column (combined form, rare).
        Never provide both forms. The unused form's value is null.
      * pdf_balance_column (optional, null when no running balance): the
        Balance/Cumulative/Closing Balance column name.

OUTPUT FORMAT (this is critical):
  - Output EXACTLY ONE block, nothing before it and nothing after it, of the form:
    ~~~
    [output]
    columns_pdf: ["Tran. Date", "Effect Date"]
    columns_excel: [...]
    header_words_pdf: [...]
    rows_dropped_pdf: 22
    header_top_pdf: 167.7
    column_boundaries_pdf: [50.5, 95.0, 200.0, 260.0, 305.0, 357.5, 420.0, 490.0, 540.0, 575.0]
    band_top_pdf: 181.3
    date_pattern_pdf: "regex date pattern"
    opening_balance_pdf: 1542389.32 (normalized, system accepts only positive (+) or negative (-) float values)
    pdf_transaction_date_column: "Tran. Date"
    pdf_details_column: "Tran. Br.Transaction Details"
    pdf_debit_column: "Debit"
    pdf_credit_column: "Credit"
    pdf_debit_credit_combined_column: null
    pdf_balance_column: "Balance"
    ~~~
  - If page 1 and page 2 DIFFER, use the list form (values are EXAMPLES ONLY - you must measure the REAL page 1 and page 2 tops from read_pdf_words):
    ~~~
    [output]
    columns_pdf: ["Booking Date", "Debit", "Credit"]
    columns_excel: [...]
    header_words_pdf: [...]
    rows_dropped_pdf: 11
    header_top_pdf: [<REAL_page1_header_top>, <REAL_page2_header_top>]
    column_boundaries_pdf: [119.6, 202.65, 267.1, 325.65, 378.45, 441.3, 497.85]
    band_top_pdf: [<REAL_page1_band_top>, <REAL_page2_band_top>]
    date_pattern_pdf: "^\\d{2} [A-Z]{3} \\d{4}$"
    opening_balance_pdf: <REAL_opening_balance> (normalized, system accepts only positive (+) or negative (-) float values)
    pdf_transaction_date_column: "Booking Date"
    pdf_details_column: "Description"
    pdf_debit_column: "Debit"
    pdf_credit_column: "Credit"
    pdf_debit_credit_combined_column: null
    pdf_balance_column: "Closing Balance"
    ~~~
  - CRITICAL: NEVER copy placeholder numbers from the examples. Every value MUST come from actually reading the tool output. If you have not yet inspected page 2 (page=1) with read_pdf_words, you MUST call it before emitting the block.
  - The ~~~
    [output]
    ...
    ~~~
    markers are required. Inside the block, each variable name and its value, one per line, as `name: value`. Do NOT write any prose, explanation, or extra text before or after the block. The block IS your entire response.
"""


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_agent(
    pdf_path: Path,
    excel_path: Path,
    sheet_name: str,
    request_id: Optional[str] = None,
    reconciliation_type: str = "bank",
    verdict_holder: Optional[dict] = None,
) -> Agent:
    """Build the structure-detection Agent bound to the uploaded files.

    Uses environment-configured model + API key (FR-010); never hardcodes
    credentials. Falls back to the prototype's default model string only for
    local dev when AI_MODEL is unset.

    Attaches the output guardrail, which validates the agent's final output
    against the assess_structure tool verdict (overall_pass). The agent also
    carries the judge_structure_by_cover agent-as-tool, which it is instructed
    to call FIRST so a known bank/vendor's stored structure short-circuits full
    detection (Judge Structure by its Cover).

    Args:
        request_id: Optional request id forwarded into the tools so the
            assess_structure evaluation honors cancellation.
        reconciliation_type: "bank" (default) or "vendor" - the default the
            agent starts from when evaluating its proposed structure.
        verdict_holder: Shared dict used by the assess_structure tool to
            record its last verdict; the guardrail reads it.
    """
    return Agent(
        name="Excel/PDF extraction agent",
        instructions=AGENT_INSTRUCTIONS,
        model=_build_model(),
        tools=build_agent_tools(
            pdf_path,
            excel_path,
            sheet_name,
            request_id=request_id,
            reconciliation_type=reconciliation_type,
            verdict_holder=verdict_holder,
        ),
        # CRITICAL: pass the SAME dict object to both the tool and the
        # guardrail. `verdict_holder or {}` would create a NEW empty dict when
        # the holder is still empty (an empty dict is falsy) - the tool would
        # write to the original and the guardrail would read the new one,
        # guaranteeing a bogus "agent never called assess_structure" tripwire
        # on the first attempt. Normalize ONCE here so both share one object.
        output_guardrails=[_build_guardrail(verdict_holder, request_id=request_id)],
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_model() -> LitellmModel:
    """Build the LiteLLM model from settings (model + API key), never hardcoding
    credentials. Falls back to the prototype's default model string only for
    local dev when AI_MODEL is unset."""
    model_id = settings.AI_MODEL or "gemini/gemini-2.0-flash"
    api_key = settings.AI_API_KEY or ""
    if settings.AI_MODEL or settings.AI_API_KEY:
        return LitellmModel(model=model_id, api_key=api_key)
    # No env config: let the provider pick up its own env var (e.g. GOOGLE_API_KEY)
    return LitellmModel(model=model_id)


OUTPUT_AGENT_INSTRUCTIONS = """
You are the final-output formatter for a Banking Reconciliation System.

You are given the ENTIRE final response of a special structure-detection agent.
That agent investigated a PDF bank statement and an Excel ledger and produced a
set of detected structure parameters. Its final response may contain the
parameters in a `~~~ [output] ... ~~~` block, or as plain text near the end, or
embedded in prose — the exact format is unreliable.

Your ONLY job: find the ABSOLUTE CANONICAL FINAL structure values that the
detection agent ultimately settled on (the values it validated with its
assessor tool, i.e. the ones in its final `[output]` block when present — never
an earlier rejected attempt), and re-emit them in the EXACT block format below.

WHY THIS FORMAT IS REQUIRED: downstream, our deterministic parser extracts each
field from a `~~~ [output] ... ~~~` block, one `name: value` per line. It
cannot read prose or reasoning. If you do not emit this exact block, the whole
reconciliation fails. This is a hard requirement, not a suggestion.

OUTPUT FORMAT (this is critical):
  - Output EXACTLY ONE block, nothing before it and nothing after it, of the
    form:
    ~~~
    [output]
    columns_pdf: ["Date", "Particulars", "Debit", "Credit", "Balance"]
    columns_excel: ["Posting Date", "Details", "Cumulative Balance (LC)", "Debit (LC)", "Credit (LC)"]
    header_words_pdf: ["Date", "Particulars", "Debit", "Credit", "Balance"]
    rows_dropped_pdf: 11
    header_top_pdf: [204.4, 203.4]
    column_boundaries_pdf: [81.65, 316.25, 396.7, 487.25]
    band_top_pdf: [243.0, 239.7]
    date_pattern_pdf: "\\d{2}-[A-Za-z]{3}-\\d{4}"
    opening_balance_pdf: 5270158.54
    pdf_transaction_date_column: "Date"
    pdf_details_column: "Particulars"
    pdf_debit_column: "Debit"
    pdf_credit_column: "Credit"
    pdf_debit_credit_combined_column: null
    pdf_balance_column: "Balance"
    ~~~
  - The `~~~` and `[output]` markers are required, and the block IS your entire
    response.
  - Lists are JSON arrays, numbers are JSON numbers, strings are JSON strings
    (note: date_pattern_pdf is a STRING, so it must be double-quoted).
  - date_pattern_pdf BACKSLASH RULE (critical): the emitted value must use
    SINGLE backslashes in the regex class escapes - e.g.
    date_pattern_pdf: "^\\d{2}-[A-Z]{3}-\\d{4}$"  (each "\\d" is exactly one
    backslash + "d", NOT two backslashes). If the detection agent's raw text
    contains a doubled form ("\\\\d" or "\\d" written with two backslashes),
    collapse every pair of backslashes to a single backslash before emitting.
    The downstream parser feeds this string straight to Python's re.compile -
    "\\\\d" compiles to a literal backslash followed by "d" and matches
    nothing, silently dropping every transaction row. Single backslashes are
    the ONLY correct emission.
  - header_top_pdf / band_top_pdf: use a single number when the detection
    agent used a scalar, or a 2-element list [page1, page2] when it used one.
  - columns_excel: 4 names for the combined Debit/Credit case, 5 names for the
    separate Debit + Credit case, in the exact order
    [transaction date, transaction details, Total/Sum, amount column(s)].
    The Total/Sum entry is the CONTINUOUS RUNNING TOTAL column of the debit and
    credit amounts (the balance after each row, accumulated from an opening
    balance) — e.g. "Cumulative Balance (LC)", "Running Balance", "Total",
    "Sum", "Balance", "Closing Balance". It is NOT a per-row debit/credit
    amount column. Never invent a name — every entry must be an exact column
    the detection agent found in the file.
  - opening_balance_pdf: the Opening Balance figure, or `null` when the
    detection agent omitted it.
  - COLUMN ROLES (carry them through verbatim): the detection agent names the
    role columns exactly as they appear in columns_pdf. Emit them as JSON
    strings, or `null` for the unused amount form:
      * pdf_transaction_date_column, pdf_details_column (required)
      * amount form: EITHER pdf_debit_column + pdf_credit_column (separate)
        OR pdf_debit_credit_combined_column (combined); the unused form is
        `null`. Never invent a value that is not in the detection agent's
        final output.
      * pdf_balance_column: the running balance column, or `null`.

Do NOT invent values. If a value is genuinely absent from the detection agent's
final output, use a sensible default (empty list for lists, null for the
opening balance and for any unused column role) rather than guessing. The block
IS your entire response.
"""


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_output_agent() -> Agent:
    """Build the final-output formatter agent.

    This second agent consumes the first agent's raw final response and
    re-emits the canonical structure as a strict `~~~ [output] ~~~` block,
    which the deterministic `parse_output_block` parser then consumes. This
    keeps the parser's exact contract while removing the risk that the
    structure-detection agent's raw output (which may be missing the fence or
    embed values in prose) fails parsing.
    """
    return Agent(
        name="Final output formatter",
        instructions=OUTPUT_AGENT_INSTRUCTIONS,
        model=_build_model(),
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def detect_structure(
    pdf_path: Path,
    excel_path: Path,
    sheet_name: str = "Sheet1",
    max_attempts: int = MAX_DETECTION_ATTEMPTS,
    max_guardrail_retries: int = MAX_GUARDRAIL_RETRIES,
    request_id: Optional[str] = None,
    reconciliation_type: str = "bank",
) -> FileStructureOutput:
    """Run the agent and return the parsed structure, retrying on failure.

    Two independent retry loops:
      1. LLM-failure retries (inner): the main agent run or the output
         formatter raises (model error, malformed block). Retried up to
         max_attempts (FR-008, default 3).
      2. Guardrail retries (outer): the output guardrail trips when the
         agent's final structure FAILED the assess_structure tool verdict.
         The full conversation history + the failure verdict is fed back and
         the main agent re-runs, up to max_guardrail_retries (default 3).

    On guardrail tripwire, the output-formatter path is NEVER reached (a
    failed output is never passed downstream - it is re-worked instead).

    Args:
        pdf_path: Saved uploaded PDF path.
        excel_path: Saved uploaded Excel path.
        sheet_name: Excel sheet the agent should inspect (default "Sheet1").
        max_attempts: Max LLM-failure retries (FR-008, default 3).
        max_guardrail_retries: Max times the output guardrail may trip before
            giving up (default 3).
        request_id: If provided, the run is registered in the processing
            cancellation registry so the client can halt it mid-run; a cancel
            request stops the current LLM turn immediately via
            RunResultStreaming.cancel().
        reconciliation_type: "bank" (default) or "vendor" - which books the
            statement belongs to; becomes the default the agent starts from
            when calling assess_structure (FR-006).

    Returns:
        Parsed FileStructureOutput.

    Raises:
        AIDetectionError: After all attempts fail (FR-009), or when the
            run was cancelled by the client (CancelledError). The .reason
            distinguishes "guardrail_failed" from "llm_failed".
    """
    from src.services.processing_cancellation import (
        is_cancelled,
        register_run,
        unregister_run,
        update_cancel_handle,
    )

    _configure_tracing()
    last_error: Optional[Exception] = None
    last_tripwire: Optional[OutputGuardrailTripwireTriggered] = None
    # The stream that tripped the guardrail - carries to_input_list() with the
    # full conversation history for the retry.
    last_stream = None
    # Shared dict: the assess_structure tool records its last verdict here;
    # the output guardrail reads it (its ONLY input is the tool's pass/fail).
    verdict_holder: dict = {}

    if request_id:
        register_run(request_id)

    try:
        for guardrail_attempt in range(max_guardrail_retries + 1):
            for attempt in range(1, max_attempts + 1):
                if request_id and is_cancelled(request_id):
                    raise asyncio.CancelledError("Processing cancelled by user")

                logger.info(
                    "AI structure detection guardrail attempt %d/%d, llm attempt %d/%d",
                    guardrail_attempt + 1,
                    max_guardrail_retries + 1,
                    attempt,
                    max_attempts,
                )
                agent = build_agent(
                    pdf_path,
                    excel_path,
                    sheet_name,
                    request_id=request_id,
                    reconciliation_type=reconciliation_type,
                    verdict_holder=verdict_holder,
                )

                try:
                    # run_streamed returns the stream immediately (not a coroutine);
                    # the actual LLM work happens while consuming stream_events().
                    if guardrail_attempt == 0 and attempt == 1:
                        prompt = (
                            "Return me details of both the pdf and the excel file in the "
                            "output format of ~~~[Output]~~~ described. "
                            f'The reconciliation is for "{reconciliation_type.capitalize()}"'
                        )
                        run_input: Any = prompt
                    else:
                        # Guardrail tripwire or LLM-failure retry: continue from
                        # the full conversation history + failure feedback.
                        history = []
                        if last_stream is not None:
                            # Full conversation history from the run that
                            # tripped the guardrail.
                            history = last_stream.to_input_list()
                        run_input = history + [
                            {
                                "role": "user",
                                "content": _build_guardrail_feedback(last_tripwire),
                            }
                        ]

                    stream = Runner.run_streamed(
                        agent,
                        run_input,
                        max_turns=25,
                    )
                    # Expose the live cancel handle to the registry so a cancel
                    # request can halt the current LLM turn immediately.
                    if request_id:
                        update_cancel_handle(request_id, stream.cancel)

                    # Consume the stream to completion (final_output becomes
                    # available only after the stream finishes). Output
                    # guardrails run at the end; a tripwire raises
                    # OutputGuardrailTripwireTriggered here.
                    async for _event in stream.stream_events():
                        if request_id and is_cancelled(request_id):
                            stream.cancel()
                            raise asyncio.CancelledError("Processing cancelled by user")

                    final_output = stream.final_output or ""
                except asyncio.CancelledError:
                    raise
                except OutputGuardrailTripwireTriggered as tw:
                    # The guardrail tripped: the agent's final structure did
                    # not pass the assess_structure tool verdict. Keep the
                    # streaming result (it carries to_input_list() for the full
                    # conversation history) so the next guardrail attempt can
                    # feed it back. Never pass a failed output to the formatter.
                    last_tripwire = tw
                    last_stream = stream
                    last_error = tw
                    logger.warning(
                        "Output guardrail tripwire on guardrail attempt %d: %s",
                        guardrail_attempt + 1,
                        (tw.guardrail_result.output.output_info or {}).get("verdict", tw),
                    )
                    break
                except Exception as e:
                    # If the user cancelled, don't treat the aborted stream as a
                    # retryable failure — surface it as cancellation so the route
                    # returns 499 instead of a generic 422.
                    if request_id and is_cancelled(request_id):
                        logger.info("Run %s cancelled during streaming, aborting", request_id)
                        raise asyncio.CancelledError("Processing cancelled by user") from e
                    # LLM-failure retry: keep the stream so the next attempt
                    # can continue from the full conversation history (the
                    # agent's last message + all prior tool calls/outputs).
                    last_stream = stream
                    last_error = e
                    logger.warning("AI structure detection attempt %d failed: %s", attempt, e)
                    continue

                try:
                    # Second agent: consume the detection agent's raw final response
                    # and re-emit the canonical structure as a strict ~~~ [output] ~~~
                    # block, which parse_output_block then consumes. Uses a normal
                    # Runner.run (no stream). Only reached when the guardrail did
                    # NOT trip (the output is validated).
                    output_agent = build_output_agent()
                    result = await Runner.run(
                        output_agent,
                        (
                            "Here is the structure-detection agent's final response. "
                            "Re-emit the canonical final structure in the required "
                            "~~~ [output] ~~~ block format:\n\n"
                            + final_output
                        ),
                        max_turns=5,
                    )
                    parsed = parse_output_block(result.final_output or "")
                    return parsed
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # The output agent failed (model error, malformed block) — a
                    # genuine retryable failure.
                    last_error = e
                    logger.warning(
                        "AI structure detection attempt %d failed to format output: %s",
                        attempt,
                        e,
                    )
                    continue

            if last_tripwire is None:
                # All LLM-failure retries exhausted with no guardrail tripwire.
                break
            # Guardrail tripwire: reset the LLM-failure retry counter for the
            # next guardrail attempt (fresh inner loop).
            if guardrail_attempt >= max_guardrail_retries:
                break
    finally:
        if request_id:
            unregister_run(request_id)

    if last_tripwire is not None:
        # Guardrail retries exhausted - the agent never produced a structure
        # that passed the assess_structure tool.
        raise AIDetectionError(
            message=AGENT_FAILED_MESSAGE,
            retries_used=max_attempts,
            reason="guardrail_failed",
        ) from last_error
    raise AIDetectionError(
        message=AGENT_INTERNAL_ERROR_MESSAGE,
        retries_used=max_attempts,
        reason="llm_failed",
    ) from last_error


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_guardrail_feedback(tripwire: Optional[OutputGuardrailTripwireTriggered]) -> str:
    """Build the user-message fed back to the main agent on retry.

    Two cases:
      - tripwire set: the guardrail rejected the structure; include the
        assessor verdict + ask to fix and re-validate.
      - tripwire None: a plain LLM/server failure; tell the agent the server
        had an issue and to CONTINUE from where it left off (the full history
        is included in the input).
    """
    if tripwire is None:
        return (
            "The model server had an issue completing your previous turn, so "
            "the conversation was interrupted. Here is the full conversation "
            "history including your last message. CONTINUE from where you left "
            "off: finish your structure investigation, call assess_structure "
            "until it returns overall_pass: true, then emit the [output] block."
        )
    verdict = (tripwire.guardrail_result.output.output_info or {}).get("verdict")
    return (
        "The output guardrail rejected your previous structure. "
        + (verdict or "It failed the assess_structure tool validation.")
        + "\nPlease re-run assess_structure with a fixed structure until "
        "overall_pass is true, then re-emit the [output] block."
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _configure_tracing() -> None:
    """Enable OpenAI Agents SDK tracing with the configured API key.

    Tracing is ON by default (matches the prototype's intent). When
    AI_TRACING_API_KEY is set in the environment, it is used to export traces;
    otherwise the SDK falls back to OPENAI_API_KEY / its own default.
    """
    set_tracing_disabled(False)
    if settings.AI_TRACING_API_KEY:
        set_tracing_export_api_key(settings.AI_TRACING_API_KEY)
        logger.info("OpenAI Agents SDK tracing enabled with AI_TRACING_API_KEY")
    else:
        logger.info("OpenAI Agents SDK tracing enabled (using default/OPENAI_API_KEY)")


# NOTE: _validate_detected_structure is intentionally NOT called from
# detect_structure(). The agent's assess_structure tool is the only structural
# gate (matching test.py); this deterministic cross-check is kept in the module
# for reference/re-enablement but must not reject agent output pre-extraction.
def _validate_detected_structure(
    parsed: FileStructureOutput,
    excel_path: Path,
    sheet_name: str,
) -> None:
    """Deterministic cross-checks on the detected structure (FR-008 retry trigger)."""
    if not parsed.columns_pdf:
        raise AIDetectionError("columns_pdf is empty")
    if len(parsed.columns_excel) not in (4, 5):
        raise AIDetectionError(
            f"columns_excel must contain 4 columns (combined Debit/Credit) or 5 columns "
            f"(separate Debit + Credit), got {len(parsed.columns_excel)}"
        )
    if len(parsed.column_boundaries_pdf) != len(parsed.columns_pdf) - 1:
        raise AIDetectionError(
            f"column_boundaries_pdf must have len(columns_pdf)-1={len(parsed.columns_pdf)-1} values, "
            f"got {len(parsed.column_boundaries_pdf)}"
        )
    if any(b1 >= b2 for b1, b2 in zip(parsed.column_boundaries_pdf, parsed.column_boundaries_pdf[1:])):
        raise AIDetectionError("column_boundaries_pdf must be strictly ascending")

    # Verify the detected Excel columns actually exist in the sheet (read header row).
    try:
        df = pd.read_excel(excel_path, header=None, sheet_name=sheet_name)
        header_row = df.iloc[0].astype(str).tolist() if not df.empty else []
    except Exception as e:
        raise AIDetectionError(f"Could not read Excel sheet '{sheet_name}': {e}")

    normalized_header = [str(h).strip() for h in header_row if str(h).strip()]
    for col in parsed.columns_excel:
        if col not in normalized_header:
            raise AIDetectionError(f"Detected Excel column '{col}' not found in header row")


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
