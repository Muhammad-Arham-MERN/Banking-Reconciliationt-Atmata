# Implementation Plan: AI Reconciler Advisor ("Subh al Baqaya")

**Branch**: `007-ai-reconciler-advisor` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-ai-reconciler-advisor/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

After a reconciliation completes and the final discrepancies list is shown, the user clicks **"Reconcile With Agent"**. A new, auth-protected `/advisor/*` endpoint sends the complete final discrepancies list (each with date, details, signed Debit/Credit, source, a stable backend-generated key) plus cumulative Bank-vs-Company totals/balance context to the Reconciler Agent — a chat-capable model from the same family as the existing AI flows (`openai-agents` SDK + LiteLLM/Gemini), no tools. The agent returns typed structured output (list of suggestions + a chat/text string), analyzing strictly for two cases only: **broken cheques/pairs** (side items whose signed amounts sum to a single opposite-sign item) and **reversals** (near-dated opposite-sign equal-magnitude entries). Suggestions are advisory only — the agent never removes anything. The frontend renders suggestions in a luxurious card panel with a reason tooltip and a **Reconcile** button per suggestion; clicking it removes exactly the suggested items from the live main list (mirroring the existing manual-reconcile `handleReconcile` filter). The user can also ask follow-up questions in a stateless streaming chat that re-sends the CURRENT live discrepancy context plus history, keyed by the reconciliation `request_id`. Any agent failure (malformed/empty output or transport/model) is retried up to 3 attempts, then a friendly error surfaces. A "What we Removed" feature is explicitly out of scope.

## Technical Context

**Language/Version**: Python `>=3.13` (backend); TypeScript `^5` with React `19.2.4` on Next.js `16.2.9` App Router (frontend)
**Primary Dependencies**: FastAPI `>=0.104.1`, `uvicorn[standard]`, `openai-agents[litellm]` (OpenAI Agents SDK + LiteLLM, Gemini family via `settings.AI_MODEL`/`AI_API_KEY`), pydantic `>=2.5.0`, pandas `2.1.4` (backend); shadcn/ui `^4.11.0` (base-nova, `@base-ui/react`), Tailwind CSS `^4.3.3`, `lucide-react`, `next-themes` (frontend)
**Storage**: CockroachDB via raw `asyncpg` (`DatabaseService`, `reconciliation_data` JSONB) for the existing cloud save; the advisor itself is **stateless** — no new persistence (FR-008a). SQLite history layer exists but is not extended.
**Testing**: pytest (backend, existing unit tests under `backend/tests/`); independent feature tests defined in the spec map to pytest scenarios. Frontend verification via Next.js build + manual scenario runs.
**Target Platform**: Web app — local desktop browser (Chrome/Edge) running `next dev` + `uvicorn`; deployment pattern is the existing local FastAPI + Next.js pair.
**Project Type**: Web application (frontend + backend) — `backend/` + `frontend/`.
**Performance Goals**: Suggestions panel renders without degradation on 100+ discrepancies / 400+ items (SC-004); agent response streams token-by-token (FR-008c). No per-request hard latency target beyond existing AI-flow behavior.
**Constraints**: Preserve existing manual and AI reconciliation flows unchanged (FR-012); preserve the debit/credit convention negative=debit / positive=credit and `FROM` source (FR-011); agent strictly two suggestion types (FR-003); stateless server chat (FR-008a); 3-attempt unified retry (FR-006); agent never auto-removes (FR-005); new dedicated endpoint (NOT `/reconcile-ai`), REQUIRING auth (not exempt like `/karwai`).
**Scale/Scope**: Local single-user tool; final discrepancies per reconcile can reach 100+ items / 400+ source transactions; full final discrepancies list always sent in full (no sampling/chunking, key clarification).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **G1 — Strict Instruction Following (Principle I)**: PASS. Spec is precise (FR-001…FR-013, edge cases, clarifications). No improvisation required; all ambiguity already resolved via the two spec clarification sessions (2026-08-25, 2026-08-26).
- **G2 — Developer Stack Authority (Principle II)**: PASS. Reuses the exact existing stack (FastAPI, openai-agents+LiteLLM/Gemini, pydantic, Next.js, shadcn/ui, asyncpg). No new frameworks or libraries proposed; requires no stack deviation.
- **G3 — Supervised Collaboration (Principle III)**: PASS. All proposals (per-item key implementation, totals/balance derivation) are framed and the developer is final authority; nothing is autonomously decided beyond what the spec mandates.
- **G4 — Constructive Objection (Principle IV)**: PASS (no violations). The constraint requiring a stable per-discrepancy key and cumulative totals/balance is a recognized gap in the current code that the spec mandates; flagged explicitly in Phase 1 rather than silently assumed.
- **G5 — Controlled Creativity (Principle V)**: PASS. Novel behavior (broken-cheque/reversal suggestion logic, stateless streaming chat) is driven entirely by explicit spec requirements and the re-used AI SDK — no unapproved creative algorithms.
- **G6 — Ambiguity Resolution (Principle VI)**: PASS. Every open question from the draft spec was resolved in the two clarification sessions, superseded entries marked. No remaining unknowns.
- **G7 — Code Standards (Standards 1–3)**: PASS. Every edited/created file MUST carry the `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` header, `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` footer, and `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٍ` inline crux marker on the core suggestion/reconciliation logic.

