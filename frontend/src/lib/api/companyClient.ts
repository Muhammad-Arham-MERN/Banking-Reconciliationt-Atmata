/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Company Dashboard API client.
 *
 * Talks to the /api/company/* surface (company-JWT branch). The sign-in
 * exchange establishes the client-held company session; every other call is
 * authenticated with that session token. The company's identity is taken from
 * the token server-side, never from the request body. Modelled on
 * frontend/src/lib/api/adminClient.ts, including its error-extraction shape,
 * so both clients read the same way.
 */
import type {
  CompanyLoginResponse,
  CompanyTrialState,
  DeleteResponse,
} from '@/types/company.types';
import type {
  CompanyEmployee,
  EmployeeListResponse,
  EmployeeManagerUpdate,
} from '@/types/employee.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class CompanyApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'CompanyApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Pull a human-readable message out of either error shape this API returns:
 *  - FastAPI `HTTPException(detail={...})` -> {"detail": {"error","message",...}}
 *  - middleware JSONResponse               -> {"error","message","status_code"}
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
        ? 'Invalid company name or password.'
        : `Company sign-in failed (${response.status})`;

    let message = fallback;
    let details: Record<string, unknown> | undefined;
    try {
      const errorData = await response.json();
      message = extractErrorMessage(errorData, fallback);
      details = errorData;
    } catch {
      message = fallback;
    }
    throw new CompanyApiError(message, response.status, details);
  }
  return response.json();
}

export const companyClient = {
  /** Exchange the company name/password for a 24-hour company session token. */
  async login(companyName: string, password: string): Promise<CompanyLoginResponse> {
    const response = await fetch(`${API_BASE_URL}/api/company/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: companyName, password }),
    });
    return handleResponse<CompanyLoginResponse>(response);
  },

  /**
   * Every employee record for the signed-in company, newest first (FR-001).
   * The optional `q` is a server-side convenience; the dashboard filters
   * client-side for instant response (see research D10).
   */
  async listEmployees(token: string, query?: string): Promise<EmployeeListResponse> {
    const qs = query ? `?q=${encodeURIComponent(query)}` : '';
    const response = await fetch(`${API_BASE_URL}/api/company/employees${qs}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<EmployeeListResponse>(response);
  },

  /** Grant a request — enables the bound signed-in account (FR-003). */
  async grantAccess(token: string, employeeId: string): Promise<CompanyEmployee> {
    const response = await fetch(
      `${API_BASE_URL}/api/company/employees/${employeeId}/grant`,
      { method: 'POST', headers: { Authorization: `Bearer ${token}` } },
    );
    return handleResponse<CompanyEmployee>(response);
  },

  /** Un-grant: revert to pending, so the account loses application access. */
  async revokeAccess(token: string, employeeId: string): Promise<CompanyEmployee> {
    const response = await fetch(
      `${API_BASE_URL}/api/company/employees/${employeeId}/revoke`,
      { method: 'POST', headers: { Authorization: `Bearer ${token}` } },
    );
    return handleResponse<CompanyEmployee>(response);
  },

  /** Delete a request, revoking any access it had granted (FR-004). */
  async deleteEmployee(token: string, employeeId: string): Promise<DeleteResponse> {
    const response = await fetch(`${API_BASE_URL}/api/company/employees/${employeeId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<DeleteResponse>(response);
  },

  /** The signed-in company's assigned free-trial window + state. */
  async getTrial(token: string): Promise<CompanyTrialState> {
    const response = await fetch(`${API_BASE_URL}/api/company/trial`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<CompanyTrialState>(response);
  },

  /** Activate the free trial (idempotent once started). */
  async startTrial(token: string): Promise<CompanyTrialState> {
    const response = await fetch(`${API_BASE_URL}/api/company/trial/start`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<CompanyTrialState>(response);
  },

  /** Assign or remove the Manager role (FR-019). */
  async setManager(
    token: string,
    employeeId: string,
    isManager: boolean,
  ): Promise<CompanyEmployee> {
    const body: EmployeeManagerUpdate = { is_manager: isManager };
    const response = await fetch(`${API_BASE_URL}/api/company/employees/${employeeId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    return handleResponse<CompanyEmployee>(response);
  },
};

export { CompanyApiError };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
