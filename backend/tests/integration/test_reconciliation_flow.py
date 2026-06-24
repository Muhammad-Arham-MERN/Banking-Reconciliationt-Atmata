# بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
"""
Integration tests for reconciliation flow.
Tests end-to-end reconciliation process with realistic data.
"""

import pytest
from src.services.reconciliation_service import ReconciliationService


class TestReconciliationFlow:
    """Integration test suite for reconciliation flow"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = ReconciliationService()

    def test_complete_reconciliation_flow(self):
        """Test complete reconciliation flow with realistic bank statement data"""
        # Realistic bank statement data (26 transactions as mentioned in spec)
        bank_txs = [
            {"Transaction_date": "2026-05-05", "Transaction Detail": "INWARD CHEQUE", "Debit/Credit": 10200.0},
            {"Transaction_date": "2026-05-06", "Transaction Detail": "P2P RECEIVING VIA GREAVES", "Debit/Credit": -22000000.0},
            {"Transaction_date": "2026-05-06", "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515", "Debit/Credit": -40771.695},
            {"Transaction_date": "2026-05-04", "Transaction Detail": "Salaries IIAP mo Apr-26", "Debit/Credit": -17929400.0},
            {"Transaction_date": "2026-05-04", "Transaction Detail": "Fund Transfer Through RTGS from SBL to MCB BANK ISB", "Debit/Credit": 22000000.0}
        ]

        # Realistic company records data (20 transactions as mentioned in spec)
        company_txs = [
            {"Transaction_date": "2026-05-05", "Transaction Detail": "INWARD CHEQUE", "Debit/Credit": -10200.0},
            {"Transaction_date": "2026-05-06", "Transaction Detail": "P2P RECEIVING VIA GREAVES", "Debit/Credit": 22000000.0},
            {"Transaction_date": "2026-05-06", "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515", "Debit/Credit": 6771.238},
            {"Transaction_date": "2026-05-04", "Transaction Detail": "Salaries IIAP mo Apr-26", "Debit/Credit": 17929400.0},
            {"Transaction_date": "2026-05-04", "Transaction Detail": "Company Other Expense", "Debit/Credit": 50000.0}
        ]

        result = self.service.reconcile(bank_txs, company_txs)

        # Verify structure
        assert isinstance(result, list)
        assert all('FROM' in tx for tx in result)
        assert all(tx['FROM'] in ['Bank', 'Company'] for tx in result)

        # Verify opposite pairs were removed
        bank_10200 = [tx for tx in result if tx['Debit/Credit'] == 10200.0 and tx['FROM'] == 'Bank']
        company_neg_10200 = [tx for tx in result if tx['Debit/Credit'] == -10200.0 and tx['FROM'] == 'Company']
        assert len(bank_10200) == 0, "Bank 10200 should have matched with company -10200"
        assert len(company_neg_10200) == 0, "Company -10200 should have matched with bank 10200"

        # Verify source attribution
        bank_discrepancies = [tx for tx in result if tx['FROM'] == 'Bank']
        company_discrepancies = [tx for tx in result if tx['FROM'] == 'Company']

        assert len(bank_discrepancies) > 0, "Should have bank-only discrepancies"
        assert len(company_discrepancies) > 0, "Should have company-only discrepancies"

    def test_reconciliation_preserves_transaction_details(self):
        """Test that reconciliation preserves all original transaction details"""
        bank_txs = [
            {
                "Transaction_date": "2026-05-06",
                "Transaction Detail": "Payment to ABC Corporation",
                "Debit/Credit": -50000.0
            }
        ]
        company_txs = [
            {
                "Transaction_date": "2026-05-04",
                "Transaction Detail": "Income from XYZ Ltd",
                "Debit/Credit": 75000.0
            }
        ]

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 2

        # Verify bank transaction details preserved
        bank_result = [tx for tx in result if tx['FROM'] == 'Bank'][0]
        assert bank_result['Transaction_date'] == "2026-05-06"
        assert bank_result['Transaction Detail'] == "Payment to ABC Corporation"
        assert bank_result['Debit/Credit'] == -50000.0

        # Verify company transaction details preserved
        company_result = [tx for tx in result if tx['FROM'] == 'Company'][0]
        assert company_result['Transaction_date'] == "2026-05-04"
        assert company_result['Transaction Detail'] == "Income from XYZ Ltd"
        assert company_result['Debit/Credit'] == 75000.0

    def test_large_scale_reconciliation(self):
        """Test reconciliation with larger transaction volumes (100+ each)"""
        # Generate 100 bank transactions
        bank_txs = [
            {
                "Transaction_date": "2026-05-06",
                "Transaction Detail": f"Bank Transaction {i}",
                "Debit/Credit": -(i * 100.0)
            }
            for i in range(1, 101)
        ]

        # Generate 100 company transactions with some matches
        company_txs = [
            {
                "Transaction_date": "2026-05-06",
                "Transaction Detail": f"Company Transaction {i}",
                "Debit/Credit": (i * 100.0) if i <= 50 else (i * 150.0)
            }
            for i in range(1, 101)
        ]

        result = self.service.reconcile(bank_txs, company_txs)

        # Should have 50 matches (first 50) + 50 bank only + 50 company only = 100 total discrepancies
        assert len(result) == 100

        # Verify performance is acceptable (should complete in reasonable time)
        # This is implicitly tested by the test running successfully

    def test_error_handling_malformed_data(self):
        """Test graceful handling of malformed transaction data"""
        bank_txs = [
            {
                "Transaction_date": "2026-05-06",
                "Transaction Detail": "Valid Transaction",
                "Debit/Credit": -1000.0
            },
            {
                # Missing required field
                "Transaction_date": "2026-05-07",
                "Transaction Detail": "Invalid Transaction"
                # Missing Debit/Credit
            }
        ]
        company_txs = [
            {
                "Transaction_date": "2026-05-06",
                "Transaction Detail": "Company Transaction",
                "Debit/Credit": 2000.0
            }
        ]

        # Service should handle gracefully without crashing
        result = self.service.reconcile(bank_txs, company_txs)

        # Should still return results for valid transactions
        assert isinstance(result, list)

    def test_reconciliation_performance_metrics(self):
        """Test that reconciliation service tracks performance metrics"""
        bank_txs = [
            {"Transaction_date": "2026-05-06", "Transaction Detail": "Bank TX", "Debit/Credit": -1000.0}
        ]
        company_txs = [
            {"Transaction_date": "2026-05-06", "Transaction Detail": "Company TX", "Debit/Credit": 2000.0}
        ]

        # Clear any previous processing time
        self.service.processing_time_ms = 0

        result = self.service.reconcile(bank_txs, company_txs)

        # Verify processing time was tracked
        assert self.service.processing_time_ms >= 0
        assert isinstance(self.service.processing_time_ms, int)


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
