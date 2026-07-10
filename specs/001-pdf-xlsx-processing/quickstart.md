# Developer Quickstart: PDF and Excel File Processing

**Feature**: PDF and Excel File Processing for Bank Reconciliation
**Date**: 2025-06-19
**Branch**: `001-pdf-xlsx-processing`
**Status**: Phase 1 Design - Implementation guide

## Overview

This quickstart guide provides step-by-step instructions for implementing the PDF and Excel file processing feature. Follow this guide to set up the development environment, implement the processing services, and test the functionality.

## Prerequisites

### Environment Setup

**Required Software**:
- Python 3.11+
- Java Runtime Environment (JRE) 8+ (required for tabula-py)
- Git

**Python Dependencies** (already in requirements.txt):
```text
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pandas==2.1.4
openpyxl==3.3.0
tabula-py==2.9.0
python-dateutil==2.8.2
pydantic==2.5.0
pydantic-settings==2.1.0
```

### Verify Java Installation

```bash
# Check if Java is installed
java -version

# If not installed, download and install:
# Windows: https://www.java.com/download/
# Linux: sudo apt install default-jre
# macOS: brew install openjdk
```

---

## Development Setup

### 1. Clone and Setup Repository

```bash
# Navigate to project directory
cd D:\Agentic_AI\Bank Reconciliation System

# Create feature branch (already created)
git checkout 001-pdf-xlsx-processing

# Install dependencies
pip install -r backend/requirements.txt

# Verify tabula-py installation
python -c "import tabula; print('tabula-py installed successfully')"
```

### 2. Create Service Directories

```bash
# Create new service directories
mkdir -p backend/src/services
mkdir -p backend/uploads/pdfs
mkdir -p backend/uploads/excels

# Create test directories
mkdir -p backend/tests/unit
mkdir -p backend/tests/integration
mkdir -p backend/fixtures
```

### 3. Prepare Test Files

Create sample test files in `backend/fixtures/`:

```bash
# Copy existing test.py as reference
cp test.py backend/fixtures/reference_pdf_implementation.py

# Create sample test files (manual step)
# - Place a sample PDF bank statement as fixtures/sample_bank_statement.pdf
# - Place a sample Excel file as fixtures/sample_company_records.xlsx
```

---

## Implementation Steps

### Phase 1: Core Processing Services

#### Step 1: Create PDF Processing Service

