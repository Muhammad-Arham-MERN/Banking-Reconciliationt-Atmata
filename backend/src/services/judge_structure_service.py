# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Judge Structure by its Cover service.

A small nested agent (OpenAI Agents SDK agents-as-tools pattern) exposed to the
main structure-detection agent as a tool. It reads the first ~10 visual text
lines of the uploaded PDF's page 1, identifies the bank/vendor, and looks up
whether that entity's PDF structure is already known in the
pdf_structure_profiles store.

The Judge's final response is returned to the main agent AS A TOOL RESULT - the
orchestrating LLM reads it directly and decides (known structure vs full
detection), so no ~~~ [output] ~~~ block, no parse_output_block variant, and no
decision branches in deterministic code.

Judgment is CONTEXTUAL, not exact-string: the Judge reads the entity list from
lookup_pdf_structures and decides whether the name it read from the PDF is
contextually the same entity as a list entry (e.g. "Askari Bank" vs
"Askar Bank"). When it decides yes, it fetches the full structure using the
EXACT stored name from the list entry, so the store lookup stays deterministic.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pdfplumber
from agents import Agent, Runner
from agents.decorators import tool
from agents.extensions.models.litellm_model import LitellmModel
from agents.tracing import set_tracing_disabled, set_tracing_export_api_key

from src.config import settings
from src.services.pdf_structure_store import (
    get_profile,
    list_profiles,
)

logger = logging.getLogger(__name__)

# Standing convention (taste): every Runner.run* call site carries max_turns=25.
JUDGE_MAX_TURNS = 25

# How many leading visual text lines of page 1 the Judge reads (context-tiny).
JUDGE_FIRST_LINES = 10

