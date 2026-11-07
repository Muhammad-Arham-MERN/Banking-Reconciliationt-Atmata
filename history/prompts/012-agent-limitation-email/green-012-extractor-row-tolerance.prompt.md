---
id: green-012-extractor-row-tolerance
title: extractor-row-tolerance-and-email-fix
stage: green
date: 2026-11-07
surface: cli
model: claude-sonnet-4-5
feature: 012-agent-limitation-email
branch: 012-agent-limitation-email
user: developer
command: follow-up fix
labels: [fix, pdf-extraction, row-clustering, tolerance, resend, email, agent-report]
links:
  spec: specs/012-agent-limitation-email/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/utils/layout_rows.py
  - backend/src/services/ai_pdf_processor.py
  - backend/src/services/pdf_processor.py
  - backend/src/utils/structure_assessor.py
  - backend/src/config.py
  - backend/src/services/notification_service.py
  - backend/.env.example
  - backend/.env
  - specs/012-agent-limitation-email/spec.md
  - specs/012-agent-limitation-email/contracts/agent-tool-contract.md
  - specs/012-agent-limitation-email/data-model.md
tests:
  - py_compile on all edited backend files (PASS)
  - import smoke of layout_rows/ai_pdf_processor/pdf_processor/structure_assessor/ai_routes (PASS)
  - stub-PDF extract_pdf test: jittered row keeps Debit/Credit (PASS)
  - group_words_into_lines unit check: 0.1pt jitter merges to 1 line (PASS)
---

## Prompt

please change the email to "arhambrowser@gmail.com" ArhamBrowser@gmail.com is problematic, change it complete,y and secondly when agent calls the tool the tool for tool limitation error, the processin should stop, currently the agent report the tool limitation but due to guard and keeps on looping agent again and again, it is like agent has broken tools, it is saying i cant work with this i am sorry and my guardrail agent is continiuosuly slapping it again and again to solve the issue without tools

(followed by) fix this issue from our agent arrived Reconciliation Atmata - tool limitation report … [the agent's email reporting that row clustering uses exact line 'top' equality, so words jittered by ~0.1pt vertically split one logical table row and its amount/balance cells are dropped; proposed adding a vertical tolerance / row_tolerance_pdf to the extractor used by assess_structure]

## Response snapshot

Three fixes on branch 012-agent-limitation-email.

1) Recipient address: changed to lowercase `arhambrowser@gmail.com` everywhere — config.py (both `COMPANY_REQUEST_NOTIFY_EMAIL` and `AGENT_LIMITATION_NOTIFY_EMAIL` defaults), notification_service.DEFAULT_RECIPIENT, backend/.env.example, and the live backend/.env (added the two AGENT_LIMITATION_* keys; company one was already lowercase). Aligned the 012 spec/plan/tasks/research/data-model/contracts/quickstart references (left PHR transcripts verbatim).

2) Stop the run when the agent reports a limitation: the tool is now `@tool(failure_error_function=None)` and RAISES a new `ToolLimitationReported` after recording + best-effort emailing. Verified against the installed SDK (agents 0.22.0) that `failure_error_function=None` disables the failure formatter so the exception propagates (`if result is None: raise` in tool_execution.py). `detect_structure` catches it outside both retry loops (`except ToolLimitationReported: raise` inside the streaming try; a holder check in the `except Exception` retry path for safety) and converts it to `AIDetectionError(reason="technical_limitation")`; the route's existing holder-based classification then returns the blue notice. Result: no LLM retries and no guardrail re-run once the agent declares its tools insufficient.

3) The agent-reported extraction bug: added `backend/src/utils/layout_rows.py` with `group_words_into_lines(words, tolerance=ROW_TOP_TOLERANCE_PDF=1.0)` — clusters words whose top is within 1.0pt into one logical row. Replaced every exact-`round(top,1)` row-grouping site with it: `ai_pdf_processor.extract_pdf` (production AI extractor), `structure_assessor.extract_pdf_words` + `_extract_rows_per_page` + the per-page bucketing + the Kabir raw-dated-row counter, and the legacy `pdf_processor._extract_rows_via_layout` (`/karwai`). Both extractors and the assessor now share one helper so they always measure the same rows. (Also fixed a dangling `len(lines)` → `len(page_lines)` introduced by the refactor.)

Verification: py_compile + imports pass; a stub-PDF test through `extract_pdf` shows a row whose amount cells sit +0.1pt below its date/details now extracts with Debit=51,122.00 and Credit=1,120,876.32 (previously dropped); the cluster helper merges the 0.1pt-jittered words into one line.

## Outcome

- ✅ Impact: The agent's reported extraction limitation is fixed (baseline-jittered rows no longer drop amount cells); the limitation tool now hard-stops the run instead of looping the guardrail; the notification recipient is the lowercase address.
- 🧪 Tests: No automated tests (standing instruction). Ran py_compile (PASS), imports (PASS), stub-PDF extract_pdf jitter test (PASS), cluster helper check (PASS).
- 📁 Files: layout_rows.py (new) + ai_pdf_processor.py, pdf_processor.py, structure_assessor.py, config.py, notification_service.py, .env.example, .env, and 3 spec docs.
- 🔁 Next prompts: re-run the live statement that failed; consider exposing `row_tolerance_pdf` as an agent structure parameter (the agent's "ideally"); commit.
- 🧠 Reflection: The agent's own report was precise enough to act on directly — the fix is a 1.0pt merge window in one shared helper reused by every row-assembly site, which also guarantees the assessor and the pipeline can't disagree. Keeping the tolerance a code constant (not an LLM parameter yet) keeps the change safe while fully resolving the reported symptom; exposing it to the agent is a clean follow-up.

## Evaluation notes (flywheel)

- Failure modes observed: a refactor slip — replacing the grouping in `assess_pdf_structure` left `"in_band_lines": len(lines)` referencing a now-renamed variable; caught by grepping for `\blines\b` after the edits and fixed. Also note the earlier failed `py_compile` call used repo-relative paths while cwd was `backend/` — corrected to `src\...`.
- Graders run and results (PASS/FAIL): py_compile PASS; imports PASS; stub-PDF extract_pdf jitter test PASS; cluster helper check PASS (3 lines without tolerance → 2 with).
- Prompt variant (if applicable): fix-v1
- Next experiment (smallest change to try): expose `row_tolerance_pdf` end-to-end (FileStructureOutput → assess_structure tool arg → extractors) with a clamp, so unusual layouts can tune the merge window.
