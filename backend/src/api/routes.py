# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
API Routes
Main API endpoints for the reconciliation service
"""
import logging
import uuid
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, Form
from typing import Optional, Tuple, Dict, Any, List

from src.models.api_models import HealthResponse, ProcessingStatus
from src.models.file_models import FormatType
from src.models.processing_models import ProcessingResult
from src.services.reconciliation_service import ReconciliationService
from src.config import settings
from src.utils.file_helpers import (
    generate_safe_filename, validate_upload_file,
    get_file_path, delete_files_by_request_id, save_uploaded_file
)
from src.utils.logger import (
    log_processing_start, log_processing_complete,
    log_file_validation, log_error_details
)
from src.utils.error_handlers import (
    handle_pdf_processing_error, handle_excel_processing_error,
    create_partial_success_response
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class LoadHistoryRequestBody(BaseModel):
    """Request body for POST /history/load"""
    file_name: str

# Check if server is shutting down
def is_server_shutting_down():
    """Check if server is in shutdown mode"""
    try:
        from src import main
        return getattr(main, 'is_shutting_down', False)
    except ImportError:
        return False

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns service health status for monitoring and availability checks

    Performance: Must respond within 500ms
    """
    from src.config import settings

    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


# ==================== File Upload Handling ====================

async def save_upload_file(
    upload_file: UploadFile,
    subdirectory: str = "pdfs"
) -> Tuple[Path, str]:
    """
    Save uploaded file to appropriate subdirectory with UUID naming

    Args:
        upload_file: FastAPI UploadFile object
        subdirectory: Subdirectory name ('pdfs' or 'excels')

    Returns:
        Tuple of (file_path, safe_filename)
    """
    # Create upload subdirectory if it doesn't exist
    upload_dir = settings.UPLOAD_DIR / subdirectory
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename with UUID
    safe_filename = generate_safe_filename(upload_file.filename)
    file_path = upload_dir / safe_filename

    # Read and save file content
    file_content = await upload_file.read()
    await save_uploaded_file(file_content, file_path)

    logger.info(f"File saved: {upload_file.filename} -> {file_path}")

    return file_path, safe_filename


async def cleanup_uploaded_files(
    pdf_path: Optional[Path] = None,
    excel_path: Optional[Path] = None
) -> None:
    """
    Cleanup uploaded files after processing

    Args:
        pdf_path: Optional PDF file path to delete
        excel_path: Optional Excel file path to delete
    """
    import time
    start_time = time.time()

    deleted_count = 0
    for file_path in [pdf_path, excel_path]:
        if file_path and file_path.exists():
            try:
                from src.utils.file_helpers import delete_file
                if delete_file(file_path):
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")

    cleanup_time_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Cleanup complete: {deleted_count} files deleted in {cleanup_time_ms}ms")


async def process_pdf_file(
    pdf_path: Path,
    pdf_filename: str,
    request_id: str
) -> Tuple[dict, int]:
    """
    Process PDF bank statement file
    Uses PDFProcessor service for actual implementation

    Args:
        pdf_path: Path to PDF file
        pdf_filename: Original filename
        request_id: Request identifier

    Returns:
        Tuple of (processed_data, processing_time_ms)
    """
    from src.services.pdf_processor import PDFProcessor

    processor = PDFProcessor(request_id)
    result = processor.process_pdf(pdf_path)

    processing_time_ms = result.get("processing_metadata", {}).get("processing_time_ms", 0)

    return result, processing_time_ms


async def process_pdf_async(
    pdf_path: Path,
    pdf_filename: str,
    request_id: str
) -> Tuple[dict, int]:
    """
    Async wrapper for PDF processing using asyncio.to_thread
    Runs CPU-intensive PDF processing in separate thread to avoid blocking event loop

    Args:
        pdf_path: Path to PDF file
        pdf_filename: Original filename
        request_id: Request identifier

    Returns:
        Tuple of (processed_data, processing_time_ms)
    """
    # Create a synchronous wrapper for the actual processing
    def sync_pdf_processing():
        from src.services.pdf_processor import PDFProcessor
        processor = PDFProcessor(request_id)
        result = processor.process_pdf(pdf_path)
        processing_time_ms = result.get("processing_metadata", {}).get("processing_time_ms", 0)
        return result, processing_time_ms

    return await asyncio.to_thread(sync_pdf_processing)


