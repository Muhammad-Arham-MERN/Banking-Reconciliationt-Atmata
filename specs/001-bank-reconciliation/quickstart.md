# Developer Quickstart Guide: Bank Reconciliation Logic

**Feature**: 001-bank-reconciliation  
**Branch**: `001-bank-reconciliation`  
**Last Updated**: 2026-06-23  
**For**: Developers implementing reconciliation logic

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+ installed
- Node.js 18+ installed  
- Git repository cloned locally
- Existing backend and frontend setup

### 1. Checkout Feature Branch
```bash
git checkout 001-bank-reconciliation
git pull origin 001-bank-reconciliation
```

### 2. Backend Setup (2 minutes)
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup (2 minutes)
```bash
# New terminal
cd frontend
npm install
npm run dev
```

### 4. Test Upload (1 minute)
- Open browser: `http://localhost:3000`
- Upload test PDF and Excel files
- View reconciliation results

---

## 📁 Project Structure Overview

```
Bank Reconciliation System/
├── backend/
│   ├── src/
│   │   ├── services/
│   │   │   ├── reconciliation_service.py    # 🆕 NEW - Core reconciliation logic
│   │   │   ├── pdf_service.py              # Existing - PDF processing
│   │   │   └── excel_service.py            # Existing - Excel processing
│   │   ├── models/
│   │   │   ├── reconciliation_models.py    # 🆕 NEW - Data models
│   │   │   └── file_models.py              # Existing - File models
│   │   ├── api/
│   │   │   └── routes.py                    # ✏️ MODIFY - Add reconciliation to karwai endpoint
│   │   └── utils/
│   │       └── response_helpers.py         # ✏️ MODIFY - Add discrepancy formatting
│   └── tests/
│       ├── unit/
│       │   └── test_reconciliation_service.py  # 🆕 NEW - Unit tests
│       └── integration/
│           └── test_reconciliation_flow.py    # 🆕 NEW - Integration tests
└── frontend/
    └── src/
        ├── components/
        │   └── results/
        │       └── DiscrepancyList.tsx      # 🆕 NEW - Display discrepancies
        ├── types/
        │   └── reconciliation.types.ts      # 🆕 NEW - TypeScript types
        └── lib/
            └── api/
                └── reconciliationClient.ts  # 🆕 NEW - API client
```

---

## 🔨 Implementation Steps

### Phase 1: Core Reconciliation Service (Priority: P1)

#### Step 1.1: Create Data Models
**File**: `backend/src/models/reconciliation_models.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Reconciliation data models for bank reconciliation logic.
Defines Pydantic models for API contracts and validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BankTransaction(BaseModel):
    """Individual transaction from bank statement"""
    Transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    Transaction_Detail: str = Field(..., description="Transaction description")
    Debit_Credit: float = Field(..., description="Amount with sign (positive for credit, negative for debit)")

class CompanyTransaction(BaseModel):
    """Individual transaction from company records"""
    Transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    Transaction_Detail: str = Field(..., description="Transaction description")  
    Debit_Credit: float = Field(..., description="Amount with sign (positive for credit, negative for debit)")

class DiscrepancyTransaction(BaseModel):
    """Transaction present in one source but not the other"""
    Transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    Transaction_Detail: str = Field(..., description="Transaction description")
    Debit_Credit: float = Field(..., description="Amount with sign (positive for credit, negative for debit)")
    FROM: str = Field(..., description="Source of this discrepancy: 'Bank' or 'Company'")

class ReconciliationSummary(BaseModel):
    """Summary statistics for reconciliation process"""
    total_bank_transactions: int
    total_company_transactions: int
    total_discrepancies: int
    bank_only_discrepancies: int
    company_only_discrepancies: int
    opposite_pairs_removed: int
    processing_duration_ms: int
    pdf_processing_time_ms: int
    excel_processing_time_ms: int
    concurrent_processing: bool

# وَإِنَّ اللَّهَ لَهُو خَيْرُ الرَّازِقِينَ
```