# Sentinel strings in the Judge's output contract (section 4.3 of the plan).
KNOWN_ENTITY_PREFIX = "KNOWN_ENTITY"
NO_DATA = "NO_DATA"


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _run_async(coro_factory):
    """Run an async store call from a SYNC tool context.

    The SDK runs sync tools in a worker thread with no running event loop.
    asyncpg connections are bound to the loop they were created on (the app's
    main loop), so we schedule the coroutine onto THAT loop via
    run_on_main_loop and block for the result - never a fresh loop (a new loop
    would raise "Future attached to a different loop"). Fail-open: the caller
    logs and returns the safe default.
    """
    from src.services.db_service import run_on_main_loop

    return run_on_main_loop(coro_factory)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _first_lines_text(pdf_path: Path, lines: int = JUDGE_FIRST_LINES) -> str:
    """Return the first ~N visual text lines of page 1 as plain readable text.

    Plain text only - NO word geometry (x0/x1/top). The Judge only needs to
    READ a bank/vendor name from the statement header / letterhead, not locate
    columns (same principle as the Ihsan closing-balance reader).
    """
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            if not pdf.pages:
                return "No pages found in the PDF."
            page = pdf.pages[0]
            words = page.extract_words()
            if not words:
                return "No text found on page 1."
            # Group words into visual lines by their top coordinate (rounded
            # to 0.1 like the other tools), ordered top-to-bottom.
            visual_lines: Dict[float, list] = {}
            for w in words:
                visual_lines.setdefault(round(w["top"], 1), []).append(w)
            rendered = []
            for top in sorted(visual_lines)[:lines]:
                row_words = sorted(visual_lines[top], key=lambda w: w["x0"])
                rendered.append(" ".join(w["text"] for w in row_words))
            return "\n".join(rendered)
    except Exception as e:
        logger.warning("read_pdf_first_lines failed (fail-open): %s", e)
        return "Could not read the PDF."


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
JUDGE_INSTRUCTIONS = """You are "Judge Structure by its Cover", the first stop for every uploaded PDF in a Banking Reconciliation System.

Your ONLY job: identify whose PDF this is, and whether the system already knows its structure.

This is a "<type>" statement (type = bank | vendor - passed to you).

Steps:
1. Call read_pdf_first_lines (page 1's first ~10 lines) and read the bank/vendor name from the statement header / letterhead.
2. If the PDF carries NO identifiable name (some vendor PDFs and Banks have none), do NOT guess. Stop and answer "NO_DATA".
3. Call lookup_pdf_structures with NO argument to see the known entities.
4. If the entity you identified is in that list, call lookup_pdf_structures with the entity name to fetch its full stored structure, and return it.
5. If the entity is NOT in the list (or you are unsure), answer "NO_DATA".

MATCHING IS CONTEXTUAL, NOT LITERAL: the known-entities list and the name you read from the PDF may differ in spelling, punctuation, or wording (e.g. "Askari Bank" vs "Askar Bank", "Meezan Bank Ltd." vs "Meezan Bank", "Faisal Cement" vs "Faisal Cement Co."). Decide by CONTEXTUAL RELEVANCE - is this list entry clearly the same bank/vendor as the PDF's? When you decide yes, fetch the full structure using the EXACT stored name as it appears in the list (lookup_pdf_structures takes the stored name), NOT the spelling you read from the PDF.

OUTPUT RULES:
- KNOWN: return the full structure JSON exactly as lookup_pdf_structures returned it, prefixed with "KNOWN_ENTITY <stored name>:".
- UNKNOWN/UNIDENTIFIABLE: return exactly "NO_DATA" followed by a one-line reason.
- Nothing before/after. No prose."""


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_judge_agent(
    pdf_path: Path,
    reconciliation_type: str = "bank",
    request_id: Optional[str] = None,
) -> Agent:
    """Build the Judge agent bound to the uploaded PDF.

    The Judge gets exactly 2 tools:
      - read_pdf_first_lines: plain readable first ~10 lines of page 1.
      - lookup_pdf_structures: the known-entities catalog (no arg) or the full
        stored structure for one entity (entity_name arg).

    Same model family + tracing as the existing AI flows (taste), and
    max_turns=25 (standing convention). The nested run carries request_id so a
    client Stop halts the Judge mid-run.
    """

    @tool
    def read_pdf_first_lines(drop: int = 0, lines: int = JUDGE_FIRST_LINES) -> str:
        """Read the first ~10 visual TEXT LINES of page 1 of the uploaded PDF as plain readable text.

        This shows the statement header / letterhead where the bank or vendor
        name is printed. Plain text only - no coordinates. Use this to
        identify whose PDF this is.

        Args:
            drop: How many initial visual lines to skip (default 0).
            lines: How many visual lines to show (default 10).
        """
        if drop > 0:
            # Paging support (taste): re-read and skip the already-shown lines.
            try:
                with pdfplumber.open(str(pdf_path)) as pdf:
                    if not pdf.pages:
                        return "No pages found in the PDF."
                    words = pdf.pages[0].extract_words()
                    if not words:
                        return "No text found on page 1."
                    visual_lines: Dict[float, list] = {}
                    for w in words:
                        visual_lines.setdefault(round(w["top"], 1), []).append(w)
                    rendered = []
                    for top in sorted(visual_lines)[drop : drop + lines]:
                        row_words = sorted(visual_lines[top], key=lambda w: w["x0"])
                        rendered.append(" ".join(w["text"] for w in row_words))
                    return "\n".join(rendered) or "No more lines."
            except Exception as e:
                logger.warning("read_pdf_first_lines failed (fail-open): %s", e)
                return "Could not read the PDF."
        return _first_lines_text(pdf_path, lines)

    @tool
    def lookup_pdf_structures(entity_name: Optional[str] = None) -> str:
        """Look up the known PDF structures in the store.

        Two modes:
          - NO argument: returns the COMPACT list of known entities, one per
            line as "name (type)" - e.g. "Askari Bank (bank), Meezan Bank
            (bank), Faisal Cement (vendor)". Use this to see what the system
            already knows.
          - WITH entity_name: returns the FULL stored structure for that entity
            as JSON, or "No profile found for <name>." when absent. Pass the
            EXACT stored name as it appears in the compact list.

        Args:
            entity_name: The entity's stored name (as shown in the compact
                list), or None to list all known entities.
        """
        try:
            if entity_name:
                profile = _run_async(
                    lambda: get_profile(entity_name, reconciliation_type)
                )
                if profile is None:
                    return f"No profile found for {entity_name}."
                return json.dumps(profile.get("structure", {}), default=str)
            profiles = _run_async(
                lambda: list_profiles(reconciliation_type)
            )
            if not profiles:
                return "No known entities yet."
            return ", ".join(
                f"{p['entity_name']} ({p['entity_type']})" for p in profiles
            )
        except Exception as e:
            logger.warning("lookup_pdf_structures failed (fail-open): %s", e)
            return "No known entities yet."

    return Agent(
        name="Judge Structure by its Cover",
        instructions=JUDGE_INSTRUCTIONS.replace(
            "<type>", reconciliation_type
        ),
        model=_build_model(),
        tools=[read_pdf_first_lines, lookup_pdf_structures],
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_judge_tool(
    pdf_path: Path,
    reconciliation_type: str = "bank",
    request_id: Optional[str] = None,
):
    """Build the Judge as an agent-as-tool for the main extraction agent.

    Registered as tool_name "judge_structure_by_cover" on the main agent. The
    main agent calls it FIRST, reads its verdict directly as a tool result, and
    either re-validates the known structure with assess_structure (Path A) or
    falls back to full detection (Path B). Fail-open: if the nested run raises,
    the SDK returns the error as the tool result and AGENT_INSTRUCTIONS tell the
    main agent to proceed with full detection.
    """
    judge_agent = build_judge_agent(
        pdf_path,
        reconciliation_type=reconciliation_type,
        request_id=request_id,
    )
    return judge_agent.as_tool(
        tool_name="judge_structure_by_cover",
        tool_description=(
            "CALL THIS FIRST, before any file inspection. Reads whose PDF this "
            "is from its first lines and checks whether the system already "
            "knows that bank/vendor's PDF structure. Returns either "
            "'KNOWN_ENTITY <name>:' followed by the full stored structure JSON "
            "(re-validate it against THIS file with assess_structure), or "
            "'NO_DATA' (unknown/new entity - detect the structure from scratch)."
        ),
        max_turns=JUDGE_MAX_TURNS,
    )


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_model() -> LitellmModel:
    """Build the LiteLLM model from settings (model + API key), never hardcoding
    credentials. Mirrors ai_structure_detector._build_model()."""
    model_id = settings.AI_MODEL or "gemini/gemini-2.0-flash"
    api_key = settings.AI_API_KEY or ""
    if settings.AI_MODEL or settings.AI_API_KEY:
        return LitellmModel(model=model_id, api_key=api_key)
    # No env config: let the provider pick up its own env var (e.g. GOOGLE_API_KEY)
    return LitellmModel(model=model_id)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _configure_tracing() -> None:
    """Enable OpenAI Agents SDK tracing with the configured API key (taste)."""
    set_tracing_disabled(False)
    if settings.AI_TRACING_API_KEY:
        set_tracing_export_api_key(settings.AI_TRACING_API_KEY)
        logger.info("OpenAI Agents SDK tracing enabled with AI_TRACING_API_KEY")
    else:
        logger.info("OpenAI Agents SDK tracing enabled (using default/OPENAI_API_KEY)")


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
