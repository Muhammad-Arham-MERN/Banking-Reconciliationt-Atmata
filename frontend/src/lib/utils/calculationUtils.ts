/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Calculation Utilities for Manual Reconciliation
 * Feature: 001-reconciliation-frontend-features
 *
 * This file provides utility functions for calculating reconciliation previews,
 * formatting calculation summaries, and managing selection state.
 */

import { CategorizedTransaction, ReconciliationCalculation } from '@/types/categorization.types';

// ============================================================================
// CALCULATION PREVIEW
// ============================================================================

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Calculate the reconciliation preview for selected transactions
 *
 * @param selectedItems - Set of selected itemIds
 * @param transactions - All available transactions
 * @returns ReconciliationCalculation object with preview data
 */
export function calculateReconciliationPreview(
  selectedItems: Set<string>,
  transactions: CategorizedTransaction[]
): ReconciliationCalculation {
  const selected = transactions.filter(t => selectedItems.has(t.itemId));
  const totalAmount = selected.reduce((sum, t) => sum + t.displayAmount, 0);
  const itemCount = selected.length;
  const isNetZero = Math.abs(totalAmount) < 0.01;  // Floating point tolerance

  return {
    totalAmount,
    itemCount,
    isNetZero,
    summary: formatCalculationSummary(totalAmount, itemCount)
  };
}

// ============================================================================
// SUMMARY FORMATTING
// ============================================================================

/**
 * Format a human-readable summary of the calculation
 *
 * @param totalAmount - The sum of all selected transaction values
 * @param itemCount - The number of selected items
 * @returns A formatted summary string
 */
export function formatCalculationSummary(totalAmount: number, itemCount: number): string {
  if (itemCount === 0) {
    return "No items selected";
  }

  const formattedAmount = formatAmount(totalAmount);
  const itemWord = itemCount === 1 ? 'item' : 'items';

  if (Math.abs(totalAmount) < 0.01) {
    return `Net zero (${itemCount} ${itemWord} selected)`;
  }

  return `${formattedAmount} (${itemCount} ${itemWord} selected)`;
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

// ============================================================================
// STATE MANAGEMENT HELPERS
// ============================================================================

/**
 * Toggle an item in a Set (add if not present, remove if present)
 *
 * @param currentSet - The current Set of itemIds
 * @param itemId - The itemId to toggle
 * @returns A new Set with the item toggled
 */
export function toggleItemInSet(currentSet: Set<string>, itemId: string): Set<string> {
  const next = new Set(currentSet);
  if (next.has(itemId)) {
    next.delete(itemId);
  } else {
    next.add(itemId);
  }
  return next;
}

/**
 * Clear all selections by creating a new empty Set
 *
 * @returns A new empty Set
 */
export function clearSelections(): Set<string> {
  return new Set<string>();
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