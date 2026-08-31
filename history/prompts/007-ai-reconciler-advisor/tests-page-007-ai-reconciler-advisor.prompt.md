---
id: tests-page-007-ai-reconciler-advisor
title: dummy-test-data-and-upload-defaults
stage: general
date: 2026-08-27
surface: cli
model: claude-sonnet-5
feature: 007-ai-reconciler-advisor
branch: 007-ai-reconciler-advisor
user: developer
command: /sp.implement
labels: [general, frontend, test-data, dummy-data, upload, placeholders, advisor]
links:
  spec: specs/007-ai-reconciler-advisor/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/lib/utils/dummyReconciliationData.ts
  - frontend/src/app/tests/page.tsx
  - frontend/src/app/tests/DummyResultsViewer.tsx
  - frontend/src/components/upload/UploadForm.tsx
  - frontend/src/lib/constants.ts
  - frontend/src/app/layout.tsx
  - history/prompts/007-ai-reconciler-advisor/tests-page-007-ai-reconciler-advisor.prompt.md
tests:
  - "none (user testing convenience feature)"
---

## Prompt

(Executed via /sp.implement, general stage.)

Two requests:

1. **Frontend /tests endpoint**: make a dummy discrepancy list of 500+ data items and 150+ discrepancies across all 4 categories — a very realistic-looking discrepancy list — so the AI Reconciler Advisor implementation can be tested easily without re-running AI reconciliation every time. It must follow exactly how the current reconciliation displays them.

2. **/upload endpoint column defaults**: in the Debit+Credit format's 4 input fields, add the "existing input" with placeholder text for each field: details column placeholder "Transaction Details", debit/credit column placeholder "Deb./Cred. (LC)", date column placeholder "Posting Date", totals balance placeholder "Cumulative Balance (LC)" — so on /upload the user only uploads a file and clicks process instead of manually writing column names.

## Response snapshot

Created a frontend /tests page (auth-protected, matching the /upload page shell) that renders a generated dummy ReconciliationResult through the exact same ReconciliationResults component used by the real flow — so categories, columns, sign-coloring, verification panel, manual-reconcile, and the new advisor panel/chat are byte-for-byte identical. The generator (dummyReconciliationData.ts) produces 300 bank + 300 company transactions and 150 discrepancies across the four display categories (44 Company-negative Unpresented, 39 Company-positive Uncleared, 35 Bank-positive, 32 Bank-negative), with realistic Pakistani bank/company vocabulary (RTGS transfers, P2P via Greaves, cheque issues, utility bills, salaries, suppliers), dates across Apr-Jul 2026, whole-rupee amounts, seeded PRNG for stability, and a Regenerate button. Crucially it embeds the two agent-detectable patterns at stable positions: the broken-cheque trio (Bank +79,000 + +100,000 vs Company -179,000) and the reversal pair (Company -45,000 Jul 19 / +45,000 Jul 24), with unique per-source discrepancy_id keys (Bank:1..N, Company:1..M) matching the backend assignment so the advisor's Reconcile action resolves exactly. A nav link "Test Data" was added to the app header. For /upload, INITIAL_COLUMN_MAPPING in UploadForm.tsx now ships pre-filled (date="Posting Date", details="Transaction Details", debit+credit="Deb./Cred. (LC)", totals="Cumulative Balance (LC)", isComplete=true) and constants.ts placeholders updated to match, so a user uploads both files and clicks Submit without typing column names.

## Outcome

- ✅ Impact: One-click testing of the AI Reconciler Advisor on 150 realistic discrepancies without re-running AI reconciliation; and a frictionless /upload default that matches the bank-statement column vocabulary (Posting Date / Transaction Details / Deb./Cred. (LC) / Cumulative Balance (LC)).
- 🧪 Tests: None (convenience feature). Validation: npx tsc --noEmit clean, next build passes with /tests registered as a dynamic auth-protected route, and a node-based sanity check on the generator confirmed 150 discrepancies (44/39/35/32 across the four categories), 300+300 transactions, both embedded patterns present, and zero duplicate discrepancy_ids after the re-key pass.
- 📁 Files: frontend/src/lib/utils/dummyReconciliationData.ts, frontend/src/app/tests/page.tsx, frontend/src/app/tests/DummyResultsViewer.tsx, frontend/src/components/upload/UploadForm.tsx, frontend/src/lib/constants.ts, frontend/src/app/layout.tsx.
- 🔁 Next prompts: User can open /tests in the browser and click "Reconcile With Agent" to exercise the advisor end-to-end on the dummy data (SC-001/SC-002 smoke).
- 🧠 Reflection: Two details mattered: (1) the display "inverts" Bank-side categories (Bank positive renders as negative, Bank negative as positive) via getDisplayAmount — the dummy generator keeps raw signed values and lets the existing categorization utils produce the display, guaranteeing identical rendering; (2) embedding the patterns by overwriting array slots then re-keying ids per source avoided the duplicate-id trap (Bank:1/Bank:2/Company:3 initially appeared twice), mirroring the backend's sequential per-source assignment.

## Evaluation notes (flywheel)

- Failure modes observed: The first generator assigned discrepancy_ids inline per category, then the embedded patterns overwrote slots — producing duplicate ids (Bank:1, Bank:2, Company:3 appeared twice). Fixed by re-keying all ids sequentially per source in final array order after the overwrites.
- Graders run and results (PASS/FAIL): tsc --noEmit PASS; next build PASS; generator sanity check PASS (counts, patterns, unique ids).
- Prompt variant (if applicable): general-v1
- Next experiment (smallest change to try): None pending — browser smoke test of /tests + advisor.
