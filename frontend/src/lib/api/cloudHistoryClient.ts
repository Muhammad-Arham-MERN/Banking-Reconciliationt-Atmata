/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Cloud History API Client
 * Handles communication with cloud backend history endpoints (load/save)
 */

import type {
  LoadCloudFilesResponse,
  SaveCloudFileRequest,
  SaveCloudFileResponse,
  CloudHistoryEntry,
  PastFileListResponse,
  LoadPastFileResponse,
  CreatePastFileRequest,
  UpdatePastFileRequest,
  UpdatePastFileResponse,
  DeletePastFileResponse,
  ExcelImportResponse,
  PastFileReconciliationType,
  LoadPastFileByNameResponse,
} from '@/types/cloud-history.types';

import { signIn } from 'next-auth/react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class CloudHistoryApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'CloudHistoryApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Handle cloud API response, throwing typed errors on failure.
 * On 401, redirect the user to sign in (FR-010).
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    // Session expired — redirect to sign-in
    await signIn('google', { callbackUrl: window.location.href });
    throw new CloudHistoryApiError('Session expired. Please sign in again.', 401);
  }

  if (!response.ok) {
    let message = 'Cloud API operation failed';
    let details: Record<string, unknown> | undefined;
    try {
      const errorData = await response.json();
      message = errorData.detail || errorData.message || message;
      details = errorData;
    } catch {
      message = `Cloud API operation failed (${response.status})`;
    }
    throw new CloudHistoryApiError(message, response.status, details);
  }

  return response.json();
}

export const cloudHistoryClient = {
  /**
   * List the authenticated user's saved file names from the cloud.
   * @param token - Bearer JWT from NextAuth session
   */
  async listCloudFiles(token: string): Promise<LoadCloudFilesResponse> {
    const response = await fetch(`${API_BASE_URL}/api/cloud/load_files_cloud`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return handleResponse<LoadCloudFilesResponse>(response);
  },

  /**
   * Save reconciliation data to the cloud for the authenticated user.
   * @param token - Bearer JWT from NextAuth session
   * @param fileName - User-provided file name
   * @param fileData - List of reconciliation entries
   */
  async saveCloudFile(
    token: string,
    fileName: string,
    fileData: CloudHistoryEntry[],
  ): Promise<SaveCloudFileResponse> {
    const body: SaveCloudFileRequest = {
      file_name: fileName,
      file_data: fileData,
    };

    const response = await fetch(`${API_BASE_URL}/api/cloud/save_files_cloud`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    return handleResponse<SaveCloudFileResponse>(response);
  },

  // --------------------------------------------------------------------------
  // Past Reconciliations — View / Create / Edit / Delete / Excel
  // --------------------------------------------------------------------------

  /** Metadata for every stored past file (newest first). */
  async listPastFiles(token: string): Promise<PastFileListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/cloud/files`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<PastFileListResponse>(response);
  },

  /** Full contents of one stored past file (user-scoped). */
  async loadPastFile(token: string, fileId: string): Promise<LoadPastFileResponse> {
    const response = await fetch(`${API_BASE_URL}/api/cloud/files/${fileId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<LoadPastFileResponse>(response);
  },

  /**
   * Load a past file by name (user-scoped) so its discrepancies can be merged
   * into a new reconciliation. Auth-protected like the rest of the API.
   */
  async loadByName(token: string, fileName: string): Promise<LoadPastFileByNameResponse> {
    const response = await fetch(`${API_BASE_URL}/history/load`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ file_name: fileName }),
    });
    return handleResponse<LoadPastFileByNameResponse>(response);
  },

  /** Create a new (possibly empty) past reconciliation file. */
  async createPastFile(
    token: string,
    body: CreatePastFileRequest,
  ): Promise<LoadPastFileResponse> {
    const response = await fetch(`${API_BASE_URL}/api/cloud/files`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    return handleResponse<LoadPastFileResponse>(response);
  },

  /** Update a past file's data and/or rename it. */
  async updatePastFile(
    token: string,
    fileId: string,
    body: UpdatePastFileRequest,
  ): Promise<UpdatePastFileResponse> {
    const response = await fetch(`${API_BASE_URL}/api/cloud/files/${fileId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    return handleResponse<UpdatePastFileResponse>(response);
  },

  /** Delete a stored past file. */
  async deletePastFile(token: string, fileId: string): Promise<DeletePastFileResponse> {
    const response = await fetch(`${API_BASE_URL}/api/cloud/files/${fileId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<DeletePastFileResponse>(response);
  },

  /**
   * Download a past-file Excel template (prefilled for edit, empty for create)
   * as a blob and trigger a browser download. Resolves with the chosen filename.
   */
  async downloadPastFileExcel(
    token: string,
    fileId?: string,
    reconciliationType: PastFileReconciliationType = 'bank',
  ): Promise<string> {
    const url = fileId != null
      ? `${API_BASE_URL}/api/cloud/files/${fileId}/excel`
      : `${API_BASE_URL}/api/cloud/excel-template?reconciliation_type=${reconciliationType}`;

    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.status === 401) {
      await signIn('google', { callbackUrl: window.location.href });
      throw new CloudHistoryApiError('Session expired. Please sign in again.', 401);
    }
    if (!response.ok) {
      let message = 'Failed to download Excel template';
      try {
        const errorData = await response.json();
        message = errorData.detail || errorData.message || message;
      } catch {
        message = `Failed to download Excel template (${response.status})`;
      }
      throw new CloudHistoryApiError(message, response.status);
    }

    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const fallback = fileId != null ? 'past-reconciliation.xlsx' : `${reconciliationType}-past-reconciliation-template.xlsx`;
    const filename = match ? match[1] : fallback;

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
    return filename;
  },

  /**
   * Upload a filled template. With file_id it updates that stored file
   * (Edit with Excel); without it, creates a new file (Create with Excel).
   */
  async importPastFileExcel(
    token: string,
    file: File,
    options: {
      fileId?: string;
      fileName?: string;
      reconciliationType?: PastFileReconciliationType;
    } = {},
  ): Promise<ExcelImportResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (options.fileId != null) formData.append('file_id', String(options.fileId));
    if (options.fileName) formData.append('file_name', options.fileName);
    formData.append('reconciliation_type', options.reconciliationType ?? 'bank');

    const response = await fetch(`${API_BASE_URL}/api/cloud/files/import-excel`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    return handleResponse<ExcelImportResponse>(response);
  },
};

export { CloudHistoryApiError };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