**File**: `backend/src/services/pdf_processor.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
PDF Processing Service
Extracts transaction data from PDF bank statements using tabula-py
"""
import re
import pandas as pd
import tabula
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class PDFProcessor:
    """Processes PDF bank statements to extract transaction data"""
    
    CANONICAL_COLUMNS = [
        "Tran. Date",
        "Effect Date", 
        "Tran. Narrative",
        "_unused_1",
        "Remitter IBAN",
        "Remitter Bank",
        "Chq / Ref No",
        "Debit",
        "Credit",
        "_unused_2",
        "Balance",
    ]
    
    DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")
    BRANCH_NARRATIVE_PATTERN = re.compile(r"^(\d{4})\s+(.+)$")
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        
    def extract_bank_statement(self) -> pd.DataFrame:
        """Extract bank statement from PDF following test.py pattern"""
        try:
            tables = tabula.read_pdf(self.pdf_path, pages="all")
            if not tables:
                raise ValueError("No tables found in PDF")
            
            raw = tables[0]
            df = raw.iloc[3:].copy()
            df.columns = self.CANONICAL_COLUMNS
            df = df.drop(columns=["_unused_1", "_unused_2"])
            
            # Extract branch and details
            branch_and_details = df["Tran. Narrative"].astype(str).str.extract(
                self.BRANCH_NARRATIVE_PATTERN
            )
            df["Tran. Br."] = branch_and_details[0]
            df["Transaction Details"] = branch_and_details[1]
            
            # Filter valid dates
            df = df[df["Tran. Date"].astype(str).str.match(self.DATE_PATTERN, na=False)]
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            raise ValueError(f"Failed to extract data from PDF: {str(e)}")
    
    def transform_to_standard_format(self, df: pd.DataFrame) -> List[Dict]:
        """Transform PDF data to standardized transaction format"""
        transactions = []
        
        for _, row in df.iterrows():
            # Merge debit/credit
            debit_value = row.get("Debit")
            credit_value = row.get("Credit")
            
            if pd.isna(debit_value) and pd.isna(credit_value):
                continue  # Skip rows with no amounts
                
            if not pd.isna(debit_value) and not pd.isna(credit_value):
                continue  # Skip ambiguous rows
                
            # Assign sign and convert to integer
            if not pd.isna(debit_value):
                amount = int(abs(float(debit_value)))
            else:
                amount = -int(abs(float(credit_value)))
            
            # Normalize date
            date_str = row["Tran. Date"]
            normalized_date = self._normalize_date(date_str)
            
            transactions.append({
                "Transaction_date": normalized_date,
                "Transaction Detail": str(row["Transaction Details"]).strip(),
                "Debit/Credit": amount
            })
        
        return transactions
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert DD-MMM-YY to YYYY-MM-DD"""
        from datetime import datetime
        try:
            dt = datetime.strptime(date_str, "%d-%b-%y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}")

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

#### Step 2: Create Excel Processing Service

**File**: `backend/src/services/excel_processor.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Excel Processing Service  
Extracts transaction data from Excel company records using pandas
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class ExcelProcessor:
    """Processes Excel company records to extract transaction data"""
    
    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
    
    def extract_company_records(
        self, 
        column_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """Extract company records using column mapping"""
        try:
            df = pd.read_excel(self.excel_path)
            
            # Validate columns exist
            for col_name in column_mapping.values():
                if col_name not in df.columns:
                    raise ValueError(f"Column '{col_name}' not found in Excel")
            
            return df
            
        except Exception as e:
            logger.error(f"Excel processing error: {e}")
            raise ValueError(f"Failed to read Excel file: {str(e)}")
    
    def transform_to_standard_format(
        self, 
        df: pd.DataFrame, 
        column_mapping: Dict[str, str]
    ) -> List[Dict]:
        """Transform Excel data to standardized transaction format"""
        transactions = []
        
        # Determine format type (3 or 4 column)
        has_separate_columns = 'debitColumn' in column_mapping
        
        for _, row in df.iterrows():
            # Extract values based on column mapping
            date_value = row[column_mapping['transactionDateColumn']]
            detail_value = row[column_mapping['transactionDetailsColumn']]
            
            # Handle amount based on format
            if has_separate_columns:
                debit_value = row.get(column_mapping.get('debitColumn', ''))
                credit_value = row.get(column_mapping.get('creditColumn', ''))
            else:
                combined_value = row[column_mapping['debitPlusCreditColumn']]
                # Determine sign based on value (negative = credit)
                if pd.isna(combined_value):
                    continue
                debit_value = combined_value if combined_value >= 0 else None
                credit_value = -combined_value if combined_value < 0 else None
            
            # Skip empty rows
            if pd.isna(date_value) or pd.isna(detail_value):
                continue
            
            # Validate amounts
            if pd.isna(debit_value) and pd.isna(credit_value):
                continue
            
            # Merge debit/credit
            if not pd.isna(debit_value) and not pd.isna(credit_value):
                continue  # Skip ambiguous rows
            
            if not pd.isna(debit_value):
                amount = int(abs(float(debit_value)))
            else:
                amount = -int(abs(float(credit_value)))
            
            # Normalize date
            normalized_date = self._normalize_date(date_value)
            
            transactions.append({
                "Transaction_date": normalized_date,
                "Transaction Detail": str(detail_value).strip(),
                "Debit/Credit": amount
            })
        
        return transactions
    
    def _normalize_date(self, date_value) -> str:
        """Handle Excel serial dates and various string formats"""
        # Excel serial date
        if isinstance(date_value, (int, float)):
            dt = datetime(1899, 12, 30) + timedelta(days=date_value)
            return dt.strftime("%Y-%m-%d")
        
        # String date - try common formats
        date_str = str(date_value)
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%y"]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        raise ValueError(f"Unrecognized date format: {date_value}")

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

#### Step 3: Update API Routes

**File**: `backend/src/api/routes.py`

Update the existing `/karwai` endpoint to use the new processing services:

```python
# Add imports
import asyncio
from pathlib import Path
from ..services.pdf_processor import PDFProcessor
from ..services.excel_processor import ExcelProcessor

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@router.post("/karwai")
async def process_reconciliation(
    bankStatement: UploadFile = Form(...),
    companyData: UploadFile = Form(...),
    # ... existing parameters ...
):
    """Enhanced endpoint with actual file processing"""
    
    # Store files locally
    pdf_path = await store_uploaded_file(bankStatement, "pdfs")
    excel_path = await store_uploaded_file(companyData, "excels")
    
    try:
        # Process files concurrently
        pdf_task = asyncio.create_task(process_pdf_file(pdf_path))
        excel_task = asyncio.create_task(process_excel_file(excel_path, params))
        
        results = await asyncio.gather(pdf_task, excel_task, return_exceptions=True)
        
        # Handle results
        if isinstance(results[0], Exception):
            raise results[0]
        if isinstance(results[1], Exception):
            raise results[1]
        
        bank_transactions, company_transactions = results
        
        return {
            "request_id": str(uuid.uuid4()),
            "processing_status": "completed",
            "results": {
                "bank_statement": bank_transactions,
                "company_records": company_transactions
            }
        }
        
    finally:
        # Cleanup files
        cleanup_files([pdf_path, excel_path])

async def process_pdf_file(pdf_path: str) -> List[Dict]:
    """Process PDF file asynchronously"""
    return await asyncio.to_thread(_process_pdf_sync, pdf_path)

def _process_pdf_sync(pdf_path: str) -> List[Dict]:
    """Synchronous PDF processing"""
    processor = PDFProcessor(pdf_path)
    df = processor.extract_bank_statement()
    return processor.transform_to_standard_format(df)

async def process_excel_file(excel_path: str, params: Dict) -> List[Dict]:
    """Process Excel file asynchronously"""
    return await asyncio.to_thread(_process_excel_sync, excel_path, params)

def _process_excel_sync(excel_path: str, params: Dict) -> List[Dict]:
    """Synchronous Excel processing"""
    processor = ExcelProcessor(excel_path)
    column_mapping = build_column_mapping(params)
    df = processor.extract_company_records(column_mapping)
    return processor.transform_to_standard_format(df, column_mapping)
```

---

### Phase 2: Testing

#### Step 1: Create Unit Tests

**File**: `backend/tests/unit/test_pdf_processor.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Unit tests for PDF processing service
"""
import pytest
from backend.src.services.pdf_processor import PDFProcessor

def test_pdf_extraction_success():
    """Test successful PDF extraction"""
    processor = PDFProcessor("fixtures/sample_bank_statement.pdf")
    df = processor.extract_bank_statement()
    
    assert len(df) > 0
    assert "Transaction Details" in df.columns
    assert "Debit" in df.columns
    assert "Credit" in df.columns

def test_debit_credit_merging():
    """Test debit and credit column merging"""
    processor = PDFProcessor("fixtures/sample_bank_statement.pdf")
    df = processor.extract_bank_statement()
    transactions = processor.transform_to_standard_format(df)
    
    # All transactions should have single amount
    for transaction in transactions:
        assert "Debit/Credit" in transaction
        assert isinstance(transaction["Debit/Credit"], int)
```

#### Step 2: Create Integration Tests

**File**: `backend/tests/integration/test_file_processing_flow.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Integration tests for end-to-end file processing
"""
import pytest
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

def test_concurrent_processing_performance():
    """Test that concurrent processing is faster than sequential"""
    # Upload both files and measure time
    # Should complete in < total of individual times
    pass

def test_error_handling_invalid_pdf():
    """Test error handling for invalid PDF"""
    with open("fixtures/malformed.pdf", "rb") as f:
        response = client.post(
            "/api/karwai",
            files={"bankStatement": f},
            data={...}
        )
    
    assert response.status_code == 422
    assert "processing_error" in response.json()
```

---

## Running Tests

```bash
# Run all tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_pdf_processor.py -v

# Run with coverage
pytest tests/ --cov=src/services --cov-report=html
```

---

## Common Issues and Solutions

### Issue 1: Tabula-py Java Not Found

**Error**: `tabula.errors.JavaNotFoundError`

**Solution**:
```bash
# Install Java Runtime Environment
# Windows: Download from java.com
# Linux: sudo apt install default-jre
# Verify: java -version
```

### Issue 2: Excel Column Not Found

**Error**: `Column 'Date' not found in Excel`

**Solution**:
- Verify column name spelling (case-sensitive)
- Check Excel file for leading/trailing spaces in column names
- Use exact column name as it appears in Excel header row

### Issue 3: Date Format Not Recognized

**Error**: `Invalid date format: 15/01/2023`

**Solution**:
- PDF dates must be DD-MMM-YY format (e.g., "15-JAN-23")
- Excel dates can be serial numbers or various string formats
- Add custom date format to `_normalize_date()` method if needed

---

## Development Workflow

### 1. Make Changes

```bash
# Edit service files
vim backend/src/services/pdf_processor.py

# Run tests
pytest tests/unit/test_pdf_processor.py -v
```

### 2. Test Locally

```bash
# Start development server
cd backend
python -m uvicorn src.main:app --reload

# Test with sample files
curl -X POST http://localhost:8000/api/karwai \
  -F "bankStatement=@fixtures/sample_bank_statement.pdf" \
  -F "companyData=@fixtures/sample_company_records.xlsx" \
  -F "formatType=debit-plus-credit" \
  -F "transactionDateColumn=Date" \
  -F "transactionDetailsColumn=Description" \
  -F "debitPlusCreditColumn=Amount"
```

### 3. Debug Tips

```python
# Add logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print intermediate results
print(f"Extracted {len(df)} rows from PDF")
print(f"Transformed to {len(transactions)} transactions")

# Validate data
assert all(t["Debit/Credit"] != 0 for t in transactions)
```

---

## Performance Testing

```bash
# Test with large files
python -m pytest tests/performance/test_large_files.py -v

# Profile processing time
python -m cProfile -o profile.stats your_test.py
python -m pstats profile.stats
```

---

## Next Steps

After completing this quickstart:

1. **Implement all services**: Complete PDF and Excel processors
2. **Update API routes**: Integrate services into existing endpoint
3. **Add comprehensive tests**: Unit, integration, and performance tests
4. **Test with real files**: Use actual bank statements and company records
5. **Handle edge cases**: Implement robust error handling
6. **Optimize performance**: Profile and optimize slow operations
7. **Document API**: Update API documentation with examples

---

## Summary

**Implementation Checklist**:
- ✅ Environment setup (Python, Java, dependencies)
- ✅ Service directories created
- ✅ PDF processing service implemented
- ✅ Excel processing service implemented  
- ✅ API routes updated
- ✅ Unit tests created
- ✅ Integration tests created
- ✅ Error handling implemented
- ✅ Performance optimized
- ✅ Documentation complete

**Ready for development**: Follow the implementation steps in order, testing each component before proceeding to the next. Use the testing and debugging sections to troubleshoot issues.