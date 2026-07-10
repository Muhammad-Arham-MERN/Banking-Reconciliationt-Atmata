/**
 * TypeScript types for reconciliation data structures
 * Bank Reconciliation System
 */

// Bank Transaction Interface
export interface BankTransaction {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
}

// Company Transaction Interface
export interface CompanyTransaction {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
}

// Discrepancy Transaction Interface
export interface DiscrepancyTransaction {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
  'FROM': 'Bank' | 'Company';
  'from_past'?: boolean;
}

// Reconciliation Summary Interface
export interface ReconciliationSummary {
  total_bank_transactions: number;
  total_company_transactions: number;
  total_discrepancies: number;
  bank_only_discrepancies: number;
  company_only_discrepancies: number;
  opposite_pairs_removed: number;
  processing_duration_ms: number;
  pdf_processing_time_ms: number;
  excel_processing_time_ms: number;
  concurrent_processing: boolean;
}

// Net Total Value Interface
export interface NetTotalValue {
  value: number | null;
  status: 'found' | 'missing' | 'invalid';
}

// Reconciliation Result Interface
export interface ReconciliationResult {
  request_id: string;
  processing_status: 'completed' | 'partial' | 'error';
  processing_timestamp: string;
  summary: ReconciliationSummary;
  results: {
    bank_statement: BankTransaction[];
    company_records: CompanyTransaction[];
    discrepancies: DiscrepancyTransaction[];
  };
  bank_net_total?: NetTotalValue;
  company_net_total?: NetTotalValue;
  errors: string[];
  message: string;
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين

// Import categorization types for frontend enhancements
export type { TransactionCategory, CategorizedTransaction, DiscrepancySelectionState, ReconciliationCalculation } from './categorization.types';
// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
