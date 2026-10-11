/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Employee Access Request API Client
 *
 * Talks to the signed-in employee surface: the company dropdown, its logos,
 * and the access-request submit. Auth is the NextAuth access token from
 * `session.user.access_token` — the same Bearer token the other session
 * clients send. A 401 here means the session is gone, so the caller sends the
 * employee back to sign in.
 */

import type {
  CompanyOptionListResponse,
  DeleteResponse,
  EmployeeRequestCreate,
  EmployeeRequestResponse,
  MembershipResponse,
} from '@/types/employee.types';
import type { CompanyRequest, CompanyRequestCreate } from '@/types/companyRequest.types';
import { companyRequestClient } from '@/lib/api/companyRequestClient';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class EmployeeApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'EmployeeApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Pull a human-readable message out of either error shape this API returns:
 *  - FastAPI `HTTPException(detail={...})` -> {"detail": {"error","message",...}}
 *  - middleware JSONResponse             -> {"error","message","status_code"}
 * Falling back to the raw object would render as "[object Object]".
 */
function extractErrorMessage(errorData: unknown, fallback: string): string {
  if (!errorData || typeof errorData !== 'object') return fallback;
  const data = errorData as Record<string, unknown>;

  const detail = data.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (detail && typeof detail === 'object') {
    const inner = (detail as Record<string, unknown>).message;
    if (typeof inner === 'string' && inner) return inner;
  }

  if (typeof data.message === 'string' && data.message) return data.message;
  return fallback;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const fallback =
      response.status === 401
        ? 'Your session has expired. Please sign in again.'
        : `Request failed (${response.status})`;

    let message = fallback;
    let details: Record<string, unknown> | undefined;
    try {
      const errorData = await response.json();
      message = extractErrorMessage(errorData, fallback);
      details = errorData;
    } catch {
      message = fallback;
    }
    throw new EmployeeApiError(message, response.status, details);
  }
  return response.json();
}

export const employeeClient = {
  /** Every company the Developer has onboarded (for the request dropdown). */
  async listCompanies(token: string): Promise<CompanyOptionListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companies`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<CompanyOptionListResponse>(response);
  },

  /** Submit an access request. The server normalizes the `adam-` ID. */
  async createRequest(
    token: string,
    input: EmployeeRequestCreate,
  ): Promise<EmployeeRequestResponse> {
    const response = await fetch(`${API_BASE_URL}/api/employees/requests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(input),
    });
    return handleResponse<EmployeeRequestResponse>(response);
  },

  /**
   * Fetch a company logo and return an object URL for <img src>. Caller revokes it.
   * The endpoint requires the session token, so a bare <img src> cannot be used.
   */
  async fetchLogoBlob(token: string, companyId: string): Promise<string | null> {
    const response = await fetch(`${API_BASE_URL}/api/companies/${companyId}/logo`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) return null;
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  },

  /**
   * The signed-in account's accepted membership (null when it has none).
   * Drives the application gate and the membership-aware navigation.
   */
  async getMembership(token: string): Promise<MembershipResponse> {
    const response = await fetch(`${API_BASE_URL}/api/me/membership`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<MembershipResponse>(response);
  },

  /**
   * Delete the account's employee record — this one operation serves BOTH
   * cancelling a pending request (FR-017) and leaving a granted company
   * (FR-015). Access is revoked either way; the user account is untouched.
   */
  async removeMembership(token: string): Promise<DeleteResponse> {
    const response = await fetch(`${API_BASE_URL}/api/me/membership`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<DeleteResponse>(response);
  },

  /** Submit a company onboarding request (delegates to the dedicated client). */
  createCompanyRequest(token: string, input: CompanyRequestCreate): Promise<CompanyRequest> {
    return companyRequestClient.createCompanyRequest(token, input);
  },
};

export { EmployeeApiError };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