#### Step 1.2: Create Reconciliation Service
**File**: `backend/src/services/reconciliation_service.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Bank reconciliation service implementing amount-based transaction comparison.
Core reconciliation logic with deterministic behavior and opposite sign removal.
"""
from typing import List, Dict, Any
import time
from decimal import Decimal

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

class ReconciliationService:
    """Service for bank statement and company records reconciliation"""
    
    def __init__(self):
        self.processing_time_ms = 0
    
    def reconcile(self, 
                 bank_transactions: List[Dict[str, Any]], 
                 company_transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform reconciliation between bank and company transactions.
        
        Args:
            bank_transactions: List of bank transaction dictionaries
            company_transactions: List of company transaction dictionaries
            
        Returns:
            List of discrepancy transactions with source attribution
        """
        start_time = time.time()
        
        # Find discrepancies from both sources
        bank_discrepancies = self._find_bank_discrepancies(bank_transactions, company_transactions)
        company_discrepancies = self._find_company_discrepancies(company_transactions, bank_transactions)
        
        # Remove opposite sign pairs
        final_discrepancies = self._remove_opposite_pairs(bank_discrepancies, company_discrepancies)
        
        self.processing_time_ms = int((time.time() - start_time) * 1000)
        return final_discrepancies
    
    def _find_bank_discrepancies(self, 
                                bank_transactions: List[Dict[str, Any]], 
                                company_transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find bank transactions that don't have matching opposite in company records.
        Matching based ONLY on amount: bank_amount == -company_amount
        """
        discrepancies = []
        
        for bank_tx in bank_transactions:
            matched = False
            bank_amount = bank_tx.get('Debit/Credit', 0.0)
            
            # Look for opposite amount in company transactions
            for company_tx in company_transactions:
                company_amount = company_tx.get('Debit/Credit', 0.0)
                
                if self._amounts_match(bank_amount, company_amount):
                    matched = True
                    break  # Early termination optimization
            
            # If no match found, add to discrepancies
            if not matched:
                discrepancy_tx = bank_tx.copy()
                discrepancy_tx['FROM'] = 'Bank'
                discrepancies.append(discrepancy_tx)
        
        return discrepancies
    
    def _find_company_discrepancies(self, 
                                   company_transactions: List[Dict[str, Any]], 
                                   bank_transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find company transactions that don't have matching opposite in bank statement.
        Matching based ONLY on amount: company_amount == -bank_amount
        """
        discrepancies = []
        
        for company_tx in company_transactions:
            matched = False
            company_amount = company_tx.get('Debit/Credit', 0.0)
            
            # Look for opposite amount in bank transactions
            for bank_tx in bank_transactions:
                bank_amount = bank_tx.get('Debit/Credit', 0.0)
                
                if self._amounts_match(company_amount, bank_amount):
                    matched = True
                    break  # Early termination optimization
            
            # If no match found, add to discrepancies
            if not matched:
                discrepancy_tx = company_tx.copy()
                discrepancy_tx['FROM'] = 'Company'
                discrepancies.append(discrepancy_tx)
        
        return discrepancies
    
    def _amounts_match(self, amount1: float, amount2: float) -> bool:
        """
        Check if two amounts are opposite signs (amount1 == -amount2).
        Uses direct equality with Decimal fallback for edge cases.
        """
        # Primary: Direct equality (fast, exact for file data)
        if amount1 == -amount2:
            return True
        
        # Fallback: Decimal comparison for edge cases
        try:
            return Decimal(str(amount1)) == Decimal(str(-amount2))
        except (ValueError, TypeError):
            return False  # Malformed data
    
    def _remove_opposite_pairs(self, 
                              bank_discrepancies: List[Dict[str, Any]], 
                              company_discrepancies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove opposite sign pairs from discrepancy lists.
        Maintains deterministic order and preserves source attribution.
        """
        # Build amount lookup for company discrepancies
        company_amounts = [tx.get('Debit/Credit', 0.0) for tx in company_discrepancies]
        company_used = [False] * len(company_discrepancies)
        
        # Filter bank discrepancies (remove if opposite found in company)
        filtered_bank = []
        for bank_tx in bank_discrepancies:
            matched = False
            bank_amount = bank_tx.get('Debit/Credit', 0.0)
            
            # Look for opposite in company discrepancies
            for i, company_amount in enumerate(company_amounts):
                if not company_used[i] and self._amounts_match(bank_amount, company_amount):
                    matched = True
                    company_used[i] = True  # Mark as used
                    break
            
            if not matched:
                filtered_bank.append(bank_tx)
        
        # Filter company discrepancies (remove used ones)
        filtered_company = [
            tx for tx, used in zip(company_discrepancies, company_used) if not used
        ]
        
        # Merge and return
        return filtered_bank + filtered_company

# وَإِنَّ اللَّهَ لَهُو خَيْرُ الرَّازِقِينَ
```

