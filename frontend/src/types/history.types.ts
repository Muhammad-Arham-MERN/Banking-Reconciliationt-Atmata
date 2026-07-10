/**
 * TypeScript types for reconciliation history operations
 * Open de Past feature
 */

// A single discrepancy entry saved in or loaded from a history file
export interface HistoryEntry {
  category: string;
  transaction_details: string;
  transaction_date: string;
  debit_credit_amount: number;
  from_past?: boolean;
}

// Metadata for a saved history file
export interface HistoryFile {
  file_name: string;
  file_path: string;
  created_at: string;
  entry_count: number;
}

// Request payload for saving a reconciliation
export interface SaveHistoryRequest {
  custom_name?: string;
  discrepancies: HistoryEntry[];
}

// Response from saving a reconciliation
export interface SaveHistoryResponse {
  status: 'saved';
  file_name: string;
  entry_count: number;
  message: string;
}

// Response from listing history files
export interface ListHistoryResponse {
  files: HistoryFile[];
  total: number;
  message?: string;
}

// Response from loading a history file
export interface LoadHistoryResponse {
  status: 'loaded';
  file_name: string;
  discrepancies: HistoryEntry[];
  entry_count: number;
}

// Error response from history API
export interface HistoryErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
