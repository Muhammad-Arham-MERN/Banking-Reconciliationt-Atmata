/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * TypeScript types for cloud history API operations
 * load_files_cloud (GET) and save_files_cloud (POST)
 */

/** Response from GET /api/cloud/load_files_cloud */
export interface LoadCloudFilesResponse {
  files: string[];
}

/** Single entry within the file_data array for save_files_cloud */
export interface CloudHistoryEntry {
  transaction_details: string;
  transaction_date: string;
  debit_credit_amount: number;
  category: string;
}

/** Request body for POST /api/cloud/save_files_cloud */
export interface SaveCloudFileRequest {
  file_name: string;
  file_data: CloudHistoryEntry[];
}

/** Response from POST /api/cloud/save_files_cloud */
export interface SaveCloudFileResponse {
  success: boolean;
  message: string;
  file_name: string;
}

/** Error response shape from cloud API */
export interface CloudApiError {
  detail: string;
}

// ============================================================================
// Past Reconciliations — View / Create / Edit / Delete / Excel
// ============================================================================

export type PastFileReconciliationType = 'bank' | 'vendor';

/** Metadata for one stored past reconciliation file (GET /api/cloud/files) */
export interface PastFileMeta {
  /** STRING — CockroachDB SERIAL ids exceed JS safe-integer range. */
  file_id: string;
  file_name: string;
  created_at: string;
  entry_count: number;
  reconciliation_type: string;
}

/** Response from GET /api/cloud/files */
export interface PastFileListResponse {
  files: PastFileMeta[];
}

/** Response from GET /api/cloud/files/{file_id} and POST /api/cloud/files */
export interface LoadPastFileResponse {
  file_id: string;
  file_name: string;
  reconciliation_type: PastFileReconciliationType;
  discrepancies: CloudHistoryEntry[];
}

/** Request body for POST /api/cloud/files */
export interface CreatePastFileRequest {
  file_name: string;
  reconciliation_type: PastFileReconciliationType;
  file_data: CloudHistoryEntry[];
}

/** Request body for PUT /api/cloud/files/{file_id} */
export interface UpdatePastFileRequest {
  file_name?: string;
  file_data?: CloudHistoryEntry[];
}

/** Response from PUT /api/cloud/files/{file_id} */
export interface UpdatePastFileResponse {
  success: boolean;
  message: string;
  file_id: string;
  file_name: string;
  entry_count: number;
}

/** Response from DELETE /api/cloud/files/{file_id} */
export interface DeletePastFileResponse {
  success: boolean;
  message: string;
}

/** Response from POST /api/cloud/files/import-excel */
export interface ExcelImportResponse {
  success: boolean;
  message: string;
  file_id: string;
  file_name: string;
  reconciliation_type: PastFileReconciliationType;
  entry_count: number;
  discrepancies: CloudHistoryEntry[];
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
