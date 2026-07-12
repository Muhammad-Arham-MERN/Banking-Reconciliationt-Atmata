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

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
