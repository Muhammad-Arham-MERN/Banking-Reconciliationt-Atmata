---
id: clarify-2-011-company-employee-wiring
title: company-employee-wiring-clarifications-round-2
stage: spec
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.clarify
labels: [clarify, spec, company-dashboard, employee-access, data-scope, authorization, membership, manager-role, session, validation]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-company-employee-wiring/spec.md
  - specs/011-company-employee-wiring/checklists/requirements.md
  - history/prompts/011-company-employee-wiring/clarify-2-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

/sp.clarify do some further clarification if found anything useful to be clarified

## Response snapshot

Second clarification pass on active feature 011-company-employee-wiring. `check-prerequisites.ps1 -Json -PathsOnly` resolved FEATURE_SPEC correctly. Re-scanned the taxonomy; interaction/UX, edge cases, and completion signals were already Clear, so focused on the remaining security/data-scope and membership gaps and asked three targeted questions one at a time, encoding each answer immediately:

1. What company-granted access unlocks → the company is only a gate; the granted account uses the application with its own personal data and the company neither owns nor sees it (FR-024; Access Grant entity; SC-013; assumptions). Framed with a doorman-vs-shared-office analogy.
2. Whether one account can belong to more than one company at once → one company at a time; a request creates the employee record/ID, cancellation deletes it, and once granted the subscription page is closed until the account leaves (FR-025; Employee entity; SC-014; assumptions). The Developer restated the full request→grant→leave flow to confirm.
3. Who can assign the "Manager" role → anyone with access to the Company Dashboard (the company account and existing Managers) can assign or remove the role for any account (FR-019; US5 scenario 1; Manager entity).

Sections touched: Clarifications (3 new bullets, 11 total under the single Session 2026-10-02 heading), User Story 5 (scenario 1), Functional Requirements (FR-019, FR-024, FR-025), Key Entities (Employee, Access Grant, Manager), Success Criteria (SC-013, SC-014), Assumptions. Validation: 0 [NEEDS CLARIFICATION] markers (grep confirmed), 11 clarification bullets = one per accepted answer, markdown headings valid, no contradictory prior text.

## Outcome

- ✅ Impact: Closed the remaining data-scope and authorization seams: granted access is a pure entry gate (no company visibility into employee data), membership is single-company at a time, and Manager assignment is open to any dashboard user. Spec is now unambiguous and ready for /sp.plan.
- 🧪 Tests: None run (specification stage only, per the Developer's standing "no tests" instruction).
- 📁 Files: specs/011-company-employee-wiring/spec.md, specs/011-company-employee-wiring/checklists/requirements.md
- 🔁 Next prompts: /sp.plan for 011-company-employee-wiring
- 🧠 Reflection: This pass resolved the "who sees what / who belongs where / who can promote" trio that a wiring spec can easily leave implicit. Leading the data-scope question with a concrete doorman analogy avoided the round-trip that Question 4 caused in the first clarify session. The remaining gaps (e.g., whether the Developer can delete a handled onboarding request) are low-impact and were deliberately not asked to respect the "only materially impactful questions" rule.

## Evaluation notes (flywheel)

- Failure modes observed: The Clarifications section now holds eleven bullets under one Session 2026-10-02 heading (three from /sp.specify, five from clarify round 1, three from round 2). Same-day entries merge because only `### Session YYYY-MM-DD` is permitted; per-session quota (<=5) and the cross-session cap (<=10 total) are respected (3 this session; 8 across the feature's clarify runs). check-prerequisites.ps1 ran cleanly on Windows PowerShell 5.1.
- Graders run and results (PASS/FAIL): PASS — one bullet per accepted answer, three questions this session (<=5), zero unresolved placeholders, no contradictory prior statements, coverage summary produced.
- Prompt variant (if applicable): clarify-v1
- Next experiment (smallest change to try): Add a "## Non-Goals / Deferred" mini-section for the low-impact items deliberately not asked (e.g., onboarding-request deletion), so they are visibly deferred rather than silently absent.
