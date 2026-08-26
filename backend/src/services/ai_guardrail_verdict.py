# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
AI Guardrail Verdict Layer (Kifalat e Natija)

Runs a small structured LLM verdict on the structure-detection agent's final
output, as the second opinion of the output guardrail loop. The primary gate
is the deterministic assessor (Saghir/Kabir/Ihsan via assess_pdf_structure);
this module adds an optional LLM layer that can catch structural problems the
deterministic checks cannot express (e.g. a column-boundary that cuts a data
column, an implausible date pattern, or a header list that does not match the
extracted columns).

Design rules:
- FAIL-OPEN: when the guardrail model/key is not configured, or the call
  errors, the verdict layer is SKIPPED - the deterministic assessor alone
  decides. A verdict-layer failure must never fail the run.
- FAIL-SAFE BIAS (mirrors the Kabir adjudicator): a false PASS = silent data
  loss; a false FAIL = one extra agent retry. When unsure, flag for retry.
"""

import json
import logging

logger = logging.getLogger(__name__)


class GuardrailVerdict:
    """Structured verdict from the guardrail LLM layer."""

    __slots__ = ("passed", "issues", "suggestions", "raw", "skipped")

    def __init__(
        self,
        passed: bool = True,
        issues: list = None,
        suggestions: list = None,
        raw: str = "",
        skipped: bool = False,
    ):
        self.passed = passed
        self.issues = issues or []
        self.suggestions = suggestions or []
        self.raw = raw
        self.skipped = skipped

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "skipped": self.skipped,
        }


def _verdict_instructions() -> str:
    """Instructions for the guardrail LLM verdict (fail-safe bias)."""
    return """
You are the Kifalat e Natija (guarantor of the result) judge for a Banking
Reconciliation System. You receive the structure-detection agent's final
extracted structure (columns, header words, band/header geometry, date
pattern, opening balance) together with the deterministic assessor's verdict.

Your ONLY job: judge whether the agent's structure is PLAUSIBLE and
SELF-CONSISTENT enough to feed the deterministic PDF extractor, and return a
structured verdict.

Judge the digest only. Rules:
- PASS only if the structure is internally consistent: the header words match
  the columns, the column boundaries look plausible for the stated columns,
  the date pattern is a valid regex matching common statement dates, and the
  assessor verdict does not contradict it.
- FAIL on any clear inconsistency: a date pattern that cannot match real
  dates, column boundaries that would cut a stated column, a header list that
  cannot be reconciled with the columns, or an assessor verdict flagging
  arithmetic/completeness problems the agent ignored.
- Cost asymmetry is explicit: a false PASS = silent data loss; a false FAIL =
  one extra agent iteration. When unsure, FAIL and say why.

Output ONLY a JSON object, nothing else:
{"passed": true|false, "issues": ["one concrete issue per entry"],
 "suggestions": ["one actionable fix per issue"]}
""".strip()


def _build_verdict_model():
    """Build the LiteLLM model for the guardrail verdict layer, or None when
    the guardrail model/key is not configured (fail-open)."""
    from src.config import settings

    model_id = (settings.AI_GUARDRAIL_MODEL or "").strip()
    api_key = (settings.AI_GUARDRAIL_API_KEY or "").strip()
    base_url = (settings.AI_GUARDRAIL_BASE_URL or "").strip()

    if not model_id or not api_key:
        logger.info(
            "Guardrail verdict layer skipped: AI_GUARDRAIL_MODEL/AI_GUARDRAIL_API_KEY not configured"
        )
        return None

    from agents.extensions.models.litellm_model import LitellmModel

    kwargs = {"model": model_id, "api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return LitellmModel(**kwargs)


def _parse_verdict(raw: str) -> GuardrailVerdict:
    """Parse the LLM's JSON verdict; unparseable → fail-safe FAIL."""
    out = (raw or "").strip()
    # Strip markdown fences if the model wrapped the JSON.
    if out.startswith("```"):
        out = out.strip("`")
        if out.startswith("json"):
            out = out[4:]
        out = out.strip()
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return GuardrailVerdict(
            passed=False,
            issues=["Guardrail verdict model returned an unparseable response."],
            suggestions=["Re-run the structure detection agent and re-validate."],
            raw=out[:300],
        )
    passed = bool(data.get("passed", False)) if "passed" in data else False
    issues = data.get("issues") or []
    suggestions = data.get("suggestions") or []
    return GuardrailVerdict(
        passed=passed,
        issues=[str(i) for i in issues],
        suggestions=[str(s) for s in suggestions],
        raw=raw,
    )


def assess_agent_output(
    output_text: str,
    assessment: dict,
) -> GuardrailVerdict:
    """Run the optional LLM verdict layer on the agent's final output.

    Fail-open: when the guardrail model/key is unconfigured or the call
    errors, returns a skipped verdict (the assess_structure tool verdict
    alone decides).

    Args:
        output_text: The agent's raw final output text.
        assessment: The assess_structure tool verdict dict (the assessment
            the agent already received in-conversation).
    """
    model = _build_verdict_model()
    if model is None:
        return GuardrailVerdict(skipped=True)

    from agents import Agent, Runner

    judge = Agent(
        name="Guardrail verdict judge",
        instructions=_verdict_instructions(),
        model=model,
    )

    packet = {
        "assessor_verdict": {
            "overall_pass": assessment.get("overall_pass"),
            "saghir": (assessment.get("cumulative_check") or {}).get("passed"),
            "kabir": (assessment.get("kabir_check") or {}).get("passed"),
            "ihsan": (assessment.get("ihsan_check") or {}).get("passed"),
            "issues": assessment.get("issues", []),
            "suggestions": assessment.get("suggestions", []),
        },
    }

    try:
        result = Runner.run_sync(
            judge,
            "Structure-detection agent final output:\n"
            + (output_text[:4000] or "")
            + "\n\nAssessor verdict:\n"
            + json.dumps(packet, indent=2, default=str),
            max_turns=10,
        )
        return _parse_verdict(result.final_output or "")
    except Exception as e:
        logger.warning("Guardrail verdict layer failed (%s); skipping (fail-open)", e)
        return GuardrailVerdict(skipped=True)


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
