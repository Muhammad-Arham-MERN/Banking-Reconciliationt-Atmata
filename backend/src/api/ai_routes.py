# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
AI Reconciliation Routes (Istikhraj e Data Ma'a AI)

Exposes POST /reconcile-ai — the AI-driven reconciliation endpoint that
auto-detects the structure of uploaded PDF and Excel files (FR-011), extracts
transactions, and runs the same reconciliation pipeline as the current flow
(FR-007). The existing /karwai flow is untouched (FR-012).

Design decisions (from research.md + contracts/api-contract.md):
- Multipart uploads: bankStatement (PDF), companyData (Excel), historyName (optional).
- The AI agent runs ONCE and produces BOTH the PDF structure and Excel column
  names in a single [output] block (FR-019). AI is detection-only.
- After detection, the deterministic PDF and Excel extractors process the
  files CONCURRENTLY via asyncio.gather (FR-019).
- If detection fails after 3 retries -> 422 with a friendly retry message
  (FR-009). If an extractor fails independently -> partial success response
  naming the failed file (FR-018).
- Reuses save_upload_file / validate_upload_file / cleanup_uploaded_files and
  ReconciliationService (FR-007, FR-013, FR-014, FR-015). Past-history merge
  is cloud-backed via cloud_service (user-scoped).
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from src.api.routes import cleanup_uploaded_files, save_upload_file
from src.config import settings
from src.models.api_models import ProcessingStatus
from src.services.ai_excel_processor import AIExcelProcessor
from src.services.ai_pdf_processor import AIPDFProcessor
from src.services.ai_structure_detector import (
    MAX_DETECTION_ATTEMPTS,
    FRIENDLY_RETRY_MESSAGE,
    AIDetectionError,
    detect_structure,
)
from src.services.reconciliation_service import ReconciliationService
from src.services.processing_cancellation import (
    cancel_run,
    is_cancelled,
    register_run,
)
from src.utils.file_helpers import validate_upload_file
from src.utils.logger import (
    log_processing_start,
    log_processing_complete,
    log_file_validation,
)

logger = logging.getLogger(__name__)

# Router for the AI-based reconciliation flow
router = APIRouter()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/reconcile-ai")
async def reconcile_ai(
    request: Request,
    bankStatement: UploadFile,
    companyData: UploadFile,
    historyName: Optional[str] = Form(None),
    sheetName: str = Form("Sheet1"),
    reconciliationType: str = Form("bank"),
    requestId: Optional[str] = Form(None),
):
    """
    AI-driven reconciliation endpoint.

    Uploads a PDF bank statement and Excel company ledger; the AI detects the
    structure of both files automatically (no manual column mapping), extracts
    transactions, and runs the same reconciliation pipeline as /karwai.

    Args:
        sheetName: Excel sheet to read (default "Sheet1"); the detector and
            the Excel processor both use this sheet.
        reconciliationType: Which books the statement belongs to - "bank"
            (default) or "vendor"; passed to the detector so the agent starts
            from the right debit/credit sign convention when evaluating its
            proposed structure (FR-006). The frontend does not surface this
            today, so the default preserves existing behavior.
        requestId: Client-generated id for this request. Lets the frontend
            cancel an in-flight run (Stop button / page reload) before the
            response arrives. A fresh uuid is used when omitted.

    Returns 200 with results (or partial_success), 422 on detection failure,
    400/422 on file validation errors.
    """
    # Check server shutdown status (same as /karwai)
    try:
        from src.api.routes import is_server_shutting_down

        if is_server_shutting_down():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "service_unavailable",
                    "message": "Server is shutting down. Please try again later.",
                    "details": {"shutdown_in_progress": True, "retry_after": 60},
                },
            )
    except ImportError:
        pass

    # Use the client-provided request id when given (so the frontend can cancel
    # the run before the response arrives), otherwise generate a fresh one.
    request_id = (requestId or "").strip() or str(uuid.uuid4())
    log_processing_start(logger, request_id, bankStatement.filename, companyData.filename)

    # Register the run so the frontend can cancel it (page reload / Stop button).
    register_run(request_id)

    pdf_path = None
    excel_path = None

    try:
        # ---- Save + validate uploads (reuse current flow helpers) ----
        pdf_path, pdf_safe_name = await save_upload_file(bankStatement, "pdfs")
        pdf_valid, pdf_errors = validate_upload_file(pdf_path, bankStatement.filename or "", "pdf")
        if not pdf_valid:
            log_file_validation(logger, request_id, bankStatement.filename or "", "pdf", False, ", ".join(pdf_errors))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "processing_error",
                    "message": f"Invalid PDF file: {', '.join(pdf_errors)}",
                    "details": {"file_type": "pdf", "filename": bankStatement.filename, "validation_errors": pdf_errors},
                },
            )
        log_file_validation(logger, request_id, bankStatement.filename or "", "pdf", True)

        excel_path, excel_safe_name = await save_upload_file(companyData, "excels")
        excel_valid, excel_errors = validate_upload_file(excel_path, companyData.filename or "", "excel")
        if not excel_valid:
            log_file_validation(logger, request_id, companyData.filename or "", "excel", False, ", ".join(excel_errors))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "processing_error",
                    "message": f"Invalid Excel file: {', '.join(excel_errors)}",
                    "details": {"file_type": "excel", "filename": companyData.filename, "validation_errors": excel_errors},
                },
            )
        log_file_validation(logger, request_id, companyData.filename or "", "excel", True)

        # ---- AI structure detection: ONE agent run for both files (FR-019) ----
        processing_start = time.time()
        detection_start = time.time()

        sheet_name = sheetName.strip() or "Sheet1"
        rec_type = reconciliationType.strip() or "bank"
        # detect_structure retries up to MAX_DETECTION_ATTEMPTS internally (FR-008);
        # raises AIDetectionError after all attempts fail. It registers the run
        # in the cancellation registry and exposes a live cancel handle.
        structure = await detect_structure(
            pdf_path,
            excel_path,
            sheet_name,
            request_id=request_id,
            reconciliation_type=rec_type,
        )
        detection_time_ms = int((time.time() - detection_start) * 1000)

        if is_cancelled(request_id):
            raise HTTPException(
                status_code=499,
                detail={
                    "error": "cancelled",
                    "message": "Processing cancelled by user",
                    "details": {"request_id": request_id},
                },
            )

        # ---- Extraction: deterministic processors run CONCURRENTLY (FR-019) ----
        pdf_processor = AIPDFProcessor(request_id)
        excel_processor = AIExcelProcessor(request_id)

        pdf_task = asyncio.to_thread(pdf_processor.process_pdf, pdf_path, structure)
        excel_task = asyncio.to_thread(excel_processor.process_excel, excel_path, structure, sheet_name)

        (pdf_result, excel_result), (pdf_error, excel_error) = await _gather_extraction(pdf_task, excel_task)

        if is_cancelled(request_id):
            raise HTTPException(
                status_code=499,
                detail={
                    "error": "cancelled",
                    "message": "Processing cancelled by user",
                    "details": {"request_id": request_id},
                },
            )

        failed_file = None
        if pdf_error is not None:
            failed_file = "PDF"
        if excel_error is not None:
            failed_file = "Excel"

        # ---- Partial success (FR-018) ----
        if failed_file is not None:
            success_file = "Excel" if failed_file == "PDF" else "PDF"
            partial_response = {
                "request_id": request_id,
                "processing_status": ProcessingStatus.PARTIAL_SUCCESS,
                "processing_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "summary": {
                    "total_bank_transactions": len(pdf_result.get("bank_statement", [])) if pdf_result else 0,
                    "total_company_transactions": len(excel_result.get("company_records", [])) if excel_result else 0,
                    "processing_duration_ms": int((time.time() - processing_start) * 1000),
                    "ai_detection_time_ms": detection_time_ms,
                    "partial_success": True,
                    "failed_file": failed_file,
                    "failure_reason": str(pdf_error or excel_error or ""),
                },
                "results": {
                    "bank_statement": pdf_result.get("bank_statement", []) if pdf_result else [],
                    "company_records": excel_result.get("company_records", []) if excel_result else [],
                },
                "ai_metadata": {
                    "retries_used": 1,
                    "failed_file": failed_file,
                    "detected_structure": {
                        "columns_pdf": structure.columns_pdf,
                        "columns_excel": structure.columns_excel,
                    },
                },
                "errors": [f"{failed_file} processing failed: {str(pdf_error or excel_error)}"],
                "message": (
                    f"We couldn't process the {failed_file} file, but the {success_file} "
                    f"was processed successfully. Please try again."
                ),
            }
            log_processing_complete(logger, request_id, None, None, 0, 0, 0)
            return partial_response

        # ---- Full success: reconcile (FR-007) ----
        bank_transactions = pdf_result["bank_statement"]
        company_transactions = excel_result["company_records"]

        if is_cancelled(request_id):
            raise HTTPException(
                status_code=499,
                detail={
                    "error": "cancelled",
                    "message": "Processing cancelled by user",
                    "details": {"request_id": request_id},
                },
            )

        reconciliation_service = ReconciliationService()
        discrepancies = reconciliation_service.reconcile(bank_transactions, company_transactions)

        # Load past history discrepancies to merge, if requested (FR-013).
        # Cloud-backed and user-scoped: pulls the stored past file belonging to
        # the authenticated user by name.
        if historyName:
            try:
                from src.services.cloud_service import load_reconciliation_by_name

                loaded = await load_reconciliation_by_name(
                    request.state.user_id, historyName
                )
                past_discrepancies = (loaded or {}).get("discrepancies", [])
                if past_discrepancies:
                    discrepancies = _merge_past_discrepancies(discrepancies, past_discrepancies)
            except Exception as e:
                logger.warning(f"Failed to load history '{historyName}': {e}")

        bank_only = sum(1 for d in discrepancies if d.get("FROM") == "Bank")
        company_only = sum(1 for d in discrepancies if d.get("FROM") == "Company")
        opposite_pairs_removed = (len(bank_transactions) + len(company_transactions) - len(discrepancies)) // 2

        total_processing_time_ms = int((time.time() - processing_start) * 1000)

        response = {
            "request_id": request_id,
            "processing_status": ProcessingStatus.COMPLETED,
            "processing_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "summary": {
                "total_bank_transactions": len(bank_transactions),
                "total_company_transactions": len(company_transactions),
                "total_discrepancies": len(discrepancies),
                "bank_only_discrepancies": bank_only,
                "company_only_discrepancies": company_only,
                "opposite_pairs_removed": opposite_pairs_removed,
                "pair_mate_pairs_removed": reconciliation_service.pair_mate_pairs_removed,
                "processing_duration_ms": total_processing_time_ms,
                "ai_detection_time_ms": detection_time_ms,
                "pdf_processing_time_ms": pdf_result.get("processing_metadata", {}).get("processing_time_ms", 0),
                "excel_processing_time_ms": excel_result.get("processing_metadata", {}).get("processing_time_ms", 0),
                "concurrent_processing": True,
            },
            "results": {
                "bank_statement": bank_transactions,
                "company_records": company_transactions,
                "discrepancies": discrepancies,
            },
            "bank_net_total": pdf_result.get("bank_net_total"),
            "company_net_total": excel_result.get("company_net_total"),
            "ai_metadata": {
                "model": settings.AI_MODEL or "default",
                "detected_structure": {
                    "columns_pdf": structure.columns_pdf,
                    "columns_excel": structure.columns_excel,
                    "header_words_pdf": structure.header_words_pdf,
                    "header_top_pdf": structure.header_top_pdf,
                    "rows_dropped_pdf": structure.rows_dropped_pdf,
                    "column_boundaries_pdf": structure.column_boundaries_pdf,
                    "band_top_pdf": structure.band_top_pdf,
                    "date_pattern_pdf": structure.date_pattern_pdf,
                    "opening_balance_pdf": structure.opening_balance_pdf,
                    "reconciliation_type": rec_type,
                },
                "retries_used": 1,
                "stages": [
                    {"stage": "structure_detection", "duration_ms": detection_time_ms},
                    {"stage": "extraction", "duration_ms": total_processing_time_ms - detection_time_ms},
                    {"stage": "reconciliation", "duration_ms": reconciliation_service.processing_time_ms},
                ],
            },
            "errors": [],
            "message": f"✅ Reconciliation complete - Found {len(discrepancies)} discrepancies",
        }

        log_processing_complete(
            logger,
            request_id,
            pdf_result.get("processing_metadata", {}).get("processing_time_ms"),
            excel_result.get("processing_metadata", {}).get("processing_time_ms"),
            total_processing_time_ms,
            len(bank_transactions),
            len(company_transactions),
        )

        return response

    except HTTPException:
        raise
    except asyncio.CancelledError:
        # The user cancelled mid-run (Stop button / page reload). CancelledError
        # is a BaseException, so it bypasses `except Exception`; surface it as
        # the same 499 the inter-stage checks use.
        logger.info("Run %s cancelled by user", request_id)
        raise HTTPException(
            status_code=499,
            detail={
                "error": "cancelled",
                "message": "Processing cancelled by user",
                "details": {"request_id": request_id},
            },
        )
    except AIDetectionError as e:
        # The AI structure-detection agent exhausted its retries. Distinguish:
        # guardrail_failed = the agent never produced a structure that passed
        # the assess_structure tool verdict; llm_failed = LLM-failure retries
        # exhausted (internal server error).
        if e.reason == "guardrail_failed":
            detail = {
                "error": "agent_failed",
                "message": e.message or "Agent failed to extract the PDF Structure.",
                "details": {"retries_used": e.retries_used, "error": str(e)},
            }
        else:
            detail = {
                "error": "agent_internal_error",
                "message": e.message or "Agent had internal server error.",
                "details": {"retries_used": e.retries_used, "error": str(e)},
            }
        logger.error("AI structure detection failed: %s", detail)
        raise HTTPException(status_code=422, detail=detail)
    except Exception as e:
        logger.error(f"Unexpected error in /reconcile-ai: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "processing_error",
                "message": FRIENDLY_RETRY_MESSAGE,
                "details": {"error": str(e)},
            },
        )
    finally:
        # Unregister the run so it can no longer be cancelled.
        from src.services.processing_cancellation import unregister_run

        unregister_run(request_id)
        # Guaranteed cleanup (FR-014)
        await cleanup_uploaded_files(pdf_path, excel_path)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/reconcile-ai/{request_id}/cancel")
