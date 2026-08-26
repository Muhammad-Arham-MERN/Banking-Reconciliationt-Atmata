# Quickstart: AI-Based Data Extraction

**Branch**: `005-ai-data-extraction` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)

How to set up and use the AI-driven reconciliation flow ("Istikhraj e Data Ma'a AI"). This flow runs alongside the existing `/upload` flow, which is unchanged.

## Prerequisites

- Python 3.11+ and the backend environment (see `backend/requirements.txt`).
- Node.js / Next.js frontend environment (`frontend/`).
- A model provider accessible via LiteLLM (the prototype used `gemini/gemini-2.0-flash` with `GOOGLE_API_KEY`, and `deepseek/deepseek-chat`). Any provider LiteLLM supports works via the model-string prefix.

## 1. Configure environment variables

In `backend/.env` (see `.env.example`):

```bash
# AI detection model + credentials (FR-010 — never hardcode these)
AI_MODEL=gemini/gemini-2.0-flash
AI_API_KEY=<your provider API key>
```

`AI_API_KEY` must match the provider named in `AI_MODEL`'s prefix (LiteLLM convention).

## 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt   # now includes openai-agents, litellm
```

```bash
cd frontend
npm install
```

## 3. Run the system

```bash
# Terminal 1 — backend
cd backend
uvicorn src.main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

## 4. Use the AI flow

1. Open the frontend (e.g. `http://localhost:3000`) and sign in.
2. Navigate to **`/upload-AI`** (distinct from `/upload`).
3. Upload a **PDF bank statement** (any bank) and an **Excel company ledger** — no column names, no format selector, no sheet name (FR-001).
4. Optionally select a **past reconciliation history** (FR-001).
5. Submit. Watch the step-by-step progress indicator: **Analyzing file structure → Extracting transactions → Reconciling** (FR-016). Allow up to 2 minutes (SC-003).
6. On success: review the discrepancies, manually reconcile, and save (unchanged pipeline, FR-007/FR-013).
7. On a clear retry message: your files couldn't be analyzed — try again (FR-009).

## 5. Verify the old flow is untouched

Open `/upload` and run the manual flow — behavior must be identical to before this feature (FR-012).

## 6. Run tests

```bash
cd backend
pytest tests/test_ai_structure_detector.py tests/test_ai_pdf_processor.py tests/test_ai_excel_processor.py tests/test_ai_routes.py -v
```

```bash
cd frontend
npm test -- upload-ai
```

## 7. Try a quick API smoke test

```bash
curl -X POST http://localhost:8000/reconcile-ai \
  -F "bankStatement=@statement.pdf" \
  -F "companyData=@ledger.xlsx" \
  -F "historyName=May-26"
```

Expect a 200 with `processing_status: "completed"` (or `"partial_success"`) plus `ai_metadata`, or a 422 `ai_detection_failed` retry message.

## Troubleshooting

- **422 `ai_detection_failed` repeatedly** — check `AI_MODEL` / `AI_API_KEY` values and provider reachability; confirm the PDF has extractable text (scanned PDFs fail gracefully by design).
- **401 on the frontend route** — sign in first; `/upload-AI` is auth-protected like `/upload`.
- **Slow processing** — detection is parallel by design (FR-019); very large files approach the 2-minute margin (SC-003).
