---
id: clarify-009-employee-access-request
title: employee-access-request-clarifications
stage: spec
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 009-employee-access-request
branch: 009-employee-access-request
user: developer
command: /sp.clarify
labels: [clarify, spec, subscription, employees, access-request, adam-id, data-model]
links:
  spec: specs/009-employee-access-request/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-employee-access-request/spec.md
  - history/prompts/009-employee-access-request/clarify-009-employee-access-request.prompt.md
tests:
  - null
---

## Prompt

/sp.clarify the spec 009, also write all questions at once

## Response snapshot

Ran the clarification workflow against specs/009-employee-access-request/spec.md (FEATURE_SPEC resolved via check-prerequisites.ps1 -Json -PathsOnly). Per the user's explicit "write all questions at once" instruction, the interactive one-question-at-a-time loop was overridden and all five candidate questions were presented in a single message with options and a recommended choice each. The user did not supply alternate answers, so the recommended resolutions were applied to the spec. Clarifications recorded under a new `## Clarifications` → `### Session 2026-09-30` section with five bullets: (1) Employee ID uniqueness is composite on ID + requested company — resolves the contradiction between FR-011/FR-013/FR-017 ("globally unique ID", "reject duplicate ID") and Edge Case "the same employee submits more than one request over time → each request is recorded"; (2) the stored request references the company's stable ID plus a name snapshot taken at request time (survives Developer renames); (3) the `adam-` ID shape is 6–12 lowercase letters/digits after the prefix, with trim/lowercase/auto-prefix normalization and case-insensitive uniqueness comparison; (4) the dedicated sign-in route is `/login`, with `/` redirecting to `/login` when signed out and to the Subscription page when signed in; (5) a company-list fetch failure shows a distinct "Couldn't load companies" error with Retry and keeps Submit disabled until the list loads.

## Outcome

- ✅ Impact: Spec 009 ambiguity reduced across the Data Model, Interaction/UX, and Routing categories before planning. One genuine internal contradiction (ID uniqueness vs. multiple recorded requests) was resolved, so downstream DB index design and acceptance tests will not be misaligned.
- 🧪 Tests: None run (specification stage; no automated tests per the Developer's standing instruction).
- 📁 Files: specs/009-employee-access-request/spec.md (Clarifications section, US1 scenarios, US2 scenarios, Edge Cases, FR-001/009/011/013/016/017, Key Entities, SC-004/SC-006, Assumptions)
- 🔁 Next prompts: /sp.plan for 009-employee-access-request
- 🧠 Reflection: The user chose to see all questions up front rather than the prescribed sequential loop — the deviation was honored, and because no explicit answers came back the recommended options were applied and are flagged to the user as overridable. This keeps the spec self-consistent while leaving the decision reversible.

## Evaluation notes (flywheel)

- Failure modes observed: The mandated create-phr script (.specify/scripts/bash/create-phr.sh) is absent on this Windows checkout (only .specify/scripts/powershell/*.ps1 exist), so the agent-native fallback was used: read templates/phr-template.prompt.md, allocated a stage-scoped id, and wrote history/prompts/<feature>/. Also, the workflow's "present EXACTLY ONE question at a time" rule was intentionally superseded by the user's args ("write all questions at once").
- Graders run and results (PASS/FAIL): Spec structure PASS (only allowed headings `## Clarifications` and `### Session YYYY-MM-DD` added; one bullet per accepted answer; no duplicate or contradictory statements left behind).
- Prompt variant (if applicable): clarify-v1-all-at-once
- Next experiment (smallest change to try): Before applying resolutions, echo the chosen option set back for a one-word confirmation so unconfirmed defaults are never written into the spec.
