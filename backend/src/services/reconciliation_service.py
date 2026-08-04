# بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
"""
Bank reconciliation service implementing amount-based transaction comparison.
Core reconciliation logic with deterministic behavior and opposite sign removal.
"""

from typing import List, Dict, Any
import time
from decimal import Decimal, ROUND_HALF_UP

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

        # Shared 1:1 consumption tracking: a bank entry that matches a company
        # entry consumes that company entry, and vice versa. Each entry can
        # only be consumed once, so a single amount is never reused to cancel
        # multiple rows on the other side. When a pair is found, both members
        # are removed together.
        company_used = [False] * len(company_transactions)
        bank_used = [False] * len(bank_transactions)

        # Find discrepancies from both sources
        bank_discrepancies = self._find_bank_discrepancies(bank_transactions, company_transactions, company_used, bank_used)
        company_discrepancies = self._find_company_discrepancies(company_transactions, bank_transactions, company_used, bank_used)

        # Remove opposite sign pairs
        final_discrepancies = self._remove_opposite_pairs(bank_discrepancies, company_discrepancies)

        self.processing_time_ms = int((time.time() - start_time) * 1000)
        return final_discrepancies

    def _find_bank_discrepancies(self,
                                bank_transactions: List[Dict[str, Any]],
                                company_transactions: List[Dict[str, Any]],
                                company_used: List[bool],
                                bank_used: List[bool]) -> List[Dict[str, Any]]:
        """
        Find bank transactions that don't have a matching amount in company records.
        Matching based ONLY on amount: bank_amount == company_amount.
        When a match is found, the company entry is marked as consumed so it is
        removed together with this bank entry and cannot be reused.
        """
        discrepancies = []

        for b_idx, bank_tx in enumerate(bank_transactions):
            matched = False
            bank_amount = bank_tx.get('Debit/Credit', 0.0)

            # Look for matching amount in company transactions
            for i, company_tx in enumerate(company_transactions):
                if company_used[i]:
                    continue  # Already consumed by a previous pair
                company_amount = company_tx.get('Debit/Credit', 0.0)

                if self._amounts_match(bank_amount, company_amount):
                    company_used[i] = True  # Consume the company entry (pair removed)
                    bank_used[b_idx] = True  # Consume this bank entry too
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
                                   bank_transactions: List[Dict[str, Any]],
                                   company_used: List[bool],
                                   bank_used: List[bool]) -> List[Dict[str, Any]]:
        """
        Find company transactions that don't have a matching amount in bank statement.
        Matching based ONLY on amount: company_amount == bank_amount.
        Entries already consumed by a bank pair are skipped, so the bank entry
        is never reused to cancel multiple company rows.
        """
        discrepancies = []

        for i, company_tx in enumerate(company_transactions):
            if company_used[i]:
                continue  # Already removed together with its bank pair
            matched = False
            company_amount = company_tx.get('Debit/Credit', 0.0)

            # Look for matching amount in bank transactions
            for b_idx, bank_tx in enumerate(bank_transactions):
                if bank_used[b_idx]:
                    continue  # Already consumed by a previous pair
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

    def _round_amount(self, amount: float) -> int:
        """
        Round amount to nearest whole number for comparison.
        Handles decimal differences between bank and company sources
        (e.g. -40771.695 vs -40772.00 both become -40772).
        """
        try:
            return int(Decimal(str(amount)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        except (ValueError, TypeError):
            return 0

    def _amounts_match(self, amount1: float, amount2: float) -> bool:
        """
        Check if two amounts match after rounding to whole numbers.
        Original values are preserved in discrepancy output.
        """
        return self._round_amount(amount1) == self._round_amount(amount2)

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


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
