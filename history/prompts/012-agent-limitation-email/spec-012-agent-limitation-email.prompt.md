---
id: spec-012-agent-limitation-email
title: agent-limitation-email-spec
stage: spec
date: 2026-11-07
surface: cli
model: claude-sonnet-4-5
feature: 012-agent-limitation-email
branch: 012-agent-limitation-email
user: developer
command: /sp.specify
labels: [spec, agent-tools, email-notification, resend, tool-limitation, developer-feedback, frontend-notice, blue-banner]
links:
  spec: specs/012-agent-limitation-email/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-agent-limitation-email/spec.md
  - specs/012-agent-limitation-email/checklists/requirements.md
  - history/prompts/012-agent-limitation-email/spec-012-agent-limitation-email.prompt.md
tests:
  - null
---

## Prompt

/sp.specify

Search in our app and project-masham for overview of project.
We need to implement a small feature

What it is:
We need to provide our agent with a tool to send emails
Why:
Our current agent of extraction, when it extracts it uses its extraction tool, sometimes there are problems or such limitations with extraction tool that the agent can not successfully perform extraction and it needs some upgradations in the tools. Now as i am pushing the app to production i found the idea quite fascinating to provide my agent an email tool that whenever it encounters a particular problem with reconciliation tool's limitation. It sends me an email with an idea of what issue is, and what kind of upgradation of tool or new tool it requires for better functioning

How:
1. Simple, you need to make a resend api tool for our agent to send emails
2. I have made labels in my gmail so whenever an email is sent an email that starts with "Reconciliation Atmata" is put into that label automatically, so email is sent to me ArhamrBrowser@gmail.com with Reconciliation Atmata in its start already pre sent
3. Guide the agent to use tool whenever it has following issues
  - It knows that the error/failure in complete reconciliation is due to tool/engine's limitation
  - There is an error with the tool
  - it needs a new tool and must tell why with a valid reason
  - It must always email when it has "failed due to a technical limitation/problem of tool" not just "any failure"
  - The error must be provided in email with details + example + analogy of the issue and proposed solution
4. Whenever a reconciliation fails and due to technical limitation of tool and the agent sends the email, the user loading screen also shows this update on our frontend. After failure the error message should clearly be indicated in "Blue" color that there is a technical limitaion from our side, the agent has sent the limitation to developer for improvement please wait in the mean time
5. Furthermore tell agent a very little and precise summary not long very short and precise summary of what its tools are made of, not the logic, just very very high level overview (so its proposed solutions are also relevant to context)

## Response snapshot

Created the feature specification at specs/012-agent-limitation-email/spec.md on new branch 012-agent-limitation-email (number 12 chosen as the highest existing spec/branch was 011; short name "agent-limitation-email"). The spec captures 3 prioritized user stories: P1 the extraction agent emails the Developer when it hits a tool/engine limitation (subject prefixed "Reconciliation Atmata", body = issue + details + example + analogy + proposed solution with reason); P1 the user sees a blue "technical limitation on our side, sent to the developer, please wait" notice on the loading screen and the failure; P2 the agent reports only genuine tool/engine limitations, guided by a short high-level purpose-only summary of its tools. It contains 16 functional requirements, 7 edge cases, 4 key entities, 6 measurable success criteria, and 9 assumptions, plus a no-tests Testing Policy matching the project convention.

Grounding (before writing): the app was mapped from CLAUDE.md, project-masham/*, and two parallel deep-dives of the backend agent and the frontend flow. Key findings: (a) the AI extraction agent lives in backend/src/services/ai_structure_detector.py with function tools judge_structure_by_cover, read_excel, read_pdf, read_pdf_words, assess_structure; its system prompt is AGENT_INSTRUCTIONS and it is orchestrated by detect_structure() with nested retry loops; (b) failures surface via AIDetectionError with reason "guardrail_failed"/"llm_failed" and become HTTP 422 detail on POST /reconcile-ai (there is NO existing "tool limitation" concept and ProcessingStatus.FAILED is defined but never set); (c) a Resend integration already exists (backend/src/services/notification_service.py) wired to config RESEND_API_KEY / RESEND_FROM_EMAIL / notify address; (d) the AI frontend flow (frontend/src/app/upload-ai + components/upload/UploadAIConfig.tsx) streams progress over SSE and renders failures in a red banner — the blue info convention is bg-blue-50 border-blue-200 text-blue-800 (+dark variants) and the loading screen is components/ai/live-processing-overlay.tsx.

Two scoping questions were raised (markers left in FR-010 and FR-016) and are pending the Developer: (Q1) do the limitation email and blue notice apply only to AI extraction-agent tool failures, or also to deterministic-engine failures, or all failures? (Q2) how much of the user's financial file content may the email include — raw sample rows/amounts/descriptions, or anonymised/structural examples only? The quality checklist at checklists/requirements.md passes all items except the "no [NEEDS CLARIFICATION] markers remain" line, which is expected until these two are answered.

## Outcome

- ✅ Impact: Specification for the agent tool-limitation email tool + blue technical-failure notice delivered; branch 012-agent-limitation-email created; spec + quality checklist written; two clarifications pending.
- 🧪 Tests: None run (specification stage only, per the project's standing "no tests" instruction).
- 📁 Files: specs/012-agent-limitation-email/spec.md, specs/012-agent-limitation-email/checklists/requirements.md, history/prompts/012-agent-limitation-email/spec-012-agent-limitation-email.prompt.md
- 🔁 Next prompts: answer Q1/Q2, then /sp.plan for 012-agent-limitation-email (or /sp.clarify)
- 🧠 Reflection: The brief already entails a subtle taxonomy the codebase lacks — "failed due to a tool/engine limitation" versus "any failure" — so the spec's real work is defining that classification and its two distinct surfaces (developer email + blue user notice) rather than the send itself. Rescoping to the AI agent flow (not the agentless deterministic /karwai path) and reusing the existing Resend service keeps the feature small. The two clarifications were chosen because they materially change scope (AI-only vs whole engine) and data exposure (financial sample data in an email), which are the two highest-impact unknowns.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 is not Windows PowerShell 5.1 safe — `Join-Path $repoRoot 'history' 'prompts' $branchName` (4 positional args) throws "A positional parameter cannot be found that accepts argument 'prompts'"; the script aborts AFTER creating the branch, specs/<branch>, and the template copy, but BEFORE creating history/prompts/<branch> and before printing JSON. The branch and spec.md were created correctly; the prompts directory + PHR were written by hand. (Same failure noted in the 008, 009, 010, and 011 PHRs; pwsh is not installed.)
- Graders run and results (PASS/FAIL): Spec quality validation PASS on content quality, testability, measurability, edge cases, scope, and assumptions; 2 [NEEDS CLARIFICATION] markers intentionally left (within the max of 3) pending the Developer's answers.
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): Fix create-new-feature.ps1's multi-arg Join-Path call (nested Join-Path or [System.IO.Path]::Combine) so the script completes cleanly on Windows PowerShell 5.1 and stops requiring a manual history-dir creation each feature.
