/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Categorization Utilities for Reconciliation Frontend Enhancements
 * Feature: 001-reconciliation-frontend-features
 *
 * This file provides utility functions for transaction categorization,
 * unique identifier generation, and display amount formatting.
 */

import { TransactionCategory } from '@/types/categorization.types';

// ============================================================================
// CATEGORIZATION LOGIC
// ============================================================================

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Categorize a transaction based on its source, value, and reconciliation type.
 *
 * For "bank" mode, the source is the bank statement (Credit +, Debit -).
 * For "vendor" mode, the source is the vendor ledger (Debit +, Credit -).
 *
 * @param source - The transaction source ('Bank' or 'Company')
 * @param value - The transaction value (positive for credit, negative for debit)
 * @param reconciliationType - "bank" (default) or "vendor"
 * @returns The appropriate TransactionCategory enum value
 */
export function categorizeTransaction(
  source: string,
  value: number,
  reconciliationType: 'bank' | 'vendor' = 'bank'
): TransactionCategory {
  const isSource = source === 'Bank';
  const isPositive = value > 0;

  if (reconciliationType === 'vendor') {
    // Vendor ledger: Credit is -, Debit is + (inverted vs a bank statement).
    // A source-side entry that is positive = debited (money the vendor paid
    // out / you owe) but not credited in the cash book; a negative one =
    // credited (money the vendor received) but not debited.
    if (isSource && isPositive) {
      return TransactionCategory.VENDOR_DEBITED_NOT_CREDITED;
    }
    if (isSource && !isPositive) {
      return TransactionCategory.VENDOR_CREDITED_NOT_DEBITED;
    }
    if (!isSource && isPositive) {
      return TransactionCategory.UNCLEARED_CHECKS;
    }
    return TransactionCategory.UNPRESENTED_CHECKS;
  }

  if (isSource && isPositive) {
    // Bank credit (money in) — not recorded in company cash book
    return TransactionCategory.BANK_CREDITED_NOT_DEBITED;
  }
  if (isSource && !isPositive) {
    // Bank debit (money out) — not recorded in company cash book
    return TransactionCategory.BANK_DEBITED_NOT_CREDITED;
  }
  if (!isSource && isPositive) {
    return TransactionCategory.UNCLEARED_CHECKS;
  }
  return TransactionCategory.UNPRESENTED_CHECKS;  // Company + Negative
}

// ============================================================================
// IDENTIFIER GENERATION
// ============================================================================

/**
 * Generate a unique identifier for a transaction
 * Format: {date}-{source}-{value}-{index}
 *
 * @param transactionDate - The transaction date in YYYY-MM-DD format
 * @param source - The transaction source ('Bank' or 'Company')
 * @param value - The transaction value
 * @param index - The transaction index to ensure uniqueness
 * @returns A unique itemId string
 */
export function generateItemId(
  transactionDate: string,
  source: string,
  value: number,
  index: number
): string {
  return `${transactionDate}-${source}-${value}-${index}`;
}

// ============================================================================
// DISPLAY FORMATTING
// ============================================================================

/**
 * Get the display amount for a transaction with enforced sign convention
 *
 * Sign convention per category:
 *   - UNPRESENTED_CHECKS:  always negative (Company debits not yet presented)
 *   - UNCLEARED_CHECKS:    always positive (Company credits not yet cleared)
 *   - BANK_CREDITED_NOT_DEBITED: always negative (Bank credits not in cash book)
 *   - BANK_DEBITED_NOT_CREDITED: always positive (Bank debits not in cash book)
 *
 * @param source - The transaction source ('Bank' or 'Company')
 * @param rawAmount - The raw transaction value
 * @param category - The transaction category for sign enforcement
 * @returns The display amount with enforced sign convention
 */
export function getDisplayAmount(
  source: string,
  rawAmount: number,
  category?: TransactionCategory,
  reconciliationType: 'bank' | 'vendor' = 'bank'
): number {
  if (category) {
    switch (category) {
      case TransactionCategory.UNPRESENTED_CHECKS:
      case TransactionCategory.BANK_CREDITED_NOT_DEBITED:
      case TransactionCategory.VENDOR_CREDITED_NOT_DEBITED:
        return -Math.abs(rawAmount);       // Always negative
      case TransactionCategory.UNCLEARED_CHECKS:
      case TransactionCategory.BANK_DEBITED_NOT_CREDITED:
      case TransactionCategory.VENDOR_DEBITED_NOT_CREDITED:
        return Math.abs(rawAmount);         // Always positive
    }
  }
  return rawAmount;  // Fallback: unchanged
}

/**
 * Resolve the display label for a category under the active reconciliation
 * mode. In "vendor" mode the Bank-side categories are replaced with their
 * vendor equivalents (a vendor ledger's debit/credit roles are inverted).
 */
export function categoryLabel(
  category: TransactionCategory,
  reconciliationType: 'bank' | 'vendor' = 'bank'
): string {
  if (reconciliationType === 'vendor') {
    switch (category) {
      case TransactionCategory.BANK_CREDITED_NOT_DEBITED:
        return TransactionCategory.VENDOR_CREDITED_NOT_DEBITED;
      case TransactionCategory.BANK_DEBITED_NOT_CREDITED:
        return TransactionCategory.VENDOR_DEBITED_NOT_CREDITED;
      default:
        return category;
    }
  }
  return category;
}

/**
 * Format an amount as a PKR currency string with sign
 * Uses Pakistani Rupee (PKR) with '+' or '-' prefix
 *
 * @param amount - The amount to format
 * @returns Formatted currency string (e.g., "+PKR 40,771.70", "-PKR 17,929.40")
 */
export function formatAmount(amount: number): string {
  const formatted = Math.abs(amount).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return amount >= 0 ? `+PKR ${formatted}` : `-PKR ${formatted}`;
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