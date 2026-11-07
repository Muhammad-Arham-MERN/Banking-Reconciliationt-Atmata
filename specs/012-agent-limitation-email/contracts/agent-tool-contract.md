# Contract: `report_tool_limitation` agent tool + limitation email

**Feature**: `012-agent-limitation-email` | **Plan**: [../plan.md](../plan.md) | **Spec**: [../spec.md](../spec.md)

This contract defines the surface the extraction agent uses to report a tool/engine limitation,
and the email the report becomes. It is the implementable form of FR-001…FR-009 and
FR-015/FR-016.

---

## 1. Tool definition

Added to `build_agent_tools(...)` in `backend/src/services/ai_structure_detector.py` (the same
place the other five tools are created) and returned in that list, so the detection agent sees it
as a first-class tool.

```python
@tool(failure_error_function=None)   # None => the SDK does NOT absorb the raise
def report_tool_limitation(
    tool_name: str,
    issue: str,
    details: str,
    example: str,
    analogy: str,
    proposed_solution: str,
    reason: str,
) -> str:
    """Email the developer when a failure is caused by a limitation or defect of your
    own tools/engine, or when you are confident a NEW tool is needed.

    Use this ONLY for genuine tool/engine limitations — never for ordinary failures such
    as malformed/unsupported input files, ordinary data mismatches, or user error.

    Provide an ANONYMISED / STRUCTURAL example (column names, layout, the nature of the
    failure) — never raw transaction rows, account numbers, or balances. Never include
    credentials, API keys, or tokens.

    Args:
        tool_name: The tool the limitation concerns, or "engine" if it is the pipeline
            itself. One of: judge_structure_by_cover, read_excel, read_pdf,
            read_pdf_words, assess_structure, engine.
        issue: One-line description of the problem/limitation.
        details: What you attempted, where it failed, and the observed error.
        example: A concrete, anonymised/structural example of the problem.
        analogy: A plain-language analogy that explains the issue.
        proposed_solution: The tool upgrade or new tool you believe is needed.
        reason: Why that upgrade/new tool is needed, tied to `tool_name`.

    Returns:
        This tool does NOT return: once called, it STOPS the whole run immediately —
        no retries and no guardrail re-loop — because you have declared your own
        tools/engine insufficient. It records the report, emails it to the developer
        best-effort, then aborts.
    """
```

### Derived tool schema (what the model sees)

| Parameter | Type | Required | Constraint |
|-----------|------|----------|------------|
| `tool_name` | string | Yes | one of the five tool names or `engine` |
| `issue` | string | Yes | non-empty |
| `details` | string | Yes | non-empty |
| `example` | string | Yes | non-empty; anonymised/structural |
| `analogy` | string | Yes | non-empty |
| `proposed_solution` | string | Yes | non-empty |
| `reason` | string | Yes | non-empty; must reference `tool_name` |

### Behaviour — calling this tool ABORTS the run

1. **Stop, don't loop**: the tool raises `ToolLimitationReported`. Because it is registered
   with `failure_error_function=None`, the OpenAI Agents SDK does **not** absorb the raise — it
   propagates out of the agent run. `detect_structure` catches it **outside** its retry loops and
   converts it to a terminal `AIDetectionError(reason="technical_limitation")`. There are then
   **no LLM-failure retries and no guardrail re-run** — the guardrail never gets to "slap" the
   agent back into trying again against tools it just declared insufficient.
2. **Record (FR-010)**: set `holder["reported"] = True` and store the report on the holder
   **first**, so the route classifies the failure as a technical limitation.
3. **Live feedback (FR-011)**: emit a neutral stage frame — e.g. key `limitation_reported`,
   message *"A technical limitation was found on our side — our agent has notified the developer."*
   — so the loading overlay reflects it.
4. **Validation (FR-003e, FR-007)**: if any required field is empty, or `reason` does not
   reference the named tool, the email is **not** sent (logged) — but the run is **still stopped**,
   because the agent's intent was "my tools cannot do this".
5. **Send (FR-002, FR-003, FR-005)**: otherwise call
   `notification_service.send_agent_limitation_email(report)` best-effort (a delivery failure is
   logged, never raised). Idempotent: a second call in the same run resends nothing and just stops.
6. **Then raise** `ToolLimitationReported(report)`.

---

## 2. Email contract (`notification_service.send_agent_limitation_email`)

Mirrors the existing `send_company_request_notification` shape (lazy `import resend`,
`asyncio.to_thread`, catch-all, returns `bool`, never raises).

| Header/part | Value |
|-------------|-------|
| `from` | `settings.RESEND_FROM_EMAIL` |
| `to` | `settings.AGENT_LIMITATION_NOTIFY_EMAIL` (default `arhambrowser@gmail.com`) |
| `subject` | `f"{settings.AGENT_LIMITATION_SUBJECT_PREFIX}: {report['tool_name']} limitation"` → **begins with `Reconciliation Atmata`** |

Body layout (plain text — the five required elements plus context):

```text
Reconciliation Atmata — tool limitation report

Tool:    <tool_name>
Run:     <run_id>

ISSUE
<issue>

DETAILS
<details>

EXAMPLE (anonymised)
<example>

ANALOGY
<analogy>

PROPOSED SOLUTION
<proposed_solution>

WHY (reason)
<reason>
```

**Invariants**

- Sends **at most one** email per run (enforced by the holder flag).
- Skips with a logged warning when `RESEND_API_KEY` or `RESEND_FROM_EMAIL` is unset; returns
  `False` and does not raise.
- Contains no secrets and no raw financial rows — it is composed only from the validated report
  fields (FR-015, FR-016).
- The subject always begins with the configured prefix so the Developer's Gmail rule routes it
  to the **Reconciliation Atmata** label (FR-002).

---

## 3. Agent instruction additions (FR-008, FR-009)

`AGENT_INSTRUCTIONS` gains:

1. **Reporting policy** — report via `report_tool_limitation` only when the agent itself
   determines a genuine tool/engine limitation or a needed new tool; never for ordinary
   failures; always report when a failure is caused by a tool/engine limitation.
2. **Tool purpose summary** — a short, purpose-only list (no logic):

   ```text
   YOUR TOOLS (purpose only):
     - judge_structure_by_cover : recall a known bank/vendor's stored structure
     - read_excel                : read rows from the Excel ledger
     - read_pdf                  : read table rows from the PDF statement
     - read_pdf_words            : read word geometry / column positions (first two pages)
     - assess_structure          : score a proposed structure against the statement
     - report_tool_limitation    : email the developer about a tool/engine limitation
   ```

---

## 4. Acceptance checks (manual)

- [ ] Tool appears in the agent's tool list and is invocable.
- [ ] Calling the tool **stops the run at once**: no further LLM retries, no guardrail re-run
      (the agent is never re-prompted to solve it "without tools"); the request ends as a
      technical-limitation failure.
- [ ] Missing `reason`/`tool_name` ⇒ no email sent, but the run is still stopped (blue notice).
- [ ] Second call in the same run ⇒ no second email; the run is still stopped.
- [ ] Valid report ⇒ email with subject beginning `Reconciliation Atmata` to the configured
      inbox, body containing all five elements.
- [ ] Email send throws / key unset ⇒ the run still stops cleanly (logged); nothing crashes.
- [ ] A live stage frame is emitted when the tool runs.
