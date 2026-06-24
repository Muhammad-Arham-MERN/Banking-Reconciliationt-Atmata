# بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
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

    def test_matching_amount_removal(self):
        """Test that matching amount pairs are correctly removed"""
        bank_txs = [{"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Test"}]
        company_txs = [{"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Test"}]

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 0, "Matching amount pairs should be removed"

    def test_bank_only_discrepancy(self):
        """Test bank-only transaction is identified"""
        bank_txs = [{"Debit/Credit": -200.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Bank Only"}]
        company_txs = []

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 1
        assert result[0]['Debit/Credit'] == -200.0
        assert result[0]['FROM'] == 'Bank'

    def test_company_only_discrepancy(self):
        """Test company-only transaction is identified"""
        bank_txs = []
        company_txs = [{"Debit/Credit": -200.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Company Only"}]

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 1
        assert result[0]['Debit/Credit'] == -200.0
        assert result[0]['FROM'] == 'Company'

    def test_deterministic_behavior(self):
        """Test that same inputs produce same outputs"""
        bank_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "First"},
            {"Debit/Credit": -200.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Second"}
        ]
        company_txs = [{"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Match"}]

        result1 = self.service.reconcile(bank_txs, company_txs)
        result2 = self.service.reconcile(bank_txs, company_txs)

        assert result1 == result2, "Results should be deterministic"

    def test_empty_transaction_lists(self):
        """Test handling of empty transaction lists"""
        bank_txs = []
        company_txs = []

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 0
        assert isinstance(result, list)

    def test_multiple_matching_pairs(self):
        """Test removal of multiple matching amount pairs"""
        bank_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "First"},
            {"Debit/Credit": -200.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Second"}
        ]
        company_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Match1"},
            {"Debit/Credit": -200.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Match2"}
        ]

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 0, "All matching pairs should be removed"

    def test_partial_matching(self):
        """Test scenario with some matching and some non-matching transactions"""
        bank_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Match"},
            {"Debit/Credit": -300.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Bank Only"}
        ]
        company_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Match"},
            {"Debit/Credit": -400.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Company Only"}
        ]

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 2
        bank_discrepancies = [d for d in result if d['FROM'] == 'Bank']
        company_discrepancies = [d for d in result if d['FROM'] == 'Company']
        assert len(bank_discrepancies) == 1
        assert len(company_discrepancies) == 1

    def test_rounded_decimal_matching(self):
        """Test that decimal precision differences match after rounding"""
        bank_txs = [{"Debit/Credit": -40772.0, "Transaction_date": "2026-05-14", "Transaction Detail": "INWARD CHEQUE"}]
        company_txs = [{"Debit/Credit": -40771.695, "Transaction_date": "2026-05-06", "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515"}]

        result = self.service.reconcile(bank_txs, company_txs)

        assert len(result) == 0, "Rounded amounts should match"

    def test_duplicate_amounts_handling(self):
        """Test handling of duplicate amounts in same source"""
        bank_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "First"},
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Second"}
        ]
        company_txs = [
            {"Debit/Credit": -100.0, "Transaction_date": "2026-05-05", "Transaction Detail": "Match"},
            {"Debit/Credit": -300.0, "Transaction_date": "2026-05-06", "Transaction Detail": "Company Only"}
        ]

        result = self.service.reconcile(bank_txs, company_txs)

        # One bank -100 matches company -100; company -300 is unmatched
        assert len(result) == 1
        assert result[0]['FROM'] == 'Company'
        assert result[0]['Debit/Credit'] == -300.0


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