**Gate result**: PASS — no unjustified violations. No Complexity Tracking entries required.

### Post-Design Re-evaluation (after Phase 1)

The Phase 0/1 artifacts (research.md, data-model.md, contracts/, quickstart.md) were produced against this gate. Re-check confirms **no new violations**:

- **G2 (Stack Authority)** still PASS — the design reuses the exact existing stack; `contracts/` and `data-model.md` define pydantic models and a route matching existing conventions. No new framework.
- **G5 (Controlled Creativity)** still PASS — the broken-cheque/reversal logic, streaming chat, per-item key, and Bank/Company running totals are all either explicitly required by FR-003/FR-008c/FR-002/FR-002b or documented in research.md as the chosen option with alternatives considered. Nothing novel is being introduced outside the spec's mandate.
- **G4 (Constructive Objection)** — the one flagged gap (no stable per-discrepancy key; no cumulative Bank/Company totals in the current engine) is now resolved in the design: key assignment at the `final_discrepancies` assembly point and running-total computation in `ReconciliationService.reconcile()`. Tracked as required work, not a deviation.
- **G7 (Code Standards)** — reinforced; `data-model.md`/`quickstart.md` explicitly carry the header/footer/crux-marker requirement for every new/edited file.

**Gate re-checked**: PASS after Phase 1. Complexity Tracking remains empty.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── advisor-openapi.yaml
│   ├── advisor-request.json
│   └── advisor-response.json
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── advisor_models.py       # NEW: advisor request/response pydantic models
│   ├── services/
│   │   ├── reconciliation_service.py # EDIT: assign stable per-discrepancy key
│   │   └── advisor_service.py      # NEW: Reconciler Agent (chat + suggestions, streaming, retry)
│   └── api/
│       ├── advisor_routes.py       # NEW: /advisor/* endpoints
│       ├── auth_middleware.py      # EDIT: ensure advisor paths NOT exempt (require Bearer)
│       └── main.py                 # EDIT: mount advisor_router
└── tests/
    └── test_advisor.py             # NEW: suggestion/retry/stream scenarios

frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   └── tooltip.tsx         # NEW: shadcn tooltip (none exists)
│   │   └── advisor/
│   │       ├── AdvisorPanel.tsx    # NEW: dedicated suggestions + reason tooltip + Reconcile
│   │       └── AdvisorChat.tsx     # NEW: stateless streaming chat
│   ├── lib/
│   │   └── api/
│   │       └── advisorClient.ts    # NEW: fetch client for /advisor endpoints
│   └── components/results/
│       └── ReconciliationResults.tsx # EDIT: wire Reconcile With Agent button + callback
└── tests/
```

**Structure Decision**: Two-project layout (backend + frontend) matching the existing repository and the constitution's Dining stack authority. New advisor logic lives in a dedicated `advisor_service` + `advisor_routes` mirroring `ai_routes.py`/`ai_structure_detector.py`, mounted in `main.py`. Reconcile-button removal reuses the existing `handleReconcile` filter in `ReconciliationResults.tsx` so the live list, manual reconcile, and "Complete Reconciliation" save all stay in sync.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(None — gate passed)* | — | — |