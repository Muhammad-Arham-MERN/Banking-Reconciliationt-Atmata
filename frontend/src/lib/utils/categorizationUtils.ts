/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Categorization Utilities for Reconciliation Frontend Enhancements
 * Feature: 001-reconciliation-frontend-features
 *
 * This file provides utility functions for transaction categorization,
 * unique identifier generation, and display amount formatting.
 */

import { TransactionCategory } from '@/types/categorization.types';

// NOTE (legacy data): reconciliations saved before this sign convention was
// finalized were written with the OLD bank/vendor polarity (bank credit +/
// debit -, vendor debit +/credit -). They are not backfilled — the original
// source polarity cannot be reconstructed — so a legacy saved file/export
// renders its stored values as-is; re-running the reconciliation regenerates it
// under the finalized convention (contracts/sign-convention.md §5).

// ============================================================================
// CATEGORIZATION LOGIC
// ============================================================================

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Categorize a transaction based on its source, value, and reconciliation type.
 *
 * Finalized canonical wire convention (contracts/sign-convention.md §2), with
 * NO per-surface flips:
 *   - Bank:    Debit = positive, Credit = negative
 *   - Company: Debit = positive, Credit = negative
 *   - Vendor:  Debit = negative, Credit = positive
 * (source "Bank" carries the vendor ledger's rows in vendor mode.)
 *
 * Categorization:
 *   - Bank + (debit)       -> BANK_DEBITED_NOT_CREDITED
 *   - Bank - (credit)      -> BANK_CREDITED_NOT_DEBITED
 *   - Company - (credit)   -> UNPRESENTED_CHECKS
 *   - Company + (debit)    -> UNCLEARED_CHECKS
 *   - Vendor + (credit)    -> VENDOR_CREDITED_NOT_DEBITED
 *   - Vendor - (debit)     -> VENDOR_DEBITED_NOT_CREDITED
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
    // Vendor ledger: Credit is + and Debit is - (its own convention). A
    // positive source-side entry = credited (money the vendor received) but
    // not debited in the cash book; a negative one = debited but not credited.
    if (isSource && isPositive) {
      return TransactionCategory.VENDOR_CREDITED_NOT_DEBITED;
    }
    if (isSource && !isPositive) {
      return TransactionCategory.VENDOR_DEBITED_NOT_CREDITED;
    }
    if (!isSource && isPositive) {
      return TransactionCategory.UNCLEARED_CHECKS;
    }
    return TransactionCategory.UNPRESENTED_CHECKS;
  }

  if (isSource && isPositive) {
    // Bank debit (money out) — not recorded in company cash book
    return TransactionCategory.BANK_DEBITED_NOT_CREDITED;
  }
  if (isSource && !isPositive) {
    // Bank credit (money in) — not recorded in company cash book
    return TransactionCategory.BANK_CREDITED_NOT_DEBITED;
  }
  if (!isSource && isPositive) {
    return TransactionCategory.UNCLEARED_CHECKS;
  }
  return TransactionCategory.UNPRESENTED_CHECKS;  // Company credit (negative)
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
 * The wire `Debit/Credit` value already carries the finalized canonical
 * convention end-to-end, with NO sign flips anywhere
 * (contracts/sign-convention.md §2):
 *   - Bank:    Debit = positive, Credit = negative
 *   - Company: Debit = positive, Credit = negative
 *   - Vendor:  Debit = negative, Credit = positive
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
 * mode. In "vendor" mode the Bank-side category SLOTS are mapped to their
 * vendor equivalents (a vendor ledger occupies the same credited/debited
 * slots, though its debit/credit polarity is inverted), and the two company
 * slots are renamed to the vendor-facing wording:
 *   - Unpresented Checks -> "Invoices Not Recorded by Vendor"
 *   - Uncleared Checks   -> "Payment Not Recorded by Vendor"
 */
export function categoryLabel(
  category: TransactionCategory,
  reconciliationType: 'bank' | 'vendor' = 'bank'
): string {
  if (reconciliationType === 'vendor') {
    switch (category) {
      case TransactionCategory.UNPRESENTED_CHECKS:
        return 'INVOICES NOT RECORDED BY VENDOR';
      case TransactionCategory.UNCLEARED_CHECKS:
        return 'PAYMENT NOT RECORDED BY VENDOR';
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