async def cancel_reconcile_ai(request_id: str):
    """Cancel an in-flight /reconcile-ai request (Stop button / page reload).

    Flips the cancellation flag and halts the streaming LLM run immediately.
    Returns 200 even if the run already finished (idempotent).
    """
    found = cancel_run(request_id)
    return {
        "request_id": request_id,
        "cancelled": found,
        "message": "Processing cancelled" if found else "No active run found",
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def _gather_extraction(pdf_task, excel_task):
    """Run both deterministic extractors concurrently, capturing errors.

    Returns ((pdf_result, excel_result), (pdf_error, excel_error)) where each
    result/error is None for the successful/failed side respectively. This
    gives per-side partial success (FR-018).
    """
    pdf_result = None
    excel_result = None
    pdf_error = None
    excel_error = None

    try:
        pdf_result = await pdf_task
    except Exception as e:
        pdf_error = e
        logger.error(f"AI PDF extraction failed: {e}")

    try:
        excel_result = await excel_task
    except Exception as e:
        excel_error = e
        logger.error(f"AI Excel extraction failed: {e}")

    return (pdf_result, excel_result), (pdf_error, excel_error)


def _merge_past_discrepancies(current: list, past: list) -> list:
    """Merge past discrepancy entries into current results (FR-013), suppressing
    exact duplicates (same details + same date), matching UploadForm semantics."""
    current_keys = {
        (
            d.get("Transaction Detail") or d.get("transaction_details"),
            d.get("Transaction_date") or d.get("transaction_date"),
        )
        for d in current
    }
    mapped = []
    for p in past:
        key = (p.get("transaction_details"), p.get("transaction_date"))
        if key in current_keys:
            continue
        mapped.append(
            {
                "Transaction_date": p.get("transaction_date"),
                "Transaction Detail": p.get("transaction_details"),
                "Debit/Credit": p.get("debit_credit_amount"),
                "FROM": "Bank" if p.get("category") and "Bank" in p.get("category") else "Company",
                "from_past": True,
            }
        )
    combined = list(current) + mapped
    combined.sort(key=lambda d: (d.get("Transaction_date") or ""))
    return combined


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
