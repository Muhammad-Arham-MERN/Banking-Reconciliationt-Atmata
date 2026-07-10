---
id: sp-spec-002
title: reconciliation-totals-spec
stage: spec
date: 2026-06-29
surface: cli
model: unknown
feature: 002-reconciliation-totals
branch: 002-reconciliation-totals
user: Muhammad-Arham-MERN
command: /sp.specify
labels: [spec, reconciliation, totals]
links:
  spec: specs/002-reconciliation-totals/spec.md
  ticket: ""
  adr: ""
  pr: ""
files:
  - specs/002-reconciliation-totals/spec.md
  - specs/002-reconciliation-totals/checklists/requirements.md
  - history/prompts/002-reconciliation-totals/reconciliation-totals-spec.prompt.md
tests:
  - N/A (specification phase)
---

## Prompt

A new feature is to be implemented in the frontend + backend Backend: 1 (Current): Our system currently takes a few important fields and columns from our Bank Statement 2 (Current): The statements include the debit,credit, details and date columns 3: We also need to take another column of data from table as well, "Balance" 4: After getting balance column, take the LAST ITEM in the list 5: Send that last item to frontend in API Karwai 6: We also receive a few values from frontend during our post request, like column names of date, details, debit and credit etc, we take another column name from frontend whose label will be "Aggregated Total" 7: When in backend we extract data from xlsx processor, we extract another column whose COLUMN name will be "Aggregated Total" user input 8: Take the last item on the list of this column and return it via API to Frontend Frontend: 1: On Receiving the Balance value at the frontend 2: When after processing the results are being displayed 2 subssections after discrepancies section one showing "Bank Net Total" (The final value of balance from pdf) and "Company Net Total" (Final value of aggregated total column last item from xlsx) 3: The discrepancies "Uncleared checks" and "unpresented checks" are to be added to Bank Total Value and displayed 4: The discrepancies "Bank Debited But not credited in cashbook" and "bank credited but not debited in cashbook" are also to be added to Company Total Value and displayed 5: At last both the values should be automatically substracted and the results will be shown below it, if it is 0 then State "Reconciliation Successful, Balanced" if not then vice versa

## Response snapshot

Created full specification for the Reconciliation Totals & Verification feature on branch 002-reconciliation-totals. The spec covers 3 user stories (P1-P3), 14 functional requirements, 4 success criteria, and 7 edge cases. Key additions: extracting last Balance item from PDF bank statements, extracting last Aggregated Total item from XLSX data, displaying Bank Net Total and Company Net Total, applying discrepancy adjustments (Uncleared checks, Unpresented checks, Bank Debited/Credited differences), and auto-subtracting adjusted totals to show a Balanced/Not Balanced verdict. All quality checklist items passed with no NEEDS CLARIFICATION markers required.

## Outcome

- ✅ Impact: Adds complete reconciliation totals and verification feature to the bank reconciliation system
- 🧪 Tests: N/A (specification phase)
- 📁 Files: 3 files created (spec.md, checklists/requirements.md, PHR)
- 🔁 Next prompts: /sp.plan for technical planning
- 🧠 Reflection: Feature description was detailed and unambiguous - no clarification markers needed. All 14 FRs map directly to user requirements.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - all checklist items
- Prompt variant (if applicable): N/A
- Next experiment (if applicable): Proceed to /sp.plan
