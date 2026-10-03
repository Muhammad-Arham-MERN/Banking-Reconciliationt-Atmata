/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Company Onboarding Request API Client
 *
 * Talks to the signed-in (NextAuth) /api/company-requests surface. Auth is the
 * NextAuth access token from `session.user.access_token`. A submission is
 * persisted server-side and best-effort emails the Developer; an email failure
 * never fails the request (FR-006/FR-007). A 401 means the session is gone, so
 * the caller sends the user back to sign in.
 */

import type { CompanyRequest, CompanyRequestCreate } from '@/types/companyRequest.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class CompanyRequestApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'CompanyRequestApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Pull a human-readable message out of either error shape this API returns:
 *  - FastAPI `HTTPException(detail={...})` -> {"detail": {"error","message",...}}
 *  - middleware JSONResponse             -> {"error","message","status_code"}
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
    throw new CompanyRequestApiError(message, response.status, details);
  }
  return response.json();
}

export const companyRequestClient = {
  /** Submit the onboarding flow's answers; the Developer is notified by email. */
  async createCompanyRequest(
    token: string,
    input: CompanyRequestCreate,
  ): Promise<CompanyRequest> {
    const response = await fetch(`${API_BASE_URL}/api/company-requests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(input),
    });
    return handleResponse<CompanyRequest>(response);
  },
};

export { CompanyRequestApiError };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
