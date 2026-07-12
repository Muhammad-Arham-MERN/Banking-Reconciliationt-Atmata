/**
 * @deprecated Use cloudHistoryClient.ts instead for save/list operations.
 * loadHistory() is still used by UploadForm.tsx for merging past discrepancies
 * until a cloud equivalent endpoint is added.
 *
 * History API Client (Open de Past)
 * Handles communication with backend history endpoints (save/list/load)
 */

import type {
  SaveHistoryResponse,
  ListHistoryResponse,
  LoadHistoryResponse,
  HistoryEntry,
  HistoryErrorResponse,
} from '@/types/history.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class HistoryApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'HistoryApiError';
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = 'History operation failed';
    let details: Record<string, unknown> | undefined;
    try {
      const errorData: HistoryErrorResponse = await response.json();
      message = errorData.message || message;
      details = errorData.details;
    } catch {
      message = `History operation failed (${response.status})`;
    }
    throw new HistoryApiError(message, response.status, details);
  }
  return response.json();
}

export const historyClient = {
  /**
   * Save completed reconciliation discrepancies to a new SQLite history file
   */
  async saveHistory(
    discrepancies: HistoryEntry[],
    customName?: string,
  ): Promise<SaveHistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/history/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        discrepancies,
        custom_name: customName || undefined,
      }),
    });
    return handleResponse<SaveHistoryResponse>(response);
  },

  /**
   * List all saved history SQLite files
   */
  async listHistory(): Promise<ListHistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/history/list`);
    return handleResponse<ListHistoryResponse>(response);
  },

  /**
   * Load discrepancy entries from a saved history file
   */
  async loadHistory(fileName: string): Promise<LoadHistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/history/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_name: fileName }),
    });
    return handleResponse<LoadHistoryResponse>(response);
  },
};

export { HistoryApiError };

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
