# بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
"""
Bank reconciliation service implementing amount-based transaction comparison.
Core reconciliation logic with deterministic behavior and opposite sign removal.
"""

from typing import List, Dict, Any, Tuple
import time
from decimal import Decimal, ROUND_HALF_UP

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

# Margin of error relief (in rupees) applied by the pair-mate filter when
# comparing two amounts after whole-rupee rounding.
PAIR_MATE_MARGIN = 1.0


class ReconciliationService:
    """Service for bank statement and company records reconciliation"""

    def __init__(self):
        self.processing_time_ms = 0
        self.pair_mate_pairs_removed = 0

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

        # Layer 1 (sam-sam leftovers): remove opposite sign pairs across sources
        bank_discrepancies, company_discrepancies = self._remove_opposite_pairs(
            bank_discrepancies, company_discrepancies
        )

        # Layer 2 (pair-mate): cancel same-date opposite-sign pairs within each source
        bank_discrepancies, company_discrepancies, pair_mate_pairs = self._remove_pair_mate_pairs(
            bank_discrepancies, company_discrepancies
        )
        self.pair_mate_pairs_removed = pair_mate_pairs

        final_discrepancies = bank_discrepancies + company_discrepancies

        # وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
        # Assign a stable, backend-generated key to every final discrepancy
        # (FR-002, AI Reconciler Advisor feature 007). The key is
        # "<FROM>:<n>" with <n> the 1-based positional index over the final
        # assembled list (Bank items first, then Company items, matching the
        # final array order). Deterministic for the same inputs, collision-free
        # across both sources, and never rendered in the frontend UI — it exists
        # so the Reconciler Agent can reference exact items and the frontend can
        # resolve them against the live main list.
        counters: Dict[str, int] = {}
        for discrepancy in final_discrepancies:
            source = discrepancy.get("FROM", "Bank")
            counters[source] = counters.get(source, 0) + 1
            discrepancy["discrepancy_id"] = f"{source}:{counters[source]}"

        self.processing_time_ms = int((time.time() - start_time) * 1000)
        return final_discrepancies

    def compute_balance_context(self, discrepancies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute the cumulative Bank-vs-Company running totals over the final
        discrepancy list (FR-002b, AI Reconciler Advisor feature 007).

        Each discrepancy's signed Debit/Credit (negative = debit, positive =
        credit) is added to its own FROM bucket only; every item produces a
        BalancePoint (index, discrepancy_id, bank_running, company_running,
        net = bank_running + company_running) in list order, plus the final
        bank_balance / company_balance summary totals. The Reconciler Agent
        uses this as a supporting mathematical check and MUST NOT propose a
        suggestion whose sums break these running totals.
        """
        bank_running = 0.0
        company_running = 0.0
        points = []

        for index, discrepancy in enumerate(discrepancies, start=1):
            amount = discrepancy.get("Debit/Credit", 0.0)
            source = discrepancy.get("FROM", "Bank")
            if source == "Company":
                company_running += amount
            else:
                bank_running += amount
            points.append(
                {
                    "index": index,
                    "discrepancy_id": discrepancy.get("discrepancy_id", ""),
                    "bank_running": bank_running,
                    "company_running": company_running,
                    "net": bank_running + company_running,
                }
            )

        return {
            "points": points,
            "bank_balance": bank_running,
            "company_balance": company_running,
        }

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
                              company_discrepancies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Remove opposite sign pairs from discrepancy lists.
        Maintains deterministic order and preserves source attribution.
        Returns the filtered bank and company discrepancy lists separately.
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

        return filtered_bank, filtered_company

    def _pair_mate_amounts_match(self, amount1: float, amount2: float) -> bool:
        """
        Check if two amounts match after rounding to whole numbers,
        with a 1 Rs margin of error relief. Compares magnitudes, since
        pair-mate only matches strictly opposite-sign entries.
        """
        return abs(
            self._round_amount(abs(amount1)) - self._round_amount(abs(amount2))
        ) <= PAIR_MATE_MARGIN

    def _remove_pair_mate_pairs(self,
                                bank_discrepancies: List[Dict[str, Any]],
                                company_discrepancies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
        """
        Pair-mate filter: within each source separately, cancel same-date,
        strictly opposite-sign, equal-amount (with 1 Rs margin) pairs.
        Each entry can be consumed at most once (1:1 semantics).
        Returns the filtered bank and company lists plus the number of
        pairs removed.
        """
        filtered_bank, pairs_bank = self._filter_pair_mate_within(bank_discrepancies)
        filtered_company, pairs_company = self._filter_pair_mate_within(company_discrepancies)
        return filtered_bank, filtered_company, pairs_bank + pairs_company

    def _filter_pair_mate_within(self,
                                 discrepancies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Cancel same-date opposite-sign pairs within a single discrepancy list.
        Preserves the original order of the surviving entries.
        """
        used = [False] * len(discrepancies)
        remaining = []
        pairs = 0

        for i, tx in enumerate(discrepancies):
            if used[i]:
                continue
            amount = tx.get('Debit/Credit', 0.0)
            date = tx.get('Transaction_date')
            partner = None

            for j in range(i + 1, len(discrepancies)):
                if used[j]:
                    continue
                other = discrepancies[j]
                # Same date + strictly opposite signs + equal amount (1 Rs margin)
                if (
                    date is not None
                    and date == other.get('Transaction_date')
                    and amount * other.get('Debit/Credit', 0.0) < 0
                    and self._pair_mate_amounts_match(amount, other.get('Debit/Credit', 0.0))
                ):
                    partner = j
                    break

            if partner is not None:
                used[i] = True
                used[partner] = True
                pairs += 1
            else:
                remaining.append(tx)

        return remaining, pairs


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
