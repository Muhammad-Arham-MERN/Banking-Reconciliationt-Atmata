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
 * The wire `Debit/Credit` value carries the pure source-specific convention
 * (no flips):
 *   - Bank:    Credit = positive, Debit = negative
 *   - Company: Credit = negative, Debit = positive
 *   - Vendor:  Credit = negative, Debit = positive
 *
 * Categorization:
 *   - Bank + (credit)      -> BANK_CREDITED_NOT_DEBITED
 *   - Bank - (debit)       -> BANK_DEBITED_NOT_CREDITED
 *   - Company - (credit)   -> UNPRESENTED_CHECKS
 *   - Company + (debit)    -> UNCLEARED_CHECKS
 *   - Vendor + (debit)     -> VENDOR_DEBITED_NOT_CREDITED
 *   - Vendor - (credit)    -> VENDOR_CREDITED_NOT_DEBITED
 *
 * @param source - The transaction source ('Bank' or 'Company')
 * @param value - The transaction value (source-specific signed amount)
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
    // Vendor ledger: Credit is -, Debit is + (its own convention, not a
    // bank-statement inversion). A source-side entry that is positive =
    // debited (money the vendor paid out / you owe) but not credited in the
    // cash book; a negative one = credited (money the vendor received) but
    // not debited.
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
 * Get the display amount for a transaction.
 *
 * The wire `Debit/Credit` value already carries the pure source-specific
 * convention end-to-end, with NO sign flips anywhere:
 *   - Bank:    Credit = positive, Debit = negative
 *   - Company: Credit = negative, Debit = positive
 *   - Vendor:  Credit = negative, Debit = positive
 * The display therefore shows the raw value as-is.
 *
 * @param source - The transaction source ('Bank' or 'Company')
 * @param rawAmount - The raw transaction value
 * @param category - The transaction category (unused for sign; kept for API compat)
 * @returns The display amount (the raw wire value)
 */
export function getDisplayAmount(
  source: string,
  rawAmount: number,
  category?: TransactionCategory,
  reconciliationType: 'bank' | 'vendor' = 'bank'
): number {
  return rawAmount;
}

/**
 * Resolve the display label for a category under the active reconciliation
 * mode. In "vendor" mode the Bank-side categories are replaced with their
 * vendor equivalents (a vendor ledger has its own debit/credit convention).
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