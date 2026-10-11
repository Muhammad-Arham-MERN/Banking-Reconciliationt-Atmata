/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Admin Dashboard (Camri Desk) API Client
 *
 * Talks to the /api/admin/* surface. Auth is a dedicated admin JWT (NOT the
 * NextAuth session token) held by the caller in sessionStorage — see
 * AdminDashboard. Unlike the other clients there is no Google re-sign-in on
 * 401: a 401 means the admin session is over, so the caller returns to the
 * sign-in form.
 */

import type {
  AdminLoginResponse,
  AdminEmployeeListResponse,
  Company,
  CompanyListResponse,
  CompanyPasswordResponse,
  CompanyWriteInput,
  DeleteCompanyResponse,
} from '@/types/admin.types';
import type { CompanyRequestListResponse } from '@/types/companyRequest.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AdminApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'AdminApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Pull a human-readable message out of either error shape this API returns:
 *  - FastAPI `HTTPException(detail={...})` -> {"detail": {"error","message",...}}
 *  - middleware JSONResponse            -> {"error","message","status_code"}
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
        ? 'Invalid username or password.'
        : `Admin API operation failed (${response.status})`;

    let message = fallback;
    let details: Record<string, unknown> | undefined;
    try {
      const errorData = await response.json();
      message = extractErrorMessage(errorData, fallback);
      details = errorData;
    } catch {
      message = fallback;
    }
    throw new AdminApiError(message, response.status, details);
  }
  return response.json();
}

/** Build multipart form data for create/update. Omitted fields stay unchanged. */
function buildCompanyFormData(input: CompanyWriteInput): FormData {
  const formData = new FormData();
  formData.append('name', input.name);
  if (input.password) formData.append('password', input.password);
  formData.append('price_rupees', String(input.price_rupees));
  formData.append('payment_status', input.payment_status);
  if (input.trial_from) formData.append('trial_from', input.trial_from);
  if (input.trial_to) formData.append('trial_to', input.trial_to);
  if (input.logo) formData.append('logo', input.logo);
  return formData;
}

export const adminClient = {
  /** Exchange the admin username/password for an admin session token. */
  async login(username: string, password: string): Promise<AdminLoginResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse<AdminLoginResponse>(response);
  },

  /** Every registered company (no password material in the payload). */
  async listCompanies(token: string): Promise<CompanyListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/companies`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<CompanyListResponse>(response);
  },

  /** The view-only onboarding request inbox, newest first (FR-006). */
  async listCompanyRequests(token: string): Promise<CompanyRequestListResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/company-requests`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<CompanyRequestListResponse>(response);
  },

  /** A company's employee roster, for the companies-table hover modal (FR-018). */
  async listCompanyEmployees(
    token: string,
    companyId: string,
  ): Promise<AdminEmployeeListResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/admin/companies/${companyId}/employees`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    return handleResponse<AdminEmployeeListResponse>(response);
  },

  /** Create a company; the logo travels as a file when one is chosen. */
  async createCompany(token: string, input: CompanyWriteInput): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/api/admin/companies`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: buildCompanyFormData(input),
    });
    return handleResponse<Company>(response);
  },

  /** Update a company. Omit `password` to keep the existing one. */
  async updateCompany(
    token: string,
    companyId: string,
    input: CompanyWriteInput,
  ): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/api/admin/companies/${companyId}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
      body: buildCompanyFormData(input),
    });
    return handleResponse<Company>(response);
  },

  /** Delete a company (revokes its access). */
  async deleteCompany(token: string, companyId: string): Promise<DeleteCompanyResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/companies/${companyId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<DeleteCompanyResponse>(response);
  },

  /** Decrypt and return a company's password on demand (reveal/copy). */
  async revealPassword(token: string, companyId: string): Promise<CompanyPasswordResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/admin/companies/${companyId}/password`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    return handleResponse<CompanyPasswordResponse>(response);
  },

  /**
   * Absolute URL for a company's logo.
   * The logo endpoint requires the admin token, so it is fetched as a blob
   * (see fetchLogoBlob) rather than used directly as an <img src>.
   */
  logoUrl(company: Pick<Company, 'id' | 'logo_url'>): string | null {
    if (!company.logo_url) return null;
    return `${API_BASE_URL}${company.logo_url}`;
  },

  /** Fetch a logo and return an object URL for <img src>. Caller revokes it. */
  async fetchLogoBlob(token: string, companyId: string): Promise<string | null> {
    const response = await fetch(`${API_BASE_URL}/api/admin/companies/${companyId}/logo`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) return null;
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  },
};

export { AdminApiError };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
