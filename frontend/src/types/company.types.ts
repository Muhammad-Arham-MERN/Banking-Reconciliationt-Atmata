/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Company Dashboard & onboarding types.
 *
 * Mirrors the company-auth contract for the sign-in shapes, plus the
 * client-held session. Employee and company-request rows now come from the
 * backend (see @/types/employee.types and @/types/companyRequest.types).
 */

/** A company as returned by the sign-in endpoint (no password material). */
export interface CompanyIdentity {
  id: string;
  name: string;
  logo_url: string | null;
}

/** The client-held company session (localStorage), valid for 24 hours. */
export interface CompanySession {
  token: string;
  company: CompanyIdentity;
  /** ISO-8601; sign-in time + COMPANY_JWT_TTL_HOURS. */
  expires_at: string;
}

/** POST /api/company/login request body. */
export interface CompanyLoginRequest {
  company_name: string;
  password: string;
}

/** POST /api/company/login success response. */
export interface CompanyLoginResponse {
  token: string;
  expires_at: string;
  company: CompanyIdentity;
}

export type EmployeeStatus = 'pending' | 'accepted' | 'denied';

/** Generic delete acknowledgement ({success,message}) returned by DELETE routes. */
export interface DeleteResponse {
  success: boolean;
  message: string;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