#### Step 1.3: Add Unit Tests
**File**: `backend/tests/unit/test_reconciliation_service.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Unit tests for reconciliation service logic.
Tests all reconciliation scenarios and edge cases.
"""
import pytest
from src.services.reconciliation_service import ReconciliationService

class TestReconciliationService:
    """Test suite for reconciliation service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = ReconciliationService()
    
    def test_opposite_sign_removal(self):
        """Test that opposite sign pairs are correctly removed"""
        bank_txs = [{"Debit/Credit": -100.0}]
        company_txs = [{"Debit/Credit": 100.0}]
        
        result = self.service.reconcile(bank_txs, company_txs)
        
        assert len(result) == 0, "Opposite sign pairs should be removed"
    
    def test_bank_only_discrepancy(self):
        """Test bank-only transaction is identified"""
        bank_txs = [{"Debit/Credit": -200.0}]
        company_txs = [{"Debit/Credit": 100.0}]
        
        result = self.service.reconcile(bank_txs, company_txs)
        
        assert len(result) == 1
        assert result[0]['Debit/Credit'] == -200.0
        assert result[0]['FROM'] == 'Bank'
    
    def test_company_only_discrepancy(self):
        """Test company-only transaction is identified"""
        bank_txs = [{"Debit/Credit": -100.0}]
        company_txs = [{"Debit/Credit": 200.0}]
        
        result = self.service.reconcile(bank_txs, company_txs)
        
        assert len(result) == 1
        assert result[0]['Debit/Credit'] == 200.0
        assert result[0]['FROM'] == 'Company'
    
    def test_deterministic_behavior(self):
        """Test that same inputs produce same outputs"""
        bank_txs = [{"Debit/Credit": -100.0}, {"Debit/Credit": -200.0}]
        company_txs = [{"Debit/Credit": 100.0}]
        
        result1 = self.service.reconcile(bank_txs, company_txs)
        result2 = self.service.reconcile(bank_txs, company_txs)
        
        assert result1 == result2, "Results should be deterministic"

# وَإِنَّ اللَّهَ لَهُو خَيْرُ الرَّازِقِينَ
```

### Phase 2: API Integration (Priority: P1)

#### Step 2.1: Modify Routes
**File**: `backend/src/api/routes.py` (MODIFY existing)

```python
# Add import at top
from src.services.reconciliation_service import ReconciliationService

# Modify karwai endpoint
@router.post("/karwai")
async def process_files(
    bank_statement: UploadFile = File(...),
    company_records: UploadFile = File(...),
    sheetName: Optional[str] = "Sheet1"
):
    """Process bank statement and company records with reconciliation"""
    
    # وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
    
    request_id = str(uuid.uuid4())
    
    try:
        # Existing PDF and Excel processing
        pdf_result = await process_pdf(bank_statement, request_id)
        excel_result = await process_excel(company_records, request_id, sheetName)
        
        # NEW: Add reconciliation
        reconciliation_service = ReconciliationService()
        discrepancies = reconciliation_service.reconcile(
            pdf_result['transactions'],
            excel_result['transactions']
        )
        
        # Build enhanced response
        response = {
            "request_id": request_id,
            "processing_status": "completed",
            "processing_timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_bank_transactions": len(pdf_result['transactions']),
                "total_company_transactions": len(excel_result['transactions']),
                "total_discrepancies": len(discrepancies),
                "bank_only_discrepancies": sum(1 for d in discrepancies if d['FROM'] == 'Bank'),
                "company_only_discrepancies": sum(1 for d in discrepancies if d['FROM'] == 'Company'),
                "opposite_pairs_removed": (len(pdf_result['transactions']) + len(excel_result['transactions']) - len(discrepancies)) // 2,
                "processing_duration_ms": reconciliation_service.processing_time_ms,
                "pdf_processing_time_ms": pdf_result['processing_time_ms'],
                "excel_processing_time_ms": excel_result['processing_time_ms'],
                "concurrent_processing": True
            },
            "results": {
                "bank_statement": pdf_result['transactions'],
                "company_records": excel_result['transactions'],
                "discrepancies": discrepancies  # NEW: Add discrepancies
            },
            "errors": [],
            "message": f"Reconciliation complete - Found {len(discrepancies)} discrepancies"
        }
        
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        # Error handling
        return error_response(request_id, str(e))
```

### Phase 3: Frontend Display (Priority: P2)

#### Step 3.1: Create TypeScript Types
**File**: `frontend/src/types/reconciliation.types.ts`