async def process_excel_file(
    excel_path: Path,
    excel_filename: str,
    request_id: str,
    format_type: str,
    transaction_date_column: str,
    transaction_details_column: str,
    sheet_name: str = "Sheet1",
    debit_plus_credit_column: Optional[str] = None,
    debit_column: Optional[str] = None,
    credit_column: Optional[str] = None
) -> Tuple[dict, int]:
    """
    Process Excel company record file
    Uses ExcelProcessor service for actual implementation

    Args:
        excel_path: Path to Excel file
        excel_filename: Original filename
        request_id: Request identifier
        format_type: Format type ('debit-plus-credit' or 'debit-pipe-credit')
        transaction_date_column: Date column name
        transaction_details_column: Details column name
        sheet_name: Excel sheet name to read
        debit_plus_credit_column: Combined amount column (3-col format)
        debit_column: Debit column (4-col format)
        credit_column: Credit column (4-col format)

    Returns:
        Tuple of (processed_data, processing_time_ms)
    """
    from src.services.excel_processor import ExcelProcessor

    processor = ExcelProcessor(request_id)

    # Convert format type string to format expected by processor
    # FormatType enum uses lowercase with underscores
    processor_format_type = format_type.lower().replace('-', '_')

    result = processor.process_excel(
        excel_path,
        transaction_date_column,
        transaction_details_column,
        processor_format_type,
        sheet_name,
        debit_plus_credit_column,
        debit_column,
        credit_column
    )

    processing_time_ms = result.get("processing_metadata", {}).get("processing_time_ms", 0)

    return result, processing_time_ms


async def process_excel_async(
    excel_path: Path,
    excel_filename: str,
    request_id: str,
    format_type: str,
    transaction_date_column: str,
    transaction_details_column: str,
    sheet_name: str = "Sheet1",
    debit_plus_credit_column: Optional[str] = None,
    debit_column: Optional[str] = None,
    credit_column: Optional[str] = None,
    aggregated_total_column: Optional[str] = None
) -> Tuple[dict, int]:
    """
    Async wrapper for Excel processing using asyncio.to_thread
    Runs CPU-intensive Excel processing in separate thread to avoid blocking event loop

    Args:
        excel_path: Path to Excel file
        excel_filename: Original filename
        request_id: Request identifier
        format_type: Format type ('debit-plus-credit' or 'debit-pipe-credit')
        transaction_date_column: Date column name
        transaction_details_column: Details column name
        sheet_name: Excel sheet name to read
        debit_plus_credit_column: Combined amount column (3-col format)
        debit_column: Debit column (4-col format)
        credit_column: Credit column (4-col format)
        aggregated_total_column: Optional column name for Aggregated Total extraction

    Returns:
        Tuple of (processed_data, processing_time_ms)
    """
    # Create a synchronous wrapper for the actual processing
    def sync_excel_processing():
        from src.services.excel_processor import ExcelProcessor
        processor = ExcelProcessor(request_id)

        # CRITICAL LOGGING: Check format_type conversion
        original_format = format_type
        processor_format_type = format_type.lower()  # Only convert to lowercase, keep hyphens
        logger.info(f"🔍 Format type conversion: '{original_format}' → '{processor_format_type}'")

        result = processor.process_excel(
            excel_path,
            transaction_date_column,
            transaction_details_column,
            processor_format_type,
            sheet_name,
            debit_plus_credit_column,
            debit_column,
            credit_column,
            aggregated_total_column
        )

        processing_time_ms = result.get("processing_metadata", {}).get("processing_time_ms", 0)

        # CRITICAL LOGGING: Check processor result before returning
        logger.info(f"🔍 Processor result keys: {list(result.keys())}")
        logger.info(f"🔍 Processor company_records count: {len(result.get('company_records', []))}")

        return result, processing_time_ms

    return await asyncio.to_thread(sync_excel_processing)


