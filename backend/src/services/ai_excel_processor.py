# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
AI Excel Processor (Istikhraj e Data Ma'a AI)

Extracts transaction rows from an uploaded Excel company ledger using the
AI-detected column names. Derives the format type (single combined
debit/credit column vs separate debit + credit columns) automatically
(FR-004) and delegates to the existing ExcelProcessor so the standardized
output shape is identical to the current flow (FR-007).
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.services.ai_structure_detector import FileStructureOutput
from src.services.excel_processor import ExcelProcessor

logger = logging.getLogger(__name__)


class AIExcelProcessor:
    """AI-driven Excel company record processor.

    Uses the AI-detected columns_excel (exactly 4: date, details,
    debit/credit amount column(s), total) and the detected sheet to call the
    existing ExcelProcessor with the correct format type.
    """

    def __init__(self, request_id: str = "unknown"):
        self.request_id = request_id

    # وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
    @staticmethod
    def derive_format_type(columns_excel: list[str]) -> str:
        """Derive the Excel processing format from the detected amount columns.

        The LLM returns columns_excel in the canonical structured order:
        [date, details, total, amount column(s)].

        - 4 entries (single combined Debit/Credit column) -> 'debit-plus-credit'.
        - 5 entries (separate Debit and Credit columns) -> 'debit-pipe-credit'.

        Args:
            columns_excel: The detected Excel columns in canonical order.

        Returns:
            'debit-plus-credit' or 'debit-pipe-credit'.
        """
        if len(columns_excel) >= 5:
            return "debit-pipe-credit"
        return "debit-plus-credit"

    def process_excel(
        self,
        excel_path: Path,
        structure: FileStructureOutput,
        sheet_name: str = "Sheet1",
    ) -> Dict[str, Any]:
        """Extract company records using the AI-detected columns.

        Args:
            excel_path: Path to the uploaded Excel file.
            structure: Detected file structure (columns_excel, excel layout).
            sheet_name: Excel sheet to read (default "Sheet1").

        Returns:
            Same result shape as ExcelProcessor.process_excel:
            company_records, company_net_total, processing_metadata.
        """
        columns = structure.columns_excel
        if len(columns) < 4:
            raise ValueError(
                f"columns_excel must contain at least 4 columns in canonical order "
                f"[date, details, total, amount(s)], got {columns}"
            )

        format_type = self.derive_format_type(columns)

        # Canonical order: [date, details, total, amount column(s)]
        transaction_date_column = columns[0]
        transaction_details_column = columns[1]
        aggregated_total_column = columns[2]

        debit_plus_credit_column: Optional[str] = None
        debit_column: Optional[str] = None
        credit_column: Optional[str] = None

        if format_type == "debit-pipe-credit":
            # 5 columns: [date, details, total, debit, credit]
            debit_column = columns[3]
            credit_column = columns[4]
        else:
            # 4 columns: [date, details, total, debit/credit]
            debit_plus_credit_column = columns[3]

        processor = ExcelProcessor(self.request_id)
        return processor.process_excel(
            excel_path,
            transaction_date_column,
            transaction_details_column,
            format_type,
            sheet_name,
            debit_plus_credit_column,
            debit_column,
            credit_column,
            aggregated_total_column,
        )


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
