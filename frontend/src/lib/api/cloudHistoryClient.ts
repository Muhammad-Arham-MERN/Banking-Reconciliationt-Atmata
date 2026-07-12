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
};

export { CloudHistoryApiError };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
