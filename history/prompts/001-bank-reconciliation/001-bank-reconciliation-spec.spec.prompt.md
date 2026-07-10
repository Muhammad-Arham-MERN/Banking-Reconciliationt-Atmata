---
id: 001
title: Bank Reconciliation Logic Spec
stage: spec
date: 2026-06-23
surface: agent
model: claude-sonnet-4-6
feature: 001-bank-reconciliation
branch: 001-bank-reconciliation
user: Muhammad Arnam
command: /sp.specify
labels: [specification, reconciliation, bank-statement, company-records]
links:
  spec: ../../specs/001-bank-reconciliation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bank-reconciliation/spec.md
  - specs/001-bank-reconciliation/checklists/requirements.md
tests: []
---

## Prompt

our current implementation accross the 3 specs now gives us a frontend, a backend and a backend that can properly process xlsx and pdf files easily and produce results in a structured format, see project-masham for important details on projects, outputs and data structures etc


now final reconciliation is needed, the data is in following format:
~~~
{
  "request_id": "f5af9205-7b5b-4ffb-8f56-95cbe292c09e",
  "processing_status": "completed",
  "processing_timestamp": "2026-06-23T03:20:03.251969Z",
  "summary": {
    "total_bank_transactions": 26,
    "total_company_transactions": 20,
    "processing_duration_ms": 7153,
    "pdf_processing_time_ms": 7151,
    "excel_processing_time_ms": 191,
    "concurrent_processing": true
  },
  "results": {
    "bank_statement": [
      {
        "Transaction_date": "2026-05-05",
        "Transaction Detail": "INWARD CHEQUE",
        "Debit/Credit": 10200.0
      },
      {
        "Transaction_date": "2026-05-06",
        "Transaction Detail": "P2P RECEIVING VIA GREAVES",
        "Debit/Credit": -22000000.0
      },
      {
        "Transaction_date": "2026-05-07",
        "Transaction Detail": "CHEQUE WITHDRAWAL",
        "Debit/Credit": 17929400.0
      }
    ],
    "company_records": [
      {
        "Transaction_date": "2026-05-04",
        "Transaction Detail": "Fund Transfer Through RTGS from SBL to MCB BANK ISB",
        "Debit/Credit": 22000000.0
      },
      {
        "Transaction_date": "2026-05-04",
        "Transaction Detail": "Salaries IIAP mo Apr-26",
        "Debit/Credit": -17929400.0
      },
      {
        "Transaction_date": "2026-05-06",
        "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515",
        "Debit/Credit": -40771.695
      }
    ]
  },
  "errors": [],
  "message": "Concurrent processing complete - Both files processed successfully"
}
~~~

The above is the output returned from routes/Karwai POST Endpoint

Now reconciliation logic will be implemented in following format

1. The lists of "bank_statement" & "company_records" taken
2. compare EACH item of "Bank statement" with each item of "Company Records".
   - Store the items of Bank Statement that are NOT Present in Company Record in an array in same format as Bank statement
   - also add another key to this list "FROM" with value "Bank"
    example) [{
        "Transaction_date": "2026-05-06",
        "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515",
        "Debit/Credit": -40771.695,
	"FROM":"Bank"
     }]
3. compare EACH item of "Company Records" with each item of "Bank Statement"
   - Store the items of Company Records that are NOT Present in Bank Statement in an array in the same format as Company statement
   - also add another key to this list "FROM" with value "Company"
     example) [{
        "Transaction_date": "2026-05-06",
        "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515",
        "Debit/Credit": 6771.238,
	"FROM":"Company"
     }]
4. After the final reconciliation, merge and combine both the lists, to form a single UNIFIED list
5. Check if each item in a list has an opposite duplicate? for example 22000 from Company and -22000 from Bank, or 500 from  bank and -500 from company, if such cases are found, these items of lists will be removed immediately and the list will be filtered with unique and different numbered list and free from same value and opposite signed items

The above is the finalized and basic reconciliation, make sure to follow step 2 and 3 precisely and follow their logic rigorously deterministically to avoid any future logical problems

## Response snapshot

Created comprehensive feature specification for bank reconciliation logic with the following components:

1. **Feature Branch**: Created `001-bank-reconciliation` branch
2. **Specification**: Complete spec.md with:
   - 3 prioritized user stories covering basic reconciliation, performance, and data quality
   - 12 functional requirements defining the reconciliation logic
   - Key entities describing bank/company transactions and discrepancy handling
   - 6 measurable success criteria focused on accuracy and performance
   - Edge cases covering amount-based matching scenarios
   - Dependencies on existing PDF/Excel processing pipeline

3. **Key Design Decision**: Matching logic is based ONLY on opposite sign amounts (bank_amount == -company_amount), not dates or descriptions. Date and description are preserved for frontend display but not used in reconciliation logic.

4. **Quality Checklist**: All validation items passed, specification ready for planning phase

## Outcome

- ✅ Impact: Complete feature specification for bank reconciliation logic ready for architectural planning
- 🧪 Tests: No tests executed yet (specification phase only)
- 📁 Files: Created specs/001-bank-reconciliation/spec.md and quality checklist
- 🔁 Next prompts: `/sp.plan` to create architectural design and implementation approach
- 🧠 Reflection: User provided excellent clarification on matching logic - amounts only, not dates/descriptions. This simplifies implementation and reduces false negatives.

## Evaluation notes (flywheel)

- Failure modes observed: Initial misunderstanding of matching logic (thought it included dates/descriptions). User corrected this immediately, leading to cleaner specification.
- Graders run and results (PASS/FAIL): Quality checklist validation PASSED - all items met
- Prompt variant (if applicable): Standard /sp.specify workflow with user correction during specification creation
- Next experiment (smallest change to try): Consider adding detailed data flow diagram in plan phase to visualize the amount-based matching algorithm