```typescript
// TypeScript types for reconciliation data structures
export interface BankTransaction {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
}

export interface CompanyTransaction {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
}

export interface DiscrepancyTransaction {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
  'FROM': 'Bank' | 'Company';
}

export interface ReconciliationResult {
  request_id: string;
  processing_status: 'completed' | 'partial' | 'error';
  processing_timestamp: string;
  summary: {
    total_bank_transactions: number;
    total_company_transactions: number;
    total_discrepancies: number;
    bank_only_discrepancies: number;
    company_only_discrepancies: number;
    opposite_pairs_removed: number;
    processing_duration_ms: number;
  };
  results: {
    bank_statement: BankTransaction[];
    company_records: CompanyTransaction[];
    discrepancies: DiscrepancyTransaction[];
  };
  errors: string[];
  message: string;
}
```

#### Step 3.2: Create Discrepancy Display Component
**File**: `frontend/src/components/results/DiscrepancyList.tsx`

```typescript
'use client';
import React from 'react';
import { DiscrepancyTransaction } from '@/types/reconciliation.types';

interface DiscrepancyListProps {
  discrepancies: DiscrepancyTransaction[];
}

export const DiscrepancyList: React.FC<DiscrepancyListProps> = ({ discrepancies }) => {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Reconciliation Discrepancies</h2>
      
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <p className="text-sm">
          Found <strong>{discrepancies.length}</strong> discrepancies between bank statement and company records.
        </p>
      </div>

      <div className="space-y-2">
        {discrepancies.map((discrepancy, index) => (
          <div 
            key={index} 
            className={`p-4 border rounded ${
              discrepancy.FROM === 'Bank' 
                ? 'bg-blue-50 border-blue-200' 
                : 'bg-green-50 border-green-200'
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="space-y-1">
                <p className="text-sm text-gray-600">{discrepancy['Transaction_date']}</p>
                <p className="font-medium">{discrepancy['Transaction Detail']}</p>
                <p className={`text-lg font-bold ${
                  discrepancy['Debit/Credit'] >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {discrepancy['Debit/Credit'] >= 0 ? '+' : ''}{discrepancy['Debit/Credit']}
                </p>
              </div>
              <div className={`px-3 py-1 rounded text-sm font-medium ${
                discrepancy.FROM === 'Bank' 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {discrepancy.FROM}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 🧪 Testing Your Implementation

### Run Backend Tests
```bash
cd backend
pytest tests/unit/test_reconciliation_service.py -v
pytest tests/integration/test_reconciliation_flow.py -v
```

### Run Frontend Tests
```bash
cd frontend
npm test -- DiscrepancyList.test.tsx
```

### Manual Testing
1. Start both servers (backend + frontend)
2. Upload test files to `http://localhost:3000`
3. Check reconciliation results appear correctly
4. Verify source attribution (Bank vs Company)
5. Confirm opposite sign pairs are removed

---

## 📊 Performance Monitoring

### Key Metrics to Track
- **Reconciliation Time**: Should be <100ms for typical files
- **Total Processing Time**: Should be <10 seconds including PDF/Excel processing
- **Memory Usage**: Should stay under 100MB
- **Discrepancy Accuracy**: 100% of genuine discrepancies found

### Performance Test
```bash
# Backend performance test
cd backend
pytest tests/performance/test_reconciliation_performance.py --benchmark-only
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Reconciliation results not showing
- **Check**: Backend logs for reconciliation service errors
- **Verify**: discrepancies field in API response
- **Test**: Reconciliation service unit tests pass

**Issue**: Wrong source attribution
- **Check**: FROM field assignment in reconciliation service
- **Verify**: Amount-based matching logic is correct
- **Test**: Unit tests for bank-only and company-only discrepancies

**Issue**: Opposite pairs not removed
- **Check**: _remove_opposite_pairs method logic
- **Verify**: Amount comparison uses opposite signs
- **Test**: Unit test for opposite sign removal

---

## 📚 Additional Resources

- **Full Specification**: `specs/001-bank-reconciliation/spec.md`
- **Implementation Plan**: `specs/001-bank-reconciliation/plan.md`
- **API Documentation**: `specs/001-bank-reconciliation/contracts/reconciliation-api.json`
- **Data Models**: `specs/001-bank-reconciliation/data-model.md`

---

## ✅ Implementation Checklist

- [ ] Create reconciliation_models.py with Pydantic models
- [ ] Create reconciliation_service.py with core logic
- [ ] Add unit tests for reconciliation service
- [ ] Modify routes.py to integrate reconciliation
- [ ] Create TypeScript types for frontend
- [ ] Build DiscrepancyList component
- [ ] Add integration tests
- [ ] Performance testing and optimization
- [ ] Documentation updates

**Estimated Time**: 4-6 hours for complete implementation

---

**Happy Coding! 🚀**

*وَإِنَّ اللَّهَ لَهُو خَيْرُ الرَّازِقِينَ*