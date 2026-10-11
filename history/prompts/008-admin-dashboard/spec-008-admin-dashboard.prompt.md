---
id: spec-008-admin-dashboard
title: admin-dashboard-spec
stage: spec
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 008-admin-dashboard
branch: 008-admin-dashboard
user: developer
command: /sp.specify
labels: [spec, admin, dashboard, companies, encryption, production-onboarding]
links:
  spec: specs/008-admin-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-admin-dashboard/spec.md
  - specs/008-admin-dashboard/checklists/requirements.md
  - history/prompts/008-admin-dashboard/spec-008-admin-dashboard.prompt.md
tests:
  - null
---

## Prompt

Starting implementation of actually pushing item to production to companies, for that we need a dashboard based access system, the system will be implemented in 3 specs, this is the first spec that is associated with Developer (Me) only.

Current idea:
So current idea that i have revolved around is that i have postponed idea of selling this project to individuals only for now, and i will be providing it to my father's company first. So we are doing a simple implementation for that keeping things as simple and concise as possible to get onboard.
We have a company that contacts me, we talk, negotiate and deal. We reach a conclusion and i create their account (This dashboard is for this), give them user and pass access, the company accesses its dashboard (Later specification) and sees payments and lists of employees, then employees by name of their required company request access. Company grants its employees access, while all payment management is done by company itself.

Current Specification and its Dealings:
This specification is first and foremost the creation of my dashboard.

Frontend:
1. A dashboard with user name and pass in a hidden route called "AdminDashAccess", it is not visible anywhere in the app
2. It contains a username and password
3. I enter the username and password and get access (more to password in backend section)
4. The dashboard is simple and clean, it contains a single page
5. The dashboard basically stores all the companies who want to work with me, i grant access to companies here, remove companies here and see their statuses here
6. So the dashboard lists companies, i can edit their details, i can delete them as well
7. Following data will be used for a company: Company Name (required), Company Logo (optional, file), Company Password (random generator or manual entry), Price (in Rupees, used to charge companies later)
8. This is the data that will be listed to me, moreover this is the data required to add a company. Moreover the list of companies will also show another field called "Payment Status" that will be influenced by a later specification dashboard for companies indicating "Pending" or "Free Trial" or "Paid"
9. Use a simple shadcnUI table for this, a placeholder on top with "+ Add Companies" to add companies. Clicking add companies opens a shadcnUI Popup, the logo will be a file

Backend:
1. The backend contains password in ENV variable to be compared against, when i enter password at runtime app uses my env variable to compare password and username
2. A separate table will be created for the companies i add with my dashboard, they will contain above mentioned fields + the payment status field
3. Encryption: use 'cryptography' library and Fernet; i will generate the Encryption Key and store it in ENV; the password entered for companies by me will be Encrypted via Fernet with my employed Key (Later on decryption in later specification will also be done via this key)

Important Points:
- Keep this specification concise, dont push too long
- Dont do any tests, just finish the task
- Dont juggle over edge cases too much, except for important ones that arrive naturally

## Response snapshot

Created the feature specification at specs/008-admin-dashboard/spec.md on new branch 008-admin-dashboard (number 8 chosen as the highest existing spec was 007; short name "admin-dashboard"). The spec covers: 3 prioritized user stories (hidden-route admin sign-in P1, register a new client company P1, manage and review registered companies P2), 5 edge cases, 20 functional requirements (hidden unlinked AdminDashAccess route, server-side credential check against environment values with a generic failure message, admin-only session, single-page company list, row columns incl. masked password with reveal/copy, "+ Add Companies" popup, name required/logo optional/password generated-or-manual/price in Rupees, edit, delete-revokes-access, Payment Status Pending|Free Trial|Paid defaulting to Pending, dedicated company table surviving restarts, Fernet encryption at rest from an env-held key with no plain-text or log exposure, on-demand password reveal, company-name-as-username deferring company login to a later spec, immediate UI reflection), 3 key entities, 7 assumptions, and 7 measurable success criteria. Generated the quality checklist at checklists/requirements.md — all items pass, no [NEEDS CLARIFICATION] markers (open points resolved as documented assumptions: company name = username, default status Pending, on-demand reveal, optional logo placeholder). Grounded assumptions in the existing codebase conventions (FastAPI backend with env-driven settings, CockroachDB tables provisioned alongside existing migrations, Next.js frontend).

## Outcome

- ✅ Impact: Developer-only specification (spec 1 of 3) delivered; branch 008-admin-dashboard created; quality checklist passed; ready for /sp.clarify or /sp.plan.
- 🧪 Tests: None run (specification stage only, per the user's explicit "dont do any tests").
- 📁 Files: specs/008-admin-dashboard/spec.md, specs/008-admin-dashboard/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 008-admin-dashboard
- 🧠 Reflection: The user explicitly asked for brevity and minimal edge-case handling, so the spec stays tight and resolves ambiguity through documented assumptions rather than clarification markers — while still stating the security-critical invariants (no plain-text password at rest, credentials never shipped to the client, route unreachable from any in-app navigation). Fernet is named because the Developer mandated it (Constitution Principle II).

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 is not Windows PowerShell 5.1 safe — `Join-Path $repoRoot 'history' 'prompts' $branchName` (4 positional args) throws, so the script aborts after creating the branch, spec dir, and template copy but before creating history/prompts/<branch> or printing JSON. Also the full feature description exceeded the Windows command-line length limit, so a shortened description was passed (branch name was pinned via -ShortName). Worked around by creating the prompts directory manually.
- Graders run and results (PASS/FAIL): Spec quality validation PASS (no placeholders, no NEEDS CLARIFICATION, mandatory sections complete, success criteria measurable and technology-agnostic).
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): Fix create-new-feature.ps1's multi-arg Join-Path calls so the script completes cleanly on Windows PowerShell 5.1.
