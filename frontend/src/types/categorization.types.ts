/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * TypeScript Type Contracts for Reconciliation Frontend Enhancements
 * Feature: 001-reconciliation-frontend-features
 *
 * This file defines all TypeScript interfaces, enums, and types required
 * for implementing transaction categorization and manual reconciliation features.
 *
 * These contracts extend the existing reconciliation.types.ts and maintain
 * type safety across the full frontend implementation.
 */

// ============================================================================
// IMPORTS
// ============================================================================

import { DiscrepancyTransaction } from './reconciliation.types';

// ============================================================================
// ENUMS
// ============================================================================

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Transaction categorization into four accounting-specific sections
 *
 * Categories are determined by transaction source (Bank/Company) and
 * value polarity (positive/negative) according to accounting conventions.
 */
export enum TransactionCategory {
  /** Company records with negative values - checks issued but not yet presented to bank */
  UNPRESENTED_CHECKS = "UNPRESENTED CHECKS",

  /** Company records with positive values - checks received but not yet cleared */
  UNCLEARED_CHECKS = "UNCLEARED CHECKS",

  /** Bank statement entries with positive values (credit, money in) - not recorded in company cash book */
  BANK_CREDITED_NOT_DEBITED = "BANK CREDITED BUT NOT DEBITED IN CASH BOOK",

  /** Bank statement entries with negative values (debit, money out) - not recorded in company cash book */
  BANK_DEBITED_NOT_CREDITED = "BANK DEBITED BUT NOT CREDITED IN CASH BOOK"
}

// ============================================================================
// INTERFACES
// ============================================================================

/**
 * Extended transaction model with category assignment and display formatting
 * Extends the base DiscrepancyTransaction from reconciliation.types.ts
 */
export interface CategorizedTransaction extends DiscrepancyTransaction {
  /** Transaction date in YYYY-MM-DD format */
  'Transaction_date': string;

  /** Transaction description/details */
  'Transaction Detail': string;

  /** Raw amount with sign (positive for credit, negative for debit) */
  'Debit/Credit': number;

  /** Source identifier: 'Bank' or 'Company' */
  'FROM': 'Bank' | 'Company';

  /** Determined category based on source and value */
  category: TransactionCategory;

  /** Unique identifier for selection tracking */
  itemId: string;

  /** Display amount (Bank amounts inverted per existing convention) */
  displayAmount: number;

  /** Formatted PKR currency string for display (e.g., "+PKR 40,771.70", "-PKR 17,929.40") */
  displayValue: string;
}

/**
 * State management interface for manual reconciliation selection tracking
 * Represents the React component state for user selections and calculations
 */
export interface DiscrepancySelectionState {
  /** Set of itemIds currently selected for manual reconciliation */
  selectedItems: Set<string>;

  /** Transactions organized by category into four sections */
  categories: {
    [key in TransactionCategory]: CategorizedTransaction[];
  };

  /** Calculation preview showing sum and status of selected items */
  calculation: ReconciliationCalculation;
}

/**
 * Calculation preview data for manual reconciliation confirmation
 * Displayed above the Manual Reconciliation Button
 */
export interface ReconciliationCalculation {
  /** Sum of all selected transaction values (can be positive, negative, or zero) */
  totalAmount: number;

  /** Number of items currently selected */
  itemCount: number;

  /** Whether the sum equals zero (within floating point tolerance) */
  isNetZero: boolean;

  /** Human-readable summary of the calculation */
  summary: string;
}

/**
 * Configuration options for categorization behavior
 * Allows customization of categorization rules if needed in future
 */
export interface CategorizationConfig {
  /** Whether to handle zero-value transactions specially */
  handleZeroValues: boolean;

  /** Default category for zero-value transactions (if handleZeroValues is true) */
  zeroValueCategory: TransactionCategory;

  /** Floating point tolerance for net-zero detection in calculations */
  netZeroTolerance: number;
}

// ============================================================================
// TYPE ALIASES & UTILITIES
// ============================================================================

/**
 * Category transaction map type for organized data structure
 */
export type CategoryTransactionMap = {
  [key in TransactionCategory]: CategorizedTransaction[];
};

/**
 * Selection callback type for checkbox onChange handlers
 */
export type SelectionToggleCallback = (itemId: string) => void;

/**
 * Manual reconciliation execution callback type
 */
export type ReconciliationExecutionCallback = () => void | Promise<void>;

// ============================================================================
// TYPE GUARDS
// ============================================================================

/**
 * Type guard to check if a transaction belongs to a specific category
 */
export function isTransactionInCategory(
  transaction: CategorizedTransaction,
  category: TransactionCategory
): boolean {
  return transaction.category === category;
}

/**
 * Type guard to check if reconciliation calculation is net zero
 */
export function isNetZeroCalculation(calculation: ReconciliationCalculation): boolean {
  return calculation.isNetZero && calculation.itemCount > 0;
}

/**
 * Type guard to check if manual reconciliation can be executed
 */
export function canExecuteReconciliation(state: DiscrepancySelectionState): boolean {
  return state.calculation.itemCount > 0;
}

// ============================================================================
// DEFAULT EXPORTS
// ============================================================================

/**
 * Default categorization configuration
 * Follows specification requirements exactly
 */
export const DEFAULT_CATEGORIZATION_CONFIG: CategorizationConfig = {
  handleZeroValues: true,
  zeroValueCategory: TransactionCategory.UNPRESENTED_CHECKS,  // Company + Negative
  netZeroTolerance: 0.01  // Allows for floating point precision issues
};

/**
 * Default empty selection state
 * Used for initializing or resetting reconciliation state
 */
export const EMPTY_SELECTION_STATE: DiscrepancySelectionState = {
  selectedItems: new Set<string>(),
  categories: {
    [TransactionCategory.UNPRESENTED_CHECKS]: [],
    [TransactionCategory.UNCLEARED_CHECKS]: [],
    [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: [],
    [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: []
  },
  calculation: {
    totalAmount: 0,
    itemCount: 0,
    isNetZero: false,
    summary: "No items selected"
  }
};

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