@router.post("/karwai")
async def process_reconciliation(
    bankStatement: UploadFile = Form(...),
    companyData: UploadFile = Form(...),
    formatType: str = Form(...),
    transactionDateColumn: str = Form(...),
    transactionDetailsColumn: str = Form(...),
    sheetName: str = Form("Sheet1"),
    debitPlusCreditColumn: Optional[str] = Form(None),
    debitColumn: Optional[str] = Form(None),
    creditColumn: Optional[str] = Form(None),
    aggregatedTotalColumn: Optional[str] = Form(None)
):
    """
    Main reconciliation processing endpoint

    Accepts PDF bank statement and Excel company data files,
    processes them, and returns reconciliation results.

    TODO: Implement actual file processing logic
    Currently returns placeholder response with comprehensive validation
    """

    # Check server shutdown status
    if is_server_shutting_down():
        logger.warning("🚨 Request rejected - server shutting down")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": "Server is shutting down. Please try again later.",
                "details": {"shutdown_in_progress": True, "retry_after": 60}
            }
        )

    logger.info("📊 New reconciliation request received")

    # Validate format type with comprehensive error messages
    try:
        format_type = FormatType(formatType)
        logger.info(f"✅ Format type validated: {formatType}")
    except ValueError:
        logger.error(f"❌ Invalid format type: {formatType}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "bad_request",
                "message": "Invalid format type provided. Must be either 'debit-plus-credit' or 'debit-pipe-credit'.",
                "details": {
                    "provided_format": formatType,
                    "valid_formats": ["debit-plus-credit", "debit-pipe-credit"],
                    "help": "Check your format type spelling and try again"
                }
            }
        )

    # Validate column mapping based on format type with detailed error messages
    if format_type == FormatType.DEBIT_PLUS_CREDIT:
        if not debitPlusCreditColumn:
            logger.error("❌ Missing debitPlusCreditColumn for debit-plus-credit format")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bad_request",
                    "message": "Missing required field for debit-plus-credit format.",
                    "details": {
                        "format_type": "debit-plus-credit",
                        "missing_field": "debitPlusCreditColumn",
                        "required_fields": [
                            "formatType",
                            "transactionDateColumn",
                            "debitPlusCreditColumn",
                            "transactionDetailsColumn"
                        ],
                        "help": "For debit-plus-credit format, provide a combined debit/credit column name"
                    }
                }
        )
    elif format_type == FormatType.DEBIT_PIPE_CREDIT:
        if not debitColumn or not creditColumn:
            missing_fields = []
            if not debitColumn:
                missing_fields.append("debitColumn")
            if not creditColumn:
                missing_fields.append("creditColumn")

            logger.error(f"❌ Missing required fields for debit-pipe-credit format: {missing_fields}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bad_request",
                    "message": f"Missing required field(s) for debit-pipe-credit format: {', '.join(missing_fields)}",
                    "details": {
                        "format_type": "debit-pipe-credit",
                        "missing_fields": missing_fields,
                        "required_fields": [
                            "formatType",
                            "transactionDateColumn",
                            "debitColumn",
                            "creditColumn",
                            "transactionDetailsColumn"
                        ],
                        "help": "For debit-pipe-credit format, provide both separate debit and credit column names"
                    }
                }
            )

    # File upload handling with proper subdirectories
    pdf_path = None
    excel_path = None

    try:
        # Generate request ID
        request_id = str(uuid.uuid4())
        log_processing_start(logger, request_id, bankStatement.filename, companyData.filename)

        # Save PDF file to pdfs/ subdirectory
        pdf_path, pdf_safe_name = await save_upload_file(bankStatement, "pdfs")
        pdf_valid, pdf_errors = validate_upload_file(pdf_path, bankStatement.filename or "", 'pdf')

        if not pdf_valid:
            log_file_validation(logger, request_id, bankStatement.filename or "", 'pdf', False, ", ".join(pdf_errors))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "processing_error",
                    "message": f"Invalid PDF file: {', '.join(pdf_errors)}",
                    "details": {
                        "file_type": "pdf",
                        "filename": bankStatement.filename,
                        "validation_errors": pdf_errors
                    }
                }
            )

        log_file_validation(logger, request_id, bankStatement.filename or "", 'pdf', True)

        # Save Excel file to excels/ subdirectory
        excel_path, excel_safe_name = await save_upload_file(companyData, "excels")
        excel_valid, excel_errors = validate_upload_file(excel_path, companyData.filename or "", 'excel')

        if not excel_valid:
            log_file_validation(logger, request_id, companyData.filename or "", 'excel', False, ", ".join(excel_errors))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "processing_error",
                    "message": f"Invalid Excel file: {', '.join(excel_errors)}",
                    "details": {
                        "file_type": "excel",
                        "filename": companyData.filename,
                        "validation_errors": excel_errors
                    }
                }
            )

        log_file_validation(logger, request_id, companyData.filename or "", 'excel', True)

        # Process files concurrently with proper error handling
        import time
        processing_start = time.time()

        try:
            # Process PDF and Excel concurrently using asyncio.gather
            logger.info("🚀 Processing files concurrently...")

            # Create processing tasks
            pdf_task = process_pdf_async(pdf_path, bankStatement.filename or "", request_id)
            excel_task = process_excel_async(
                excel_path, companyData.filename or "", request_id, formatType,
                transactionDateColumn, transactionDetailsColumn, sheetName,
                debitPlusCreditColumn, debitColumn, creditColumn, aggregatedTotalColumn
            )

            # Run both tasks concurrently and wait for both to complete
            (pdf_result, pdf_time), (excel_result, excel_time) = await asyncio.gather(
                pdf_task, excel_task
            )

            logger.info(f"✅ PDF processing completed: {len(pdf_result.get('bank_statement', []))} transactions")
            logger.info(f"✅ Excel processing completed: {len(excel_result.get('company_records', []))} transactions")

            # CRITICAL LOGGING: Check excel_result content IMMEDIATELY after processing
            logger.info(f"🔍 IMMEDIATE excel_result keys: {list(excel_result.keys())}")
            logger.info(f"🔍 IMMEDIATE excel_result['company_records'] length: {len(excel_result.get('company_records', []))}")
            logger.info(f"🔍 IMMEDIATE excel_result content: {str(excel_result)[:500]}")

            # Initialize error variables
            pdf_error = None
            excel_error = None

            # Process PDF result (already processed above)
            logger.info(f"✅ PDF processing completed in {pdf_time}ms")

            # Process Excel result (already processed above)
            logger.info(f"✅ Excel processing completed in {excel_time}ms")

            # Calculate total processing time
            total_processing_time = int((time.time() - processing_start) * 1000)

            # Handle partial success scenario
            if pdf_error and excel_error:
                # Both files failed
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "processing_error",
                        "message": "Both PDF and Excel processing failed",
                        "details": {
                            "pdf_error": pdf_error,
                            "excel_error": excel_error
                        }
                    }
                )
            elif pdf_error or excel_error:
                # Partial success - one file processed, one failed
                failed_file = "PDF" if pdf_error else "Excel"
                failed_error = pdf_error if pdf_error else excel_error
                success_file = "Excel" if pdf_error else "PDF"

                partial_response = {
                    "request_id": request_id,
                    "processing_status": ProcessingStatus.PARTIAL_SUCCESS,
                    "processing_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "summary": {
                        "total_bank_transactions": len(pdf_result.get("bank_statement", [])),
                        "total_company_transactions": len(excel_result.get("company_records", [])),
                        "processing_duration_ms": total_processing_time,
                        "partial_success": True,
                        "failed_file": failed_file,
                        "failure_reason": failed_error
                    },
                    "results": {
                        "bank_statement": pdf_result.get("bank_statement", []),
                        "company_records": excel_result.get("company_records", [])
                    },
                    "errors": [f"{failed_file} processing failed: {failed_error}"],
                    "message": f"⚠️ Partial success: {success_file} processed successfully, {failed_file} failed"
                }

                log_processing_complete(
                    logger,
                    request_id,
                    pdf_result.get("processing_metadata", {}).get("processing_time_ms"),
                    excel_result.get("processing_metadata", {}).get("processing_time_ms"),
                    total_processing_time,
                    len(pdf_result.get("bank_statement", [])),
                    len(excel_result.get("company_records", []))
                )

                return partial_response

            # Both files processed successfully - perform reconciliation
            bank_transactions = pdf_result.get("bank_statement", [])
            company_transactions = excel_result.get("company_records", [])

            # Initialize reconciliation service and perform reconciliation
            reconciliation_service = ReconciliationService()
            discrepancies = reconciliation_service.reconcile(bank_transactions, company_transactions)

            logger.info(f"✅ Reconciliation completed: {len(discrepancies)} discrepancies found")

            # Calculate discrepancy statistics
            bank_only_discrepancies = sum(1 for d in discrepancies if d.get('FROM') == 'Bank')
            company_only_discrepancies = sum(1 for d in discrepancies if d.get('FROM') == 'Company')
            opposite_pairs_removed = (len(bank_transactions) + len(company_transactions) - len(discrepancies)) // 2

            response = {
                "request_id": request_id,
                "processing_status": ProcessingStatus.COMPLETED,
                "processing_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "summary": {
                    "total_bank_transactions": len(bank_transactions),
                    "total_company_transactions": len(company_transactions),
                    "total_discrepancies": len(discrepancies),
                    "bank_only_discrepancies": bank_only_discrepancies,
                    "company_only_discrepancies": company_only_discrepancies,
                    "opposite_pairs_removed": opposite_pairs_removed,
                    "pair_mate_pairs_removed": reconciliation_service.pair_mate_pairs_removed,
                    "processing_duration_ms": total_processing_time,
                    "pdf_processing_time_ms": pdf_time,
                    "excel_processing_time_ms": excel_time,
                    "concurrent_processing": True
                },
                "results": {
                    "bank_statement": bank_transactions,
                    "company_records": company_transactions,
                    "discrepancies": discrepancies
                },
                "bank_net_total": pdf_result.get("bank_net_total"),
                "company_net_total": excel_result.get("company_net_total"),
                "errors": [],
                "message": f"✅ Reconciliation complete - Found {len(discrepancies)} discrepancies"
            }

            # Log completion with transaction counts
            log_processing_complete(
                logger,
                request_id,
                pdf_time,
                excel_time,
                total_processing_time,
                len(bank_transactions),
                len(company_transactions)
            )

            return response

        except Exception as processing_error:
            logger.error(f"Processing error: {str(processing_error)}")
            raise processing_error

    finally:
        # Guaranteed cleanup: Always delete uploaded files
        await cleanup_uploaded_files(pdf_path, excel_path)


# ==================== History Load (merge past file; cloud-backed) ====================

@router.post("/history/load")
async def load_history(request: Request, body: LoadHistoryRequestBody):
    """
    Load discrepancy entries from cloud database (user-scoped).
    Each entry includes category, transaction_details, transaction_date, debit_credit_amount,
    and from_past=True.

    Returns 404 if the record is not found, 422 if the data is corrupted.
    """
    from src.services.cloud_service import load_reconciliation_by_name

    user_id = request.state.user_id
    file_data = await load_reconciliation_by_name(user_id, body.file_name)
    if not file_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "file_not_found",
                "message": f"History record '{body.file_name}' not found in cloud database.",
            },
        )

    discrepancies = []
    for entry in file_data["discrepancies"]:
        discrepancies.append({
            "category": entry.get("category", ""),
            "transaction_details": entry.get("transaction_details", ""),
            "transaction_date": entry.get("transaction_date", ""),
            "debit_credit_amount": entry.get("debit_credit_amount", 0.0),
            "from_past": True,
        })

    return {
        "status": "loaded",
        "file_name": body.file_name,
        "discrepancies": discrepancies,
        "entry_count": len(discrepancies),
    }


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ# Testing auto-reload Mon Jun 22 09:14:25 PST 2026
